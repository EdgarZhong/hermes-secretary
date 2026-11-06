"""Real SessionDB and native lifecycle receipts; model transports remain controlled."""
import json
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from secretary import adaptive_runtime as runtime, adaptive_store as store
from secretary.adaptive_import import import_samples
from tests.secretary.test_adaptive_runtime import adaptive_config
from tests.secretary import test_adaptive_runtime as runtime_tests, test_noting_child as child_tests
from tests.secretary.test_noting_child import _tool_response, empty_state


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from runtime_tests.owned.__wrapped__(tmp_path, monkeypatch)


@pytest.fixture
def db(tmp_path):
    yield from child_tests.db.__wrapped__(tmp_path)


@pytest.fixture
def parent(db):
    return child_tests.parent.__wrapped__(db)


@pytest.fixture
def stub_client(monkeypatch, tmp_path):
    return child_tests.stub_client.__wrapped__(monkeypatch, tmp_path)


def _response():
    return SimpleNamespace(model="test/aux", usage=SimpleNamespace(
        prompt_tokens=100, completion_tokens=7,
        prompt_tokens_details=SimpleNamespace(cached_tokens=60)))


def _samples(db, ref):
    return [event for event in store.history(db, ref, time.time()) if event["kind"] == "maintenance_sample"]


def _sample(identity="old", **values):
    result = dict(kind="maintenance_sample", component="compaction", event_id=identity,
                operation_id=identity, at=100, available_at=120, verified=True,
                model_key="old-model", model_identity={"provider": "openai", "model": "old"},
                model_contract={"provider": "openai", "model": "old", "reasoning_effort": "high"},
                context_before=1000, context_after=0, duration_seconds=10, block_seconds=10,
                duration_scope="component_execution", block_scope="native_compaction_registration",
                outcome="completed", usage={"input_tokens": 40, "cache_read_tokens": 60,
                                            "cache_write_tokens": 0, "output_tokens": 7},
                usage_complete=True, proof={"source": "native_history_numeric"})
    return {**result, **values}


@pytest.fixture
def real_parent(parent, db, tmp_path):
    from agent.context_compressor import ContextCompressor
    from secretary.noting_scope import bind_main_runtime
    parent.model, parent.provider, parent.api_mode = "test/runtime", "openai", "chat_completions"
    parent.requested_provider = None
    parent.context_compressor = ContextCompressor(model="test/runtime", config_context_length=130000,
                                                threshold_tokens_cap=75000, quiet_mode=True)
    parent.context_compressor.update_from_response({"prompt_tokens": 5000})
    db.patch_session_model_config(parent.session_id, {"provider": "openai", "api_mode": "chat_completions"})
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model=? WHERE id=?",
                                              (parent.model, parent.session_id)))
    (tmp_path / "config.yaml").write_text(json.dumps(adaptive_config(parent._secretary_conversation_ref)))
    bind_main_runtime(parent)
    return parent


def test_native_compaction_facade_collects_auxiliary_receipts(real_parent, db, monkeypatch):
    """Registration/settlement are real; replace only the compression execution boundary."""
    from agent.auxiliary_hooks import run_with_aux_hooks
    parent = real_parent
    parent._compression_feasibility_checked = True
    def execute(agent, messages, system, **kwargs):
        run_with_aux_hooks(_response, aux_task="compression", metadata={}, client=SimpleNamespace(),
                           kwargs={}, provider="openai", model="test/aux", api_mode="chat_completions")
        # Native reset is an invalid anchor, not a measured zero-context outcome.
        parent.context_compressor.last_prompt_tokens = 0
        parent.context_compressor.last_real_prompt_tokens = 0
        return messages, system
    monkeypatch.setattr("agent.conversation_compression.compress_context", execute)
    parent._compress_context(parent._session_messages, None, force=True)
    sample = _samples(db, parent._secretary_conversation_ref)[0]
    assert sample["usage_complete"] is True
    assert sample["usage"] == dict(input_tokens=40, cache_read_tokens=60, cache_write_tokens=0, output_tokens=7)
    assert sample["context_after"] is None
    assert sample["block_scope"] == "native_compaction_registration"
    assert sample["model_identity"]["model"] == "test/aux"
    assert sample["parent_model_key"] == runtime.model_key(parent)
    assert sample["duration_seconds"] >= 0


