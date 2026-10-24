"""Actual native Notebook state and CLI slash dispatch, without model calls."""

import queue
from unittest.mock import MagicMock

import pytest

from hermes_constants import reset_hermes_home_override, set_hermes_home_override
from hermes_state import SessionDB
from hermes_cli.cli_secretary_commands import notebook_command, noting_command, propose_persistence_command
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
    db.append_message("main", "assistant", "Preference acknowledged.", message_uid="coverage-only-anchor")
    ref = db.resolve_conversation_ref("main")
    working = NotebookStore(db, ref, anchor_message_uid="coverage-only-anchor")
    working.create("candidate", {"description": "Prefers concise answers", "targets": ["memory"], "notebook_refs": [], "source_types": []},
                   source_message_identities=[{"conversation_ref": ref, "message_uid": "evidence"}])
    working.commit(termination={"type": "finish_noting", "reason": "Synthetic fixture candidate"})
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
        output = noting_command(db, agent.session_id, "on").output
        assert guidance in output and "is on" not in output and "global noting.enabled is false" not in output
        assert not db.notebook_local_enabled(ref) and config.read_text() == before
        off = noting_command(db, agent.session_id, "off").output
        if idle:
            assert "unavailable" in off and guidance in off
            assert "unavailable" in notebook_command(db, agent.session_id).output
        else:
            assert "is off" in off
            assert "no Notebook Snapshot" in notebook_command(db, agent.session_id).output
        assert not db.notebook_local_enabled(ref) and config.read_text() == before
    finally:
        agent.close()


def test_unknown_cold_on_is_visible_and_cannot_enable(native_runtime):
    db, config = native_runtime
    config.write_text("noting:\n  enabled: true\n")
    db.create_session("unknown", source="cli")
    ref = db.resolve_conversation_ref("unknown")
    db.notebook_set_local_enabled(ref, False)
    output = noting_command(db, "unknown", "on").output
    assert "native Hermes context window and threshold" in output and "is on" not in output
    assert not db.notebook_local_enabled(ref)


def test_failed_config_read_cannot_enable_or_claim_global_false(state):
    home, db, ref = state
    db.notebook_set_local_enabled(ref, False)
    (home / "config.yaml").write_text("noting: [broken\n")
    assert "unreadable" in noting_command(db, "main", "on").output
    assert "unreadable" in propose_persistence_command(db, "main").output
    assert not db.notebook_local_enabled(ref)


def test_notebook_local_off_retains_human_snapshot_and_candidates(state):
    home, db, ref = state
    snapshot = db.notebook_current(ref)
    assert "is off" in noting_command(db, "main", "off").output
    assert not db.notebook_local_enabled(ref)
    text = notebook_command(db, "main").output
    from hermes_time import format_timestamp
    assert format_timestamp(snapshot["created_at"], profile_home=home) in text
    assert all(section in text.splitlines() for section in ("work", "situations", "discussion", "candidates"))
    assert snapshot["snapshot_id"] not in text
    assert snapshot["anchor_message_uid"] not in text
    result = propose_persistence_command(db, "main", "Focus on reusable preferences, 请简洁")
    assert result.prompt.endswith("Focus on reusable preferences, 请简洁")
    assert "I prefer concise answers." not in result.prompt
    assert "source_evidence" not in result.prompt
    assert "Before any actual mutation, obtain the user's explicit approval of the concrete content and destination." in result.prompt
    assert db.notebook_current(ref) == snapshot
    assert not db.notebook_local_enabled(ref)
    assert (home / "config.yaml").read_text() == "noting:\n  enabled: true\n"
    assert "is on" in noting_command(db, "main", "on").output
    assert db.notebook_local_enabled(ref)


def test_global_off_cannot_read_or_toggle_existing_state(state):
    home, db, ref = state
    (home / "config.yaml").write_text("noting:\n  enabled: false\n")
    assert "unavailable" in notebook_command(db, "main").output
    for action in ("on", "off"):
        assert "unavailable" in noting_command(db, "main", action).output
    assert "unavailable" in propose_persistence_command(db, "main", "tail").output
    assert db.notebook_local_enabled(ref)


def test_usage_null_pointer_no_candidates_and_pre_turn_local_state(state):
    _, db, _ = state
    assert noting_command(db, "main", "on extra").output == "Usage: /noting on|off"
    assert "no Notebook Snapshot" in notebook_command(db, "empty").output
    assert "no Notebook Snapshot" in propose_persistence_command(db, "empty").output
    assert "is off" in noting_command(db, "empty", "off").output
    ref = db.resolve_conversation_ref("empty")
    assert not db.notebook_local_enabled(ref)
    db.notebook_set_local_enabled(ref, True)
    db.append_message("empty", "user", "just a note", message_uid="empty-note")
    db.notebook_commit_snapshot(ref, NotebookWorkingState(ref), anchor_message_uid="empty-note",
        termination={"type": "finish_noting", "reason": "No candidate"})
    empty_proposal = propose_persistence_command(db, "empty")
    assert empty_proposal.prompt and '"candidates": []' in empty_proposal.prompt
    assert "If no suitable proposal exists, explain briefly" in empty_proposal.prompt


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
    assert cli.process_command("/noting off")
    assert not db.notebook_local_enabled(ref)
    assert cli.process_command("/propose-persistence Keep My Exact CASE, 普通自然语言")
    prompt = cli._pending_input.get_nowait()
    assert prompt.endswith("Keep My Exact CASE, 普通自然语言")
    assert "I prefer concise answers." not in prompt
    assert cli.session_id == "main"
    assert not db.notebook_local_enabled(ref)
    assert not hasattr(HermesCLI, "_handle_refine_command")
    assert callable(cli._handle_review_command)


