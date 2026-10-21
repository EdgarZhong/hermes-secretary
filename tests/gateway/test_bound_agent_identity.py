"""Explicit ingress rebinding must not claim the messaging peer's old identity aliases."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from agent.agent_init import _init_session_state
from agent.prompt_cache_scope import initialize_conversation_identity, resolve_prompt_cache_scope
from gateway.control_conversation_binding import ConversationBindingControl
from gateway.conversation_binding import BINDING_KEY, agent_session_key
from gateway.run_turn_runner import TurnRunner
from gateway.turn_context import TurnContext
from hermes_state import SessionDB
from hermes_state_secretary_identity import ConversationIdentityError
from secretary.notebook_store import NotebookStore
from secretary.schedules import SchedulerStore
from tests.gateway.test_conversation_binding import bound_store as bound_store


def build_agent(store, db, source, key, sid):
    """Exercise Gateway's real constructor kwargs and the native session initializer."""
    def native_session_agent(**kwargs):
        agent = SimpleNamespace(
            max_iterations=kwargs["max_iterations"], platform=kwargs["platform"],
            _gateway_session_key=kwargs["gateway_session_key"],
        )
        _init_session_state(agent, kwargs["session_id"], kwargs["session_db"], None,
                            None, None, False, 1, 1, 1)
        return agent

    runner = SimpleNamespace(session_store=store, _session_db=SimpleNamespace(_db=db),
                             _prefill_messages=None, _service_tier=None,
                             _refresh_fallback_model=lambda: None)
    ctx = TurnContext(source=source, session_id=sid, session_key=key,
                      user_config={}, AIAgent=native_session_agent)
    return TurnRunner(runner, ctx)._build_fresh_agent(
        {"model": "fixture", "runtime": {}}, "weixin", None, 1, None, {}, True)


def binding_control(store):
    runner = SimpleNamespace(session_store=store, _running_agents={},
                             _evict_cached_agent=Mock(), _clear_conversation_scope=Mock())
    return ConversationBindingControl(runner)


@pytest.mark.parametrize("source", ["desktop", "pi-import"])
def test_real_binding_a_to_b_initializes_b_without_merging_channel_aliases(bound_store, source):
    store, db, ingress, key = bound_store
    # The three old source-qualified aliases are independent, valid historic owners.
    old_refs = {}
    for old_source in ("desktop", "pi-import", "weixin"):
        sid = "old-" + old_source
        # Legacy imported Main can already own the alias while its row has no native key.
        db.create_session(sid, old_source, session_key=None if old_source == "pi-import" else key)
        db.append_message(sid, "user", "historic " + old_source)
        old_refs[sid] = db.resolve_conversation_ref(sid, (old_source, key, 0))
    db.create_session("selected-b", source)
    ref_b = db.resolve_conversation_ref("selected-b")
    for sid in ("old-" + source, "selected-b"):
        uid = "anchor-" + sid
        db.append_message(sid, "user", "retained source", message_uid=uid)
        ref = db.resolve_conversation_ref(sid)
        notebook = NotebookStore(db, ref, anchor_message_uid=uid)
        notebook.create("candidate", {"description": "retained candidate", "targets": ["memory"],
                                      "notebook_refs": [], "source_types": []},
                        source_message_identities=[{"conversation_ref": ref, "message_uid": uid}])
        notebook.commit(termination={"type": "forced"})
        schedule = SchedulerStore(db, ref, session_id=sid).create(
            "retained reminder", "2099-01-01T00:00:00+00:00", "instant")
        assert schedule["success"]
    control = binding_control(store)
    params = {"profile": key.split(":")[1], "action": "bind"}
    assert control.execute({**params, "conversation_ref": old_refs["old-" + source]})["ok"]
    first = build_agent(store, db, ingress, key, "old-" + source)
    assert first._secretary_conversation_ref == old_refs["old-" + source]
    assert control.execute({**params, "conversation_ref": ref_b})["ok"]
    tables = [row[0] for row in db._read_all("SELECT name FROM sqlite_master "
                                            "WHERE type='table' AND name LIKE 'secretary_%'")]
    tables.extend(("sessions", "messages"))
    before = {table: db._read_all("SELECT * FROM " + table) for table in tables}

    # This is the previous erroneous construction: a mutable ingress key claims an old alias.
    wrong = SimpleNamespace(_session_db=db, session_id="selected-b", _gateway_session_key=key)
    with pytest.raises(ConversationIdentityError, match="aliases conflict"):
        initialize_conversation_identity(wrong)
    agent = build_agent(store, db, ingress, key, "selected-b")
    assert agent._secretary_conversation_ref == ref_b
    assert agent._gateway_session_key is None
    assert resolve_prompt_cache_scope(agent) == "selected-b"
    assert {sid: db.resolve_conversation_ref(sid) for sid in old_refs} == old_refs
    assert store.lookup_by_session_key(key).metadata[BINDING_KEY]["conversation_ref"] == ref_b
    assert {table: db._read_all("SELECT * FROM " + table) for table in before} == before
    assert store.get_or_create_session(ingress).session_id == "selected-b"