def test_failed_auxiliary_keeps_paid_receipts_and_unknown_total(real_parent, db, monkeypatch):
    from agent.auxiliary_hooks import run_with_aux_hooks
    parent = real_parent
    parent._compression_feasibility_checked = True
    def execute(agent, messages, system, **kwargs):
        route = dict(aux_task="compression", metadata={}, client=SimpleNamespace(), kwargs={},
                     provider="openai", model="test/aux", api_mode="chat_completions")
        run_with_aux_hooks(_response, **route)
        def fail():
            raise RuntimeError("controlled unavailable provider")
        run_with_aux_hooks(fail, **route)
    monkeypatch.setattr("agent.conversation_compression.compress_context", execute)
    with pytest.raises(RuntimeError):
        parent._compress_context(parent._session_messages, None, force=True)
    sample = _samples(db, parent._secretary_conversation_ref)[0]
    assert sample["outcome"] in {"error", "cancelled"} and sample["usage_complete"] is False
    assert sample["usage"]["input_tokens"] is None
    assert sample["observed_usage"]["input_tokens"] == 40
    assert sample["observed_usage"]["output_tokens"] == 7
    assert sample["proof"]["dispatches"] == sample["proof"]["requests"] == 2


def test_real_noting_turn_has_independent_component_bill(real_parent, db, stub_client):
    from secretary.noting_child import run_noting_task
    parent = real_parent
    response = _tool_response("finish_noting", {"reason": "No changes needed."}, "finish")
    response.usage = _response().usage
    stub_client.chat.completions.create.return_value = response
    ref = parent._secretary_conversation_ref
    admission = db.noting_admit(ref, "m2", kind="idle")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref,
                             anchor_message_uid="m2", trigger_type="idle", runtime_profile="NOTING",
                             task_instruction="Maintain the Notebook.", state_provider=lambda child: empty_state())
    assert outcome.committed, outcome
    sample = _samples(db, ref)[0]
    assert sample["component"] == "noting" and sample["outcome"] == "completed"
    assert sample["usage_complete"] is True
    assert sample["usage"]["output_tokens"] == 7
    assert sample["block_seconds"] == 0 and sample["block_scope"] == "background_not_main_block"
    assert "joint_operation_id" not in sample  # No native operation association was supplied.


def test_explicit_import_is_atomic_idempotent_owner_scoped_and_restart_readable(owned):
    from tests.hermes_state._secretary_noting_harness import open_noting_db
    parent, db, ref = owned
    args = dict(import_id="fixed-numeric", source_sha256="a" * 64, now=200)
    preview = import_samples(db, ref, [_sample()], **args)
    assert preview["applied"] is False
    assert not store.imported_history(db, ref, 200)
    receipt = import_samples(db, ref, [_sample()], apply=True, **args)
    assert receipt["event_count"] == 1
    assert import_samples(db, ref, [_sample()], apply=True, **args)["already_applied"] is True
    with pytest.raises(ValueError, match="conflicting"):
        import_samples(db, ref, [_sample(outcome="error")], apply=True, **args)
    with pytest.raises(ValueError):
        import_samples(db, ref, [_sample("good"), _sample("bad", duration_seconds=float("nan"))],
                       import_id="bad-package", source_sha256="b" * 64, now=200, apply=True)
    other = open_noting_db(db.db_path)
    try:
        assert not store.imported_history(other, ref, 199)
        cohorts = store.imported_history(other, ref, 200)
        assert len(cohorts) == 1 and len(cohorts[0]["events"]) == 1
        assert cohorts[0]["events"][0]["context_after"] is None
        assert cohorts[0]["events"][0]["model_contract"]["reasoning_effort"] == "high"
        assert cohorts[0]["events"][0]["source_kind"] == "component_pool"
        assert cohorts[0]["events"][0]["ownership"] == "unproven_historical_component_pool"
        assert cohorts[0]["origin_conversation"] != ref
        assert not store.history(other, ref, 200)
    finally:
        other.close()


def test_disabled_and_cross_owner_imports_rejected(owned):
    parent, db, ref = owned
    for bad in [{"origin_profile": "/other/profile"}, {"origin_conversation": "other"}]:
        with pytest.raises(ValueError):
            import_samples(db, ref, [_sample(**bad)], import_id="denied", source_sha256="c" * 64, now=200, apply=True)
    (Path(db.db_path).parent / "config.yaml").write_text("noting: {enabled: false}")
    with pytest.raises(ValueError, match="enabled"):
        import_samples(db, ref, [_sample()], import_id="off", source_sha256="c" * 64, now=200, apply=True)
    assert not store.imported_history(db, ref, 200)


