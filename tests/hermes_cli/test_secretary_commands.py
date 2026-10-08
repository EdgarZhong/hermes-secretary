"""Actual native Notebook state and CLI slash dispatch, without model calls."""

import queue
from unittest.mock import MagicMock

import pytest

from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from hermes_state import SessionDB
from hermes_cli.cli_secretary_commands import notebook_command, propose_persistence_command
from secretary.notebook_model import NotebookWorkingState
from secretary.notebook_store import NotebookStore
from tests.secretary.test_noting_config_contract import _construct, native_runtime as _native_runtime


@pytest.fixture
def state(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text("noting:\n  enabled: true\n")
    token = set_hermes_home_override(str(home))
    db = SessionDB(home / "state.db")
    db.create_session("main", source="cli")
    db.append_message("main", "user", "I prefer concise answers.", message_uid="evidence")
    ref = db.resolve_conversation_ref("main")
    working = NotebookStore(db, ref)
    working.create("memory_candidate", {"draft": "Prefers concise answers", "why_persist": "Repeated preference"},
                   source_message_identities=[{"conversation_ref": ref, "message_uid": "evidence"}])
    db.notebook_commit_snapshot(ref, working.show(), anchor_message_uid="evidence")
    # Enable requires the actual owner's native resolved pair, not merely a saved flag.
    from tests.secretary.test_noting_surface import _agent
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kw: MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **kw: {})
    agent = _agent(db, session_id="main", existing=False)
    try:
        yield home, db, ref
    finally:
        agent.close()
        db.close()
        reset_hermes_home_override(token)


@pytest.fixture
def native_runtime(tmp_path, monkeypatch):
    yield from _native_runtime.__wrapped__(tmp_path, monkeypatch)


@pytest.mark.parametrize("window,ratio,idle,guidance", [(128000, .75, 0, "increase the Context Window"),
    (500000, .60, 0, "move the Hermes threshold later"), (196000, .75, 300, "idle_compact_after_seconds to 0")])
def test_actual_invalid_capability_on_is_visible_and_does_not_write_local(native_runtime, window, ratio, idle, guidance):
    db, config = native_runtime
    agent, ref, _data = _construct(db, config, window=window, ratio=ratio, idle=idle, local=False)
    try:
        before = config.read_text()
        output = notebook_command(db, agent.session_id, "on").output
        assert guidance in output and "is on" not in output and "global noting.enabled is false" not in output
        assert not db.notebook_local_enabled(ref) and config.read_text() == before
        assert "is off" in notebook_command(db, agent.session_id, "off").output
        assert "no Notebook Snapshot" in notebook_command(db, agent.session_id).output
    finally:
        agent.close()


def test_unknown_cold_on_is_visible_and_cannot_enable(native_runtime):
    db, config = native_runtime
    config.write_text("noting:\n  enabled: true\n")
    db.create_session("unknown", source="cli")
    ref = db.resolve_conversation_ref("unknown")
    db.notebook_set_local_enabled(ref, False)
    output = notebook_command(db, "unknown", "on").output
    assert "native Hermes context window and threshold" in output and "is on" not in output
    assert not db.notebook_local_enabled(ref)


def test_failed_config_read_cannot_enable_or_claim_global_false(state):
    home, db, ref = state
    db.notebook_set_local_enabled(ref, False)
    (home / "config.yaml").write_text("noting: [broken\n")
    assert "unreadable" in notebook_command(db, "main", "on").output
    assert "unreadable" in propose_persistence_command(db, "main").output
    assert not db.notebook_local_enabled(ref)


def test_notebook_local_off_retains_human_snapshot_and_candidates(state):
    home, db, ref = state
    snapshot = db.notebook_current(ref)
    assert "is off" in notebook_command(db, "main", "off").output
    assert not db.notebook_local_enabled(ref)
    text = notebook_command(db, "main").output
    assert str(snapshot["created_at"]) in text
    assert all(section in text for section in ("user", "assistant", "consultation", "persistence"))
    assert snapshot["snapshot_id"] not in text
    assert snapshot["anchor_message_uid"] not in text
    result = propose_persistence_command(db, "main", "Focus on reusable preferences, 请简洁")
    assert result.prompt.endswith("Focus on reusable preferences, 请简洁")
    assert "I prefer concise answers." in result.prompt
    assert "source_evidence" in result.prompt
    assert "do not write Memory, Rules, Skills, or Notebook" in result.prompt
    assert db.notebook_current(ref) == snapshot
    assert not db.notebook_local_enabled(ref)
    assert (home / "config.yaml").read_text() == "noting:\n  enabled: true\n"
    assert "is on" in notebook_command(db, "main", "on").output
    assert db.notebook_local_enabled(ref)


def test_global_off_cannot_read_or_toggle_existing_state(state):
    home, db, ref = state
    (home / "config.yaml").write_text("noting:\n  enabled: false\n")
    for action in ("", "on", "off"):
        assert "unavailable" in notebook_command(db, "main", action).output
    assert "unavailable" in propose_persistence_command(db, "main", "tail").output
    assert db.notebook_local_enabled(ref)


def test_usage_null_pointer_no_candidates_and_pre_turn_local_state(state):
    _, db, _ = state
    assert notebook_command(db, "main", "on extra").output == "Usage: /notebook [on|off]"
    assert "no Notebook Snapshot" in notebook_command(db, "empty").output
    assert "no Notebook Snapshot" in propose_persistence_command(db, "empty").output
    assert "is off" in notebook_command(db, "empty", "off").output
    ref = db.resolve_conversation_ref("empty")
    assert not db.notebook_local_enabled(ref)
    db.notebook_set_local_enabled(ref, True)
    db.append_message("empty", "user", "just a note", message_uid="empty-note")
    db.notebook_commit_snapshot(ref, NotebookWorkingState(ref), anchor_message_uid="empty-note")
    assert "no persistence candidates" in propose_persistence_command(db, "empty").output


def test_cli_canonical_dispatch_queues_proposal_on_original_session(state, monkeypatch):
    from cli import HermesCLI
    _, db, ref = state
    cli = HermesCLI.__new__(HermesCLI)
    cli.session_id = "main"
    cli._session_db = db
    cli._pending_input = queue.Queue()
    cli._pending_resume_sessions = None
    cli.config = {}
    monkeypatch.setattr("hermes_cli.plugins.fire_pre_command_hook", lambda **kw: None)
    assert cli.process_command("/notebook off")
    assert not db.notebook_local_enabled(ref)
    assert cli.process_command("/propose-persistence Keep My Exact CASE, 普通自然语言")
    prompt = cli._pending_input.get_nowait()
    assert prompt.endswith("Keep My Exact CASE, 普通自然语言")
    assert "I prefer concise answers." in prompt
    assert cli.session_id == "main"
    assert not db.notebook_local_enabled(ref)
    assert not hasattr(HermesCLI, "_handle_refine_command")
    assert callable(cli._handle_review_command)