def test_proposal_reads_only_candidate_leads_and_preserves_source_identity(state, monkeypatch):
    import json
    _, db, ref = state
    def forbidden(*args, **kwargs):
        raise AssertionError("Slash must not retrieve source evidence")
    monkeypatch.setattr(db, "get_history_foreground_conn", forbidden)
    result = propose_persistence_command(db, "main", "Revise only; do not execute")
    assert result.prompt
    payload = json.loads(result.prompt.split("Current Notebook Snapshot (data):\n", 1)[1].split("\n\nUser's additional request:", 1)[0])
    entry = payload["payload"]["candidates"][0]
    assert entry["entry_type"] == "candidate"
    assert payload["conversation_ref"] == ref
    assert entry["source_message_uids"] == ["evidence"]
    assert "source_message_identities" not in entry
    assert "source_evidence" not in payload
    assert "I prefer concise answers." not in result.prompt
    assert result.prompt.endswith("Revise only; do not execute")


def test_retired_notebook_toggle_does_not_change_local_state(state):
    _, db, ref = state
    before = db.notebook_current(ref)
    assert notebook_command(db, "main", "off").output == "Usage: /notebook"
    assert db.notebook_local_enabled(ref)
    assert db.notebook_current(ref) == before


def test_cli_feedback_survives_reload_and_is_visible_in_main_history(state, monkeypatch):
    from cli import HermesCLI
    _, db, ref = state
    cli = HermesCLI.__new__(HermesCLI)
    cli.session_id = "main"
    cli._session_db = db
    cli._pending_resume_sessions = None
    cli.conversation_history = db.get_messages_as_conversation("main")
    cli.config = {}
    monkeypatch.setattr("hermes_cli.plugins.fire_pre_command_hook", lambda **kw: None)
    assert cli.process_command("/noting off")
    assert cli.conversation_history[-2]["content"].endswith("/noting off")
    assert cli.conversation_history[-1]["content"] == "Background Noting is off for this Conversation."
    durable = db.get_messages_as_conversation("main")
    assert durable[-1]["content"] == cli.conversation_history[-1]["content"]
    assert durable[-2]["role"] == "user" and durable[-1]["role"] == "assistant"
    assert durable[-2]["content"].startswith("<timestamp>")
    assert not db.notebook_local_enabled(ref)


def test_cli_local_feedback_reaches_next_real_request_without_tool_change(state, monkeypatch):
    import copy
    from cli import HermesCLI
    from tests.secretary.test_noting_surface import _agent, _requests
    _, db, ref = state
    agent = _agent(db, session_id="main", existing=False)
    cli = HermesCLI.__new__(HermesCLI)
    cli.session_id = "main"
    cli._session_db = db
    cli._pending_resume_sessions = None
    cli.conversation_history = db.get_messages_as_conversation("main")
    cli.agent = agent
    cli.config = {}
    monkeypatch.setattr("hermes_cli.plugins.fire_pre_command_hook", lambda **kw: None)
    expected_tools = copy.deepcopy(agent.tools)
    requests = _requests(agent)
    try:
        assert cli.process_command("/noting off")
        assert agent.tools == expected_tools
        assert agent.run_conversation(user_message="Continue normally", conversation_history=cli.conversation_history,
                                      title_user_message="")["completed"]
        assert requests[0]["tools"] == expected_tools
        request_text = str(requests[0]["messages"])
        assert "Background Noting is off for this Conversation." in request_text
        assert "/noting off" in request_text
        assert not db.notebook_local_enabled(ref)
    finally:
        agent.close()


def test_cli_feedback_failure_does_not_claim_durable_history(state, monkeypatch):
    from hermes_cli.cli_secretary_commands import CLISecretaryCommandsMixin
    _, db, ref = state
    cli = CLISecretaryCommandsMixin()
    cli.session_id = "main"
    cli._session_db = db
    cli.conversation_history = []
    def failed(*args, **kwargs):
        raise OSError("disk unavailable")
    monkeypatch.setattr(db, "append_messages_batch", failed)
    assert "is off" in noting_command(db, "main", "off").output
    output = cli._secretary_feedback("/noting off", "Background Noting is off for this Conversation.")
    assert "feedback could not be saved" in output
    assert cli.conversation_history == []
    assert not db.notebook_local_enabled(ref)