def test_declared_conversation_source_requires_matching_owner_proof(owned):
    parent, db, ref = owned
    args = dict(import_id="claimed-owner", source_sha256="e" * 64, now=200, apply=True,
                source_kind="conversation", source_conversation=ref)
    with pytest.raises(ValueError, match="owner proof"):
        import_samples(db, ref, [_sample()], **args)
    with pytest.raises(ValueError, match="owner proof"):
        import_samples(db, ref, [_sample(proof=dict(owner_verified=True, owner_conversation_ref="other"))], **args)
    proven = _sample(proof=dict(source="isolated_session_db", owner_verified=True, owner_conversation_ref=ref))
    with pytest.raises(ValueError, match="conflicts"):
        import_samples(db, ref, [{**proven, 'source_conversation_ref': 'other'}], **args)
    receipt = import_samples(db, ref, [proven], **args)
    assert receipt["ownership"] == "same_target_verified"
    event = store.imported_history(db, ref, 200)[0]["events"][0]
    assert event["source_conversation_ref"] == ref and event["ownership"] == "same_target_verified"
    assert import_samples(db, ref, [proven], **args)["already_applied"] is True


def test_stream_and_late_receipt_cannot_complete_or_contaminate_successor(owned):
    from agent.auxiliary_hooks import run_with_aux_hooks
    from secretary.adaptive_samples import start, finish, scope, auxiliary_receipt
    parent, db, ref = owned
    old = start(parent, "compaction", "old-operation")
    route = dict(aux_task="compression", metadata={}, client=SimpleNamespace(), kwargs={},
                 provider="openai", model="old-model", api_mode="chat_completions", streaming=True)
    with scope(old):
        run_with_aux_hooks(_response, **route)
    finish(old, "cancelled", block_seconds=3, block_scope="native_compaction_registration")
    path = Path(db.db_path).parent / "config.yaml"
    config = json.loads(path.read_text())
    models = config["noting"]["adaptive_idle_token_saving"]["models"]["openai"]
    models["new-model"] = models["test/runtime"]
    path.write_text(json.dumps(config))
    parent.model = "new-model"
    successor = start(parent, "compaction", "new-operation")
    with scope(old):
        auxiliary_receipt(_response(), aux_task="compression", provider="openai", model="late-old",
                          api_mode="chat_completions", streaming=False)
    with scope(successor):
        response = _response()
        response.model = "new-model"
        run_with_aux_hooks(lambda: response, **{**route, "model": "new-model", "streaming": False})
    finish(successor, "completed", block_seconds=1, block_scope="native_compaction_registration")
    samples = _samples(db, ref)
    assert len(samples) == 2
    assert samples[0]["usage_complete"] is False and samples[0]["usage"]["input_tokens"] is None
    assert samples[1]["usage_complete"] is True
    assert samples[1]["model_identity"]["model"] == "new-model"
    assert samples[0]["proof"]["requests"] == 1


def test_pending_dispatch_and_closed_switch_stay_unknown_or_native(owned):
    from secretary.adaptive_samples import start, finish
    parent, db, ref = owned
    collector = start(parent, "compaction", "pending-operation")
    collector.dispatch()
    finish(collector, "cancelled", block_seconds=1)
    assert _samples(db, ref)[0]["usage_complete"] is False
    assert _samples(db, ref)[0]["proof"]["dispatches"] == 1
    (Path(db.db_path).parent / "config.yaml").write_text("noting: {enabled: false}")
    disabled = start(parent, "compaction", "disabled")
    disabled.dispatch()
    finish(disabled, "completed")
    assert len(_samples(db, ref)) == 1


@pytest.mark.parametrize('change', ['disable', 'owner'])
def test_inflight_cost_settles_to_original_owner_after_disable(owned, change):
    from agent.auxiliary_hooks import run_with_aux_hooks
    from secretary.adaptive_samples import scope
    parent, db, ref = owned
    observation = SimpleNamespace(operation_id="owned-before-disable", state="running", cancel_requested=False)
    registration = SimpleNamespace(observation=observation, fence=SimpleNamespace())
    runtime.maintenance(parent, registration)
    with scope(observation._adaptive_collector):
        run_with_aux_hooks(_response, aux_task="compression", metadata={}, client=SimpleNamespace(), kwargs={},
                           provider="openai", model="test/aux", api_mode="chat_completions")
    if change == 'disable':
        (Path(db.db_path).parent / "config.yaml").write_text("noting: {enabled: false}")
    else:
        parent._secretary_conversation_ref = 'replacement-owner'
    observation.state = "cancelled"
    runtime.maintenance(parent, registration, finished=True)
    sample = _samples(db, ref)[0]
    assert sample["usage_complete"] is True and sample["usage"]["input_tokens"] == 40
    assert sample["operation_id"] == "owned-before-disable"
    if change == 'owner':
        assert sample['context_after'] is None
        assert not store.history(db, 'replacement-owner', time.time())
    assert not [event for event in store.history(db, ref, time.time()) if event["kind"] == "state_refresh"]


