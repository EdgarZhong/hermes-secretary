"""The reaper/exit-flush transcript persistence: right home, no external-secret hydration.

``session_reaper._flush_session_messages`` runs on the reaper tick and on the exit-flush worker —
threads with no turn on the stack. The transcript ROWS were never at risk (a profile session gets a
dedicated ``SessionDB`` whose ``db_path`` is frozen at construction), but everything
``agent._persist_session`` resolves at CALL time — config.yaml, the token ledger, memory/provider
lookups — resolved against the LAUNCH profile for a served profile's flush. ``_finalize_session``
binds the same session at the same chokepoint.

Binding that scope must stay CHEAP: it happens inside a 5s total exit-flush budget, and hydrating
the profile's external secret sources shells out to the operator's secret command (30s CLI budget)
— persisting a transcript needs no external credential.
"""
import threading
import time
import contextvars
import json
import tempfile
from pathlib import Path

import pytest

from hermes_constants import get_hermes_home
from tui_gateway import server as tui_server

class _Agent:
    def __init__(self, seen):
        self._session_messages = [{"role": "user", "content": "hi"}]
        self._seen = seen

    def _persist_session(self, _messages):
        self._seen.append(str(get_hermes_home()))

@pytest.fixture
def homes(tmp_path, monkeypatch):
    launch, served = tmp_path / "launch", tmp_path / "served"
    for home in (launch, served):
        home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(launch))
    return launch, served

def _install_session(monkeypatch, session):
    monkeypatch.setattr(tui_server, "_sessions", {"sid": session}, raising=False)
    monkeypatch.setattr(tui_server, "_sessions_lock", threading.RLock(), raising=False)
    monkeypatch.setattr(tui_server, "_INCREMENTAL_FLUSH_INTERVAL_S", 30.0, raising=False)

def test_incremental_flush_persists_into_the_sessions_own_home(homes, monkeypatch):
    launch, served = homes
    seen: list[str] = []
    _install_session(monkeypatch, {"agent": _Agent(seen), "profile_home": str(served)})

    assert tui_server._flush_dirty_sessions(now=1000.0) == 1
    assert seen == [str(served)], f"transcript flushed into {seen} instead of the served home"
    assert str(launch) not in seen

def test_exit_flush_never_waits_on_an_external_secret_source(homes, monkeypatch):
    """A slow ``op run`` / ``bws`` source must not cost the transcript the exit flush exists to save."""
    _launch, served = homes
    from hermes_cli import env_loader

    def _slow_source(_home):
        time.sleep(2.0)  # a real secret CLI gets a 30s budget; this whole flush gets 1s
        return {}

    monkeypatch.setattr(env_loader, "hydrate_profile_secret_sources", _slow_source)
    _install_session(monkeypatch, {"agent": _Agent([]), "profile_home": str(served)})

    assert tui_server._flush_sessions_before_exit(budget_s=1.0) == 1


@pytest.fixture
def kernel_workspace():
    with tempfile.TemporaryDirectory(prefix="hermes-finalize-workspace-", dir=Path(__file__).resolve().parents[3]) as path:
        yield Path(path)


def test_unscoped_finalize_clears_only_target_profiles_same_owner_kernel(homes, monkeypatch, kernel_workspace):
    from hermes_constants import (
        get_hermes_home_override, get_scratch_dir,
        reset_hermes_home_override, set_hermes_home_override,
    )
    from tools.approval_context import reset_current_session_key, set_current_session_key
    from tools.code_execution_tool import _execute_code_handler
    from tools.code_kernel import shutdown_kernels_for_owner

    launch, served = homes
    scratch = get_scratch_dir(launch)
    for name in ("TMPDIR", "TMP", "TEMP", "HERMES_SCRATCH_DIR"):
        monkeypatch.setenv(name, str(scratch))
    monkeypatch.setenv("TERMINAL_ENV", "local")
    monkeypatch.setenv("TERMINAL_CWD", str(kernel_workspace))
    monkeypatch.setattr("tools.code_execution_tool._load_config", lambda: {"timeout": 5})
    owner = "same-finalized-session-id"

    def run(home, code):
        home_token = set_hermes_home_override(home)
        owner_token = set_current_session_key(owner)
        try:
            return json.loads(_execute_code_handler({"code": code}, task_id="finalize-kernel"))
        finally:
            reset_current_session_key(owner_token)
            reset_hermes_home_override(home_token)

    errors, scopes = [], []

    def close_without_caller_scope():
        try:
            scopes.append(get_hermes_home_override())
            tui_server._finalize_session({
                "agent": None, "history": [], "history_lock": threading.Lock(),
                "session_key": owner, "profile_home": str(served), "source": "tui",
            }, end_reason="idle_timeout")
            scopes.append(get_hermes_home_override())
        except BaseException as exc:
            errors.append(exc)

    try:
        code = "import os; print(os.environ['HERMES_KERNEL_SPILL_DIR'])"
        launch_first = run(launch, "v = 41\n" + code)
        served_first = run(served, "v = 83\n" + code)
        assert launch_first["status"] == served_first["status"] == "success"
        launch_dir = Path(launch_first["output"].strip())
        served_dir = Path(served_first["output"].strip())
        assert launch_dir != served_dir
        worker = threading.Thread(target=lambda: contextvars.Context().run(close_without_caller_scope))
        worker.start()
        worker.join(timeout=10)
        assert not worker.is_alive()
        assert not errors, errors
        assert scopes == [None, None]
        assert not served_dir.exists()
        assert launch_dir.is_dir()
        launch_next = run(launch, "print(v)")
        assert launch_next["output"].strip() == "41", launch_next
        assert launch_next["kernel"]["reused"] is True
        served_next = run(served, "print('v' in globals())")
        assert served_next["output"].strip() == "False", served_next
        assert served_next["kernel"]["reused"] is False
    finally:
        for home in (launch, served):
            token = set_hermes_home_override(home)
            try:
                shutdown_kernels_for_owner(owner)
            finally:
                reset_hermes_home_override(token)