def test_bound_target_keeps_its_own_declared_key_across_compression_and_branch(bound_store):
    store, db, ingress, key = bound_store
    own_key = "desktop-conversation-key"
    db.create_session("target", "desktop", session_key=own_key)
    ref = db.resolve_conversation_ref("target")
    control = binding_control(store)
    assert control.execute({"profile": key.split(":")[1], "action": "bind", "conversation_ref": ref})["ok"]
    db.end_session("target", "compression")
    db.create_session("tip", "desktop", session_key=own_key, parent_session_id="target")
    assert store.get_or_create_session(ingress).session_id == "tip"
    agent = build_agent(store, db, ingress, key, "tip")
    assert agent._gateway_session_key == own_key and agent._secretary_conversation_ref == ref
    db.create_session("branch", "desktop", session_key=own_key, parent_session_id="tip",
                      model_config={"_branched_from": "tip"})
    branch_ref = db.resolve_conversation_ref("branch")
    assert branch_ref != ref
    with pytest.raises(ValueError, match="does not own"):
        build_agent(store, db, ingress, key, "branch")
    assert store.lookup_by_session_key(key).metadata[BINDING_KEY]["conversation_ref"] == ref


def test_unbound_initialization_keeps_native_channel_identity(bound_store):
    store, db, ingress, key = bound_store
    sid = store.lookup_by_session_key(key).session_id
    ref = db.resolve_conversation_ref(sid)
    agent = build_agent(store, db, ingress, key, sid)
    assert agent._gateway_session_key == key and agent._secretary_conversation_ref == ref


def test_binding_ref_from_another_profile_is_rejected(bound_store, tmp_path):
    store, db, ingress, key = bound_store
    other = SessionDB(tmp_path / "another-profile.db")
    try:
        other.create_session("foreign", "desktop")
        ref = other.resolve_conversation_ref("foreign")
        result = binding_control(store).execute({
            "profile": key.split(":")[1], "action": "bind", "conversation_ref": ref,
        })
        assert not result["ok"] and result["error"]["code"] == "conversation_unavailable"
        entry = store.lookup_by_session_key(key)
        entry.metadata[BINDING_KEY] = {"conversation_ref": ref}
        with pytest.raises(ValueError, match="does not own"):
            agent_session_key(store, key, "foreign")
        assert db.get_session("foreign") is None
    finally:
        other.close()


def test_true_alias_conflict_in_bound_target_still_fails_closed(bound_store):
    store, db, ingress, key = bound_store
    control = binding_control(store)
    ref = db.resolve_conversation_ref("imported")
    assert control.execute({"profile": key.split(":")[1], "action": "bind", "conversation_ref": ref})["ok"]
    sid = store.lookup_by_session_key(key).session_id
    db.create_session("unrelated", "desktop")
    other_ref = db.resolve_conversation_ref("unrelated")
    db._write_sql("UPDATE secretary_conversation_aliases SET conversation_ref=? "
                  "WHERE alias_kind='compression_root' AND alias_value=?", (other_ref, sid))
    with pytest.raises(ConversationIdentityError, match="aliases conflict"):
        build_agent(store, db, ingress, key, sid)
