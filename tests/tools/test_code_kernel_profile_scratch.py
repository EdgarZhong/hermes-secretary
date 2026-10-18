"""Real execute_code kernels stage scripts and output under the calling profile."""

import json
import os
import tempfile
import uuid
from contextlib import nullcontext
from pathlib import Path

import pytest

from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from tools.approval_context import reset_current_session_key, set_current_session_key
from tools.code_execution_tool import _execute_code_handler
from tools.code_kernel import _KERNELS, shutdown_kernels_for_owner


@pytest.fixture
def shared_workspace():
    with tempfile.TemporaryDirectory(prefix="hermes-kernel-workspace-", dir=Path(__file__).resolve().parents[3]) as path:
        yield Path(path)


@pytest.fixture
def profiles(monkeypatch, tmp_path, shared_workspace):
    launch, alpha, beta = (tmp_path / name for name in ("launch", "alpha", "beta"))
    launch_scratch = launch / "cache" / "scratch"
    launch_scratch.mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(launch))
    monkeypatch.setenv("TERMINAL_ENV", "local")
    for name in ("TMPDIR", "TMP", "TEMP"):
        monkeypatch.setenv(name, str(launch_scratch))
    monkeypatch.setenv("HERMES_SCRATCH_DIR", str(launch_scratch))
    # Reproduce a long-lived host whose tempfile default was cached at boot.
    monkeypatch.setattr(tempfile, "tempdir", str(launch_scratch))
    monkeypatch.setattr("tools.code_execution_tool._load_config", lambda: {
        "mode": "strict", "timeout": 5,
    })
    owner_prefix = "profile-scratch-" + uuid.uuid4().hex
    owners = set()

    def run(home, code, *, owner=None, **kwargs):
        owner = owner or owner_prefix + "::" + str(home or launch)
        home_token = set_hermes_home_override(home)
        session_token = set_current_session_key(owner)
        try:
            from tools.code_kernel import _resolve_owner
            owners.add((home, _resolve_owner("")))
            return json.loads(_execute_code_handler(
                {"code": code, **kwargs}, task_id=uuid.uuid4().hex,
            ))
        finally:
            reset_current_session_key(session_token)
            reset_hermes_home_override(home_token)

    yield launch, alpha, beta, run
    for home, owner in owners:
        home_token = set_hermes_home_override(home)
        try:
            shutdown_kernels_for_owner(owner)
        finally:
            reset_hermes_home_override(home_token)


_PATHS_CELL = """
import json, os, tempfile, hermes_tools
print(json.dumps({
    "home": os.environ["HERMES_HOME"],
    "staging": os.getcwd(),
    "tools_script": hermes_tools.__file__,
    "spill_dir": os.environ["HERMES_KERNEL_SPILL_DIR"],
    "tempdir": tempfile.gettempdir(),
}))
"""


def _paths(result, home, *, tempdir=None, cwd=None):
    assert result["status"] == "success", result
    paths = json.loads(result["output"])
    scratch = home / "cache" / "scratch"
    staging = Path(paths["tools_script"]).parent
    assert staging.parent == scratch, paths
    assert Path(paths["staging"]) == (cwd or staging), paths
    assert Path(paths["home"]) == home, paths
    assert Path(paths["tempdir"]) == (tempdir or scratch), paths
    assert Path(paths["spill_dir"]) == staging, paths
    assert Path(paths["tools_script"]) == staging / "hermes_tools.py", paths
    assert (staging / "hermes_kernel_runner.py").is_file()
    return staging