def test_idle_task_resolves_joint_association_added_after_dispatch(owned):
    from secretary.adaptive_samples import start, finish
    parent, db, ref = owned
    admission_id = db.noting_admit(ref, "u1", kind="idle")
    collector = start(parent, "noting", "late-linked-child", admission_id=admission_id)
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_noting_attempts SET operation_id=? WHERE admission_id=?",
        ("native-operation", admission_id)))
    finish(collector, "cancelled", block_seconds=0, block_scope="background_not_main_block")
    assert _samples(db, ref)[0]["joint_operation_id"] == "native-operation"


def test_local_import_cli_preserves_source_and_reaches_policy_snapshot(owned, monkeypatch, tmp_path, capsys):
    from hashlib import sha256
    from scripts.adaptive_empirical_import import main
    parent, db, ref = owned
    package = tmp_path / "numeric-source.json"
    package.write_text(json.dumps({"samples": [_sample()]}))
    digest = sha256(package.read_bytes()).hexdigest()
    monkeypatch.setattr("hermes_cli.profiles.profile_exists", lambda name: name == "isolated")
    monkeypatch.setattr("hermes_cli.profiles.get_profile_dir", lambda name: Path(db.db_path).parent)
    main(["apply", "--profile", "isolated", "--target", ref, "--input", str(package), "--import-id", "cli"])
    assert json.loads(capsys.readouterr().out)["applied"] is True
    measured, history = runtime.snapshot(parent, db, ref, runtime.settings.for_db(db, ref, parent=parent), time.time())
    assert not history
    samples = measured["historical_cohorts"][0]["events"]
    assert samples[0]["event_id"] == "old"
    assert samples[0]["usage"]["input_tokens"] == 40
    assert sha256(package.read_bytes()).hexdigest() == digest


def test_imported_then_native_receipts_update_formal_maintenance_estimate(real_parent, db, monkeypatch):
    from agent.auxiliary_hooks import run_with_aux_hooks
    from secretary.adaptive_features import build_features
    from secretary.adaptive_cost import maintenance_profile
    parent, ref = real_parent, real_parent._secretary_conversation_ref
    compact = _sample("historical-compact", context_after=250, joint_operation_id="historical-joint",
                      usage=dict(input_tokens=1000, cache_read_tokens=0, cache_write_tokens=0, output_tokens=0))
    noting = _sample("historical-noting", component="noting", joint_operation_id="historical-joint",
                     block_seconds=0, block_scope="background_not_main_block",
                     usage=dict(input_tokens=500, cache_read_tokens=0, cache_write_tokens=0, output_tokens=0))
    import_samples(db, ref, [compact, noting], import_id="learning", source_sha256="d" * 64, now=200, apply=True)
    config = runtime.settings.for_db(db, ref, parent=parent)
    def estimate():
        measured, history = runtime.snapshot(parent, db, ref, config, time.time())
        return maintenance_profile(build_features(measured, history, config), config)
    before = estimate()
    assert before is not None
    def execute(agent, messages, system, **kwargs):
        run_with_aux_hooks(_response, aux_task="compression", metadata={}, client=SimpleNamespace(), kwargs={},
                           provider="openai", model="test/aux", api_mode="chat_completions")
        return messages, system
    parent._compression_feasibility_checked = True
    monkeypatch.setattr("agent.conversation_compression.compress_context", execute)
    parent._compress_context(parent._session_messages, None, force=True)
    after = estimate()
    assert after is not None and after.cost != before.cost
    sample_id = _samples(db, ref)[0]["event_id"]
    assert any(sample_id in scenario.diagnostics["scenario"]["ids"] for scenario in after.scenarios)