def test_routed_profiles_stage_and_spill_separately_with_persistent_state(profiles):
    launch, alpha, beta, run = profiles
    alpha_first = run(alpha, "alpha_only = 41\n" + _PATHS_CELL)
    beta_first = run(beta, "beta_only = 83\n" + _PATHS_CELL)
    alpha_dir = _paths(alpha_first, alpha)
    beta_dir = _paths(beta_first, beta)
    assert alpha_dir != beta_dir
    for first in (alpha_first, beta_first):
        assert first["kernel"]["reused"] is False
        assert first["kernel"]["execution_count"] == 1
    alpha_next = run(alpha, "print(alpha_only + 1, 'beta_only' in globals())")
    beta_next = run(beta, "print(beta_only + 1, 'alpha_only' in globals())")
    assert alpha_next["output"].strip() == "42 False", alpha_next
    assert beta_next["output"].strip() == "84 False", beta_next
    for next_cell in (alpha_next, beta_next):
        assert next_cell["kernel"]["reused"] is True
        assert next_cell["kernel"]["execution_count"] == 2
    for home, foreign_name in ((alpha, "beta_only"), (beta, "alpha_only")):
        foreign = run(home, "print(" + foreign_name + ")")
        assert foreign["status"] == "error", foreign
        assert "NameError" in foreign["error"], foreign
    for home, staging in ((alpha, alpha_dir), (beta, beta_dir)):
        spilled = run(home, "print('x' * 1000001)")
        assert spilled["status"] == "success", spilled
        spill = Path(spilled["stdout_spill_path"])
        assert spill.parent == staging, spilled
        assert spill.read_text() == "x" * 1000001 + "\n"
    # The fix must not mutate process-global scratch selection between calls.
    launch_scratch = launch / "cache" / "scratch"
    assert tempfile.tempdir == str(launch_scratch)
    assert os.environ["TMPDIR"] == str(launch_scratch)
    assert not list(launch_scratch.glob("hermes_kernel_*"))


@pytest.mark.parametrize("mode", ["strict", "project"])
def test_single_profile_without_override_preserves_native_paths_and_reuse(profiles, monkeypatch, mode, shared_workspace):
    launch, _, _, run = profiles
    config = {"timeout": 5}
    if mode == "strict":
        config["mode"] = mode
    # Omitted mode exercises the native project default and its cwd selection.
    monkeypatch.setattr("tools.code_execution_tool._load_config", lambda: config)
    monkeypatch.setenv("TERMINAL_CWD", str(shared_workspace))
    first = run(None, "native_value = 23\n" + _PATHS_CELL)
    _paths(first, launch, cwd=shared_workspace if mode == "project" else None)
    second = run(None, "print(native_value)")
    assert second["output"].strip() == "23", second
    assert second["kernel"]["reused"] is True


def test_explicit_user_tempdir_is_preserved_without_moving_kernel_staging(profiles, monkeypatch):
    launch, alpha, _, run = profiles
    user_temp = launch.parent / "user-temporary-files"
    user_temp.mkdir()
    monkeypatch.setenv("TMPDIR", str(user_temp))
    result = run(alpha, _PATHS_CELL)
    _paths(result, alpha, tempdir=user_temp)
    assert os.environ["TMPDIR"] == str(user_temp)


def test_same_owner_and_shared_workspace_cannot_share_profile_kernel(profiles, monkeypatch, shared_workspace):
    launch, alpha, beta, run = profiles
    monkeypatch.setattr("tools.code_execution_tool._load_config", lambda: {
        "mode": "project", "timeout": 5,
    })
    monkeypatch.setenv("TERMINAL_CWD", str(shared_workspace))
    owner = "same-stored-session-id"
    first = run(alpha, "alpha_only = 41\n" + _PATHS_CELL, owner=owner)
    second = run(beta, "beta_only = 83\nprint(globals().get('alpha_only'))", owner=owner)
    assert second["status"] == "success", second
    assert second["kernel"]["reused"] is False, second
    assert second["output"].strip() == "None", second
    alpha_dir = _paths(first, alpha, cwd=shared_workspace)
    beta_dir = _paths(run(beta, _PATHS_CELL, owner=owner), beta, cwd=shared_workspace)
    assert alpha_dir != beta_dir
    alpha_next = run(alpha, "print(alpha_only, 'beta_only' in globals())", owner=owner)
    assert alpha_next["output"].strip() == "41 False", alpha_next
    for home, name in ((alpha, "beta_only"), (beta, "alpha_only")):
        foreign = run(home, "print(" + name + ")", owner=owner)
        assert foreign["status"] == "error", foreign
        assert "NameError" in foreign["error"], foreign