@pytest.mark.parametrize('interference', [None, 'branch', 'next_compaction', 'rewind', 'runtime_replacement', 'path_read_failure'])
def test_real_native_rotation_tracks_only_its_committed_path(real_parent, db, monkeypatch, interference):
    """Real compress_context/lease/publish_compression_child; control summary output only."""
    from agent.auxiliary_hooks import run_with_aux_hooks
    from agent.context_compressor import SUMMARY_PREFIX
    from secretary.noting_native_link import adopt_native_publication
    from tests.agent.test_compression_rotation_state import _seed_bulk_head
    parent, ref, original = real_parent, real_parent._secretary_conversation_ref, real_parent.session_id
    _seed_bulk_head(db, original)
    parent._session_messages = db.get_messages_as_conversation(original, include_row_ids=True)
    parent.context_compressor.update_from_response({'prompt_tokens': 50000})
    parent.compression_in_place = False
    parent.tools = []
    parent._compression_feasibility_checked = True
    monkeypatch.setattr(parent, '_build_system_prompt', lambda *args, **kwargs: 'frozen system')
    # Noting admission still runs; its unrelated asynchronous model worker is controlled.
    monkeypatch.setattr('secretary.noting_runtime._dispatch_joint_decision', lambda _parent, decision, *_args: decision)

    def summary(messages, **kwargs):
        run_with_aux_hooks(_response, aux_task='compression', metadata={}, client=SimpleNamespace(), kwargs={},
                           provider='openai', model='test/aux', api_mode='chat_completions')
        parent.context_compressor.last_real_prompt_tokens = 0
        parent.context_compressor.compression_count += 1
        parent.context_compressor._last_compression_made_progress = True
        return [{'role': 'user', 'content': SUMMARY_PREFIX + '\nEarlier work.', '_compressed_summary': True},
                {'role': 'assistant', 'content': 'persisted answer'}]

    monkeypatch.setattr(parent.context_compressor, 'compress', summary)
    published = []
    publication_proofs = []

    def branch(agent, child):
        db.create_session('branch-after-publication', source='test', parent_session_id=child,
                          model_config={'_branched_from': child})
        agent.session_id = 'branch-after-publication'

    def next_compaction(agent, child):
        assert db.try_acquire_compression_lock(child, 'next-native-operation')
        db.publish_compression_child(parent_session_id=child, child_session_id='next-native-child', source='test',
                                     compression_lock_holder='next-native-operation',
                                     messages=[{'role': 'user', 'content': SUMMARY_PREFIX + '\nNext operation.'}])
        agent.session_id = 'next-native-child'

    def rewind(agent, child):
        user = next(row for row in db.get_messages(child) if row['role'] == 'user')
        db.rewind_to_message(child, user['id'])

    def runtime_replacement(agent, child):
        from tests.secretary.test_noting_runtime import _agent
        replacement = _agent(db, child)
        published.append(replacement)  # Keep the actual bound runtime alive through settlement.

    def path_read_failure(agent, child):
        def fail_read(*args):
            raise RuntimeError('controlled unavailable path metadata')
        monkeypatch.setattr('secretary.adaptive_samples._path_witness', fail_read)

    handlers = {None: lambda _agent, _child: None, 'branch': branch, 'next_compaction': next_compaction,
                'rewind': rewind, 'runtime_replacement': runtime_replacement, 'path_read_failure': path_read_failure}

    def after_publication(agent, registration, messages, result):
        adopt_native_publication(agent, registration, messages, result)
        child = agent.session_id
        published.append(child)
        collector = registration.observation._adaptive_collector
        publication_proofs.append((collector.initial_path, collector.publication_path))
        handlers[interference](agent, child)

    monkeypatch.setattr('secretary.noting_native_link.adopt_native_publication', after_publication)
    parent._compress_context(parent._session_messages, None, approx_tokens=50000, force=True)
    assert published and published[0] != original
    assert db.get_session(original)['end_reason'] == 'compression'
    assert db.get_session(published[0])['parent_session_id'] == original
    assert db.resolve_conversation_ref(published[0]) == ref
    sample = next(row for row in _samples(db, ref) if row['component'] == 'compaction')
    assert sample['context_before'] == 50000 and sample['usage_complete'] is True
    refreshed = [row for row in store.history(db, ref, time.time()) if row['kind'] == 'state_refresh']
    if interference is None:
        assert publication_proofs[0][1] is not None, publication_proofs
        assert sample['outcome'] == 'completed'
        assert 0 < sample['context_after'] < sample['context_before']
        assert sample['context_after_source'] == 'native_post_compaction_rough'
        assert len(refreshed) == 1
    else:
        assert sample['context_after'] is None
        assert not refreshed