@pytest.mark.parametrize("cleanup", ["close", "reset", "child"])
def test_same_owner_cleanup_is_confined_to_calling_profile(profiles, monkeypatch, cleanup, shared_workspace):
    from agent.delegation_context import delegated_child_context
    from tools.approval import clear_session
    from tools.code_kernel import shutdown_kernels_for_delegated_child

    launch, alpha, beta, run = profiles
    monkeypatch.setattr("tools.code_execution_tool._load_config", lambda: {
        "mode": "project", "timeout": 5,
    })
    monkeypatch.setenv("TERMINAL_CWD", str(shared_workspace))
    owner = "same-cleanup-session-id"
    scope = delegated_child_context("same-child-id") if cleanup == "child" else nullcontext()
    with scope:
        alpha_dir = _paths(run(alpha, "v = 41\n" + _PATHS_CELL, owner=owner), alpha, cwd=shared_workspace)
        beta_dir = _paths(run(beta, "v = 83\n" + _PATHS_CELL, owner=owner), beta, cwd=shared_workspace)
        home_token = set_hermes_home_override(alpha)
        try:
            if cleanup == "close":
                clear_session(owner)
            elif cleanup == "child":
                shutdown_kernels_for_delegated_child("same-child-id")
            else:
                reset = run(alpha, "print('v' in globals())", owner=owner, reset=True)
                assert reset["output"].strip() == "False", reset
        finally:
            reset_hermes_home_override(home_token)
        assert not alpha_dir.exists()
        assert beta_dir.is_dir()
        beta_next = run(beta, "print(v)", owner=owner)
        assert beta_next["output"].strip() == "83", beta_next
        assert beta_next["kernel"]["reused"] is True
        alpha_next = run(alpha, "print('v' in globals())", owner=owner)
        assert alpha_next["output"].strip() == "False", alpha_next
        assert alpha_next["kernel"]["reused"] is (cleanup == "reset")


@pytest.mark.parametrize("failure", ["mkdir", "write", "spawn"])
def test_failed_creation_cleans_profile_staging_and_allows_retry(profiles, monkeypatch, failure):
    _, alpha, _, run = profiles

    def fail(*args, **kwargs):
        raise OSError("controlled kernel creation failure")

    with monkeypatch.context() as patcher:
        if failure == "mkdir":
            patcher.setattr("tools.code_kernel.tempfile.mkdtemp", fail)
        elif failure == "write":
            patcher.setattr(Path, "write_text", fail)
        else:
            patcher.setattr("tools.code_kernel.subprocess.Popen", fail)
        result = run(alpha, "print('unreachable')")
    assert result["status"] == "error", result
    assert "controlled kernel creation failure" in result["error"], result
    assert not list((alpha / "cache" / "scratch").glob("hermes_kernel_*"))
    assert not any("profile-scratch-" in kernel.owner for kernel in _KERNELS.values())
    fresh = run(alpha, _PATHS_CELL)
    _paths(fresh, alpha)
    assert fresh["kernel"]["reused"] is False


@pytest.mark.parametrize("ending", ["timeout", "exit", "reset"])
def test_kernel_end_removes_profile_staging_and_restarts_cleanly(profiles, ending):
    _, alpha, _, run = profiles
    first = run(alpha, "old_value = 41\n" + _PATHS_CELL)
    staging = _paths(first, alpha)
    if ending == "reset":
        ended = run(alpha, "print('old_value' in globals())", reset=True)
        assert ended["output"].strip() == "False", ended
        assert ended["kernel"]["state_reset"] is True
    else:
        code = "import time; time.sleep(30)" if ending == "timeout" else "raise SystemExit(0)"
        ended = run(alpha, code)
        assert ended["status"] == ("timeout" if ending == "timeout" else "success"), ended
    assert not staging.exists()
    fresh = run(alpha, _PATHS_CELL)
    assert _paths(fresh, alpha) != staging
    assert fresh["kernel"]["reused"] is (ending == "reset")
