"""Trigger→admission runtime on a real SessionDB: gates, Idle timing, Force gating (02 §4.5–4.11).

The hooks write only for real main Conversation Turns and only when global AND local Noting are
enabled; an off gate means no thread, no scheduler and no write (02 §4.3, §6.6). Force consumes
Hermes-resolved values through ``ContextMeasurement`` and never estimates tokens itself.
"""

from types import SimpleNamespace

import pytest

from hermes_constants import get_hermes_home
from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from secretary import noting_runtime as rt
from secretary.noting_policy import (
    CAPABILITY_RESERVE_ABOVE_128K,
    CAPABILITY_THRESHOLD_BELOW_64K,
    TASK_PROFILE_NOTING,
    TASK_PROFILE_NOTING_WITH_COMPACTION,
    ContextMeasurement,
    NotingSettings,
)
from tests.hermes_state._secretary_noting_harness import add, empty_state, make as _make, open_noting_db, ref_of


# Hermes-resolved pairs exercised below: reserve = max((window - threshold) * 1.20, 66K).
FORCE_WINDOW, FORCE_HERMES = 130_000, 75_000          # reserve 66,000 -> Force threshold 64,000
FLOOR_FAIL_WINDOW, FLOOR_FAIL_HERMES = 120_000, 75_000  # threshold 54,000 < 64K
CEIL_FAIL_WINDOW, CEIL_FAIL_HERMES = 400_000, 240_000   # reserve 192,000 > 128K


@pytest.fixture
def db(tmp_path):
    db = open_noting_db(tmp_path / "state.db")
    yield db
    db.close()


def _settings(enabled=True, delay=500.0, selection=False, selection_threshold=None, compact_after_force=False):
    return NotingSettings(enabled, delay, selection, selection_threshold, compact_after_force)


def _measurement(measured, window=FORCE_WINDOW, hermes=FORCE_HERMES):
    return ContextMeasurement(measured, window, hermes)


def _agent(db, sid):
    from agent.context_compressor import ContextCompressor
    from secretary.noting_scope import bind_main_runtime
    agent = SimpleNamespace(_session_db=db, session_id=sid, platform="telegram",
                            _secretary_conversation_ref=ref_of(db, sid), context_compressor=ContextCompressor(
                                model="test/runtime", config_context_length=FORCE_WINDOW,
                                threshold_percent=.75, threshold_tokens_cap=FORCE_HERMES, quiet_mode=True))
    # SimpleNamespace is not weak-referenceable; use a normal runtime object retained by the host fixture.
    class Runtime:
        pass
    runtime = Runtime()
    runtime.__dict__.update(vars(agent))
    bind_main_runtime(runtime)
    db._test_runtime_agents = [*getattr(db, "_test_runtime_agents", []), runtime]
    return runtime


def make(db, *args, **kwargs):
    _make(db, *args, **kwargs)
    _agent(db, args[0])


def _write_config(text):
    (get_hermes_home() / "config.yaml").write_text(text, encoding="utf-8")


def _admission_count(db):
    with db._read_ctx() as conn:
        return conn.execute("SELECT COUNT(*) FROM secretary_noting_admissions").fetchone()[0]


def test_global_off_hooks_and_admissions_are_inert(db):
    from pathlib import Path
    (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: false\n")
    make(db, "s")
    add(db, "s", "one turn", "m1")
    ref = ref_of(db, "s")
    agent = _agent(db, "s")

    assert rt.note_main_turn_started(agent, at=1000.0) is False
    assert rt.note_main_turn_finished(agent, at=1500.0) is False
    assert db.noting_idle_state(ref) is None

    idle = rt.try_admit_idle(db, ref, now=10_000.0)
    force = rt.try_admit_force(db, ref, _measurement(10_000_000))
    assert (idle.action, idle.reason) == ("skip", "global_disabled")
    assert (force.action, force.reason) == ("skip", "global_disabled")
    assert _admission_count(db) == 0
    assert rt.idle_candidates(db, now=10_000.0) == []


def test_local_off_is_inert_and_turning_it_on_resumes_participation(db):
    make(db, "s")
    add(db, "s", "one turn", "m1")
    ref = ref_of(db, "s")
    agent = _agent(db, "s")
    db.notebook_set_local_enabled(ref, False)

    assert rt.note_main_turn_finished(agent, at=1500.0) is False
    assert db.noting_idle_state(ref) is None
    assert rt.try_admit_idle(db, ref, now=10_000.0).reason == "local_disabled"
    assert rt.try_admit_force(db, ref, _measurement(10_000_000)).reason == "local_disabled"
    assert _admission_count(db) == 0

    db.notebook_set_local_enabled(ref, True)
    assert rt.note_main_turn_finished(agent, at=1500.0) is True
    assert db.noting_idle_state(ref)["last_turn_finished_at"] == 1500.0


def test_idle_admits_after_the_delay_with_the_frozen_anchor(db):
    make(db, "s")
    add(db, "s", "first", "m1")
    add(db, "s", "second", "m2")
    ref = ref_of(db, "s")
    agent = _agent(db, "s")

    assert rt.note_main_turn_started(agent, at=1000.0) is True
    assert rt.note_main_turn_finished(agent, at=1500.0) is True

    early = rt.try_admit_idle(db, ref, now=1999.0)
    assert (early.action, early.reason) == ("skip", "not_idle")

    due = rt.try_admit_idle(db, ref, now=2000.0)
    assert due.action == "admit"
    admission = due.admission
    assert admission.anchor_message_uid == "m2"
    assert admission.kind == "idle"
    assert admission.task_profile == TASK_PROFILE_NOTING
    assert db.noting_admission(admission.admission_id)["anchor_message_uid"] == "m2"

    repeat = rt.try_admit_idle(db, ref, now=2100.0)
    assert (repeat.action, repeat.reason) == ("skip", "same_anchor_admitted")


def test_non_main_turns_never_touch_the_timer(db):
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")
    agent = _agent(db, "s")
    rt.note_main_turn_started(agent, at=1000.0)
    rt.note_main_turn_finished(agent, at=1500.0)

    make(db, "child", parent="s", marker="_delegate_from", source="subagent")
    non_main = [
        SimpleNamespace(_session_db=db, session_id="s", platform="subagent"),
        SimpleNamespace(_session_db=db, session_id="s", side_agent=True),
        SimpleNamespace(_session_db=db, session_id="s", _parent_session_id="s"),
        SimpleNamespace(_session_db=db, session_id="s", _persist_disabled=True),
        SimpleNamespace(_session_db=db, session_id="child", platform="telegram"),
    ]
    for variant in non_main:
        assert rt.is_main_conversation_agent(variant) is False
        assert rt.note_main_turn_started(variant, at=1600.0) is False
        assert rt.note_main_turn_finished(variant, at=1700.0) is False

    state = db.noting_idle_state(ref)
    assert (state["last_turn_started_at"], state["last_turn_finished_at"]) == (1000.0, 1500.0)
    # The main Conversation is still idle despite all that child/hygiene activity.
    assert rt.try_admit_idle(db, ref, now=2000.0).action == "admit"


def test_new_main_turn_resets_the_idle_timer(db):
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")
    agent = _agent(db, "s")
    rt.note_main_turn_finished(agent, at=1500.0)

    assert rt.note_main_turn_started(agent, at=1990.0) is True
    assert rt.try_admit_idle(db, ref, now=2000.0).reason == "not_idle"

    assert rt.note_main_turn_finished(agent, at=2500.0) is True
    assert rt.try_admit_idle(db, ref, now=2999.0).reason == "not_idle"
    assert rt.try_admit_idle(db, ref, now=3000.0).action == "admit"


def test_idle_selection_picks_the_runtime_profile(db):
    make(db, "below")
    add(db, "below", "turn", "m1")
    make(db, "at")
    add(db, "at", "turn", "m1")
    settings = _settings(selection=True, selection_threshold=50_000)
    below_ref, at_ref = ref_of(db, "below"), ref_of(db, "at")
    db.noting_idle_turn_finished(below_ref, 1000.0)
    db.noting_idle_turn_finished(at_ref, 1000.0)

    below = rt.try_admit_idle(db, below_ref, measurement=_measurement(40_000), settings=settings, now=2000.0)
    at = rt.try_admit_idle(db, at_ref, measurement=_measurement(55_000), settings=settings, now=2000.0)
    assert below.admission.task_profile == TASK_PROFILE_NOTING
    assert at.admission.task_profile == TASK_PROFILE_NOTING_WITH_COMPACTION
    assert at.admission.compaction_threshold_tokens == 50_000


def test_idle_defers_to_the_force_path_in_a_covered_segment(db):
    make(db, "s")
    add(db, "s", "first", "m1")
    add(db, "s", "second", "m2")
    ref = ref_of(db, "s")
    db.noting_idle_turn_finished(ref, 1000.0)
    measurement = _measurement(70_000)  # at/above the 64,000 Force threshold

    no_snapshot = rt.try_admit_idle(db, ref, measurement=measurement, now=2000.0)
    assert (no_snapshot.action, no_snapshot.reason) == ("skip", "force_path_owns_segment")

    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1",
                                trigger_type="force", runtime_profile=TASK_PROFILE_NOTING)
    assert rt.try_admit_idle(db, ref, measurement=measurement, now=2000.0).reason == "force_snapshot_present"
    compact = rt.try_admit_idle(db, ref, measurement=measurement, now=2000.0,
                                settings=_settings(compact_after_force=True))
    assert (compact.action, compact.reason) == ("compact_parent", "force_snapshot_present")
    assert _admission_count(db) == 0


def test_force_admission_boundaries_and_same_anchor_dedupe(db):
    make(db, "s")
    add(db, "s", "first", "m1")
    ref = ref_of(db, "s")

    under = rt.try_admit_force(db, ref, _measurement(63_999))
    assert (under.action, under.reason) == ("skip", "below_force_threshold")

    at = rt.try_admit_force(db, ref, _measurement(64_000))
    assert at.action == "admit"
    assert (at.admission.kind, at.admission.anchor_message_uid) == ("force", "m1")
    assert at.admission.task_profile == TASK_PROFILE_NOTING

    assert rt.try_admit_force(db, ref, _measurement(64_000)).reason == "same_anchor_admitted"

    # Different Anchor: concurrent Force Tasks are allowed (02 §4.8).
    add(db, "s", "second", "m2")
    second = rt.try_admit_force(db, ref, _measurement(64_000))
    assert second.action == "admit" and second.admission.anchor_message_uid == "m2"
    assert _admission_count(db) == 2


def test_force_capability_failures_skip_with_reason(db):
    make(db, "floor")
    add(db, "floor", "turn", "m1")
    make(db, "ceiling")
    add(db, "ceiling", "turn", "m1")

    floor = rt.try_admit_force(
        db, ref_of(db, "floor"), _measurement(1_000_000, FLOOR_FAIL_WINDOW, FLOOR_FAIL_HERMES))
    ceiling = rt.try_admit_force(
        db, ref_of(db, "ceiling"), _measurement(1_000_000, CEIL_FAIL_WINDOW, CEIL_FAIL_HERMES))
    assert (floor.action, floor.reason) == ("skip", f"capability_failure:{CAPABILITY_THRESHOLD_BELOW_64K}")
    assert (ceiling.action, ceiling.reason) == ("skip", f"capability_failure:{CAPABILITY_RESERVE_ABOVE_128K}")
    assert _admission_count(db) == 0


def test_force_skips_when_the_segment_already_has_a_force_snapshot(db):
    make(db, "s")
    add(db, "s", "first", "m1")
    add(db, "s", "second", "m2")
    ref = ref_of(db, "s")
    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="m1",
                                trigger_type="force", runtime_profile=TASK_PROFILE_NOTING)

    decision = rt.try_admit_force(db, ref, _measurement(64_000))
    assert (decision.action, decision.reason) == ("skip", "force_snapshot_in_segment")
    assert _admission_count(db) == 0


def test_no_admission_without_a_frozen_anchor(db):
    make(db, "s")
    db.append_message("s", "user", SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                      message_uid="sum", _compressed_summary=True)
    ref = ref_of(db, "s")
    db.noting_idle_turn_finished(ref, 1000.0)

    idle = rt.try_admit_idle(db, ref, now=2000.0)
    force = rt.try_admit_force(db, ref, _measurement(64_000))
    assert (idle.action, idle.reason) == ("skip", "no_frozen_anchor")
    assert (force.action, force.reason) == ("skip", "no_frozen_anchor")
    assert _admission_count(db) == 0


def test_missing_notebook_reader_fails_closed(db, monkeypatch):
    """Unavailable local policy cannot bypass an already-persisted off state."""
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")
    monkeypatch.setattr(db, "notebook_local_enabled_conn", None)

    assert rt.noting_local_enabled(db, ref) is False


def test_trigger_failures_and_write_failures_fail_safe(db, monkeypatch):
    """A failing evaluation or Idle-timer write must not raise into the host loop."""
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")
    db.noting_idle_turn_finished(ref, 1000.0)

    def _boom(*args, **kwargs):
        raise RuntimeError("db is gone")

    monkeypatch.setattr(db, "noting_idle_state", _boom)
    idle = rt.try_admit_idle(db, ref, now=2000.0)
    assert (idle.action, idle.reason) == ("skip", "trigger_error")
    monkeypatch.setattr(db, "noting_force_snapshot_since_boundary", _boom)
    force = rt.try_admit_force(db, ref, _measurement(64_000))
    assert (force.action, force.reason) == ("skip", "trigger_error")

    monkeypatch.setattr(db, "noting_idle_turn_finished", _boom)
    assert rt.note_main_turn_finished(_agent(db, "s"), at=1500.0) is False


def test_state_survives_reopen_and_still_dedupes(tmp_path):
    path = tmp_path / "state.db"
    db = open_noting_db(path)
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")
    db.noting_idle_turn_finished(ref, 1000.0)
    first = rt.try_admit_force(db, ref, _measurement(64_000))
    assert first.action == "admit"
    db.close()

    reopened = open_noting_db(path)
    _agent(reopened, "s")  # The restarted host resolves its native main runtime before admission.
    try:
        assert rt.try_admit_force(reopened, ref, _measurement(64_000)).reason == "same_anchor_admitted"
        assert rt.idle_candidates(reopened, now=1600.0) == [ref]
    finally:
        reopened.close()


def test_d01_external_gate_runs_only_after_a_real_trigger_and_before_admission(db):
    make(db, "force")
    add(db, "force", "turn", "m1")
    force_ref = ref_of(db, "force")

    under = rt.try_admit_force(
        db, force_ref, _measurement(63_999), execution_source="external",
    )
    assert (under.action, under.reason) == ("skip", "below_force_threshold")
    blocked = rt.try_admit_force(
        db, force_ref, _measurement(64_000), execution_source="external",
    )
    assert (blocked.action, blocked.reason) == ("skip", "external_main_execution")
    assert _admission_count(db) == 0

    native = rt.try_admit_force(
        db, force_ref, _measurement(64_000), execution_source="native",
    )
    assert native.action == "admit"

    make(db, "idle")
    add(db, "idle", "turn", "m1")
    idle_ref = ref_of(db, "idle")
    db.noting_idle_turn_finished(idle_ref, 1000.0)
    before = _admission_count(db)
    blocked_idle = rt.try_admit_idle(
        db, idle_ref, now=2000.0, execution_source="external",
    )
    assert (blocked_idle.action, blocked_idle.reason) == ("skip", "external_main_execution")
    assert _admission_count(db) == before
    assert rt.try_admit_idle(
        db, idle_ref, now=2000.0, execution_source="native",
    ).action == "admit"


def test_d01_actual_execution_fact_persists_and_no_request_does_not_overwrite(db):
    make(db, "s")
    add(db, "s", "turn", "m1")
    agent = _agent(db, "s")
    key = "_secretary_last_main_execution"

    assert db.get_session_model_config_value("s", key) is None
    agent._session_init_model_config = {"existing": "kept"}
    assert rt.note_actual_main_execution(agent, "external") is True
    assert rt.main_execution_for_force(agent) == "external"
    assert agent._session_init_model_config == {
        "existing": "kept", "_secretary_last_main_execution": "external",
    }
    assert rt.note_main_turn_finished(agent, at=1500.0) is True
    assert db.get_session_model_config_value("s", key) == "external"

    resumed = _agent(db, "s")
    assert rt.main_execution_for_force(resumed) == "external"
    # A Main turn with no actual model dispatch must preserve the old execution fact.
    assert rt.note_main_turn_finished(resumed, at=1600.0) is True
    assert db.get_session_model_config_value("s", key) == "external"

    assert rt.note_actual_main_execution(resumed, "native") is True
    assert rt.note_main_turn_finished(resumed, at=1700.0) is True
    assert db.get_session_model_config_value("s", key) == "native"

    non_main = SimpleNamespace(_session_db=db, session_id="s", platform="subagent")
    assert rt.note_actual_main_execution(non_main, "external") is False
    assert db.get_session_model_config_value("s", key) == "native"


def test_d01_idle_external_blocks_before_force_snapshot_compaction_branch(db):
    make(db, "s")
    add(db, "s", "first", "m1")
    add(db, "s", "second", "m2")
    ref = ref_of(db, "s")
    db.noting_idle_turn_finished(ref, 1000.0)
    db.notebook_commit_snapshot(
        ref, empty_state(), anchor_message_uid="m1",
        trigger_type="force", runtime_profile=TASK_PROFILE_NOTING,
    )

    decision = rt.try_admit_idle(
        db, ref, measurement=_measurement(70_000), now=2000.0,
        settings=_settings(compact_after_force=True), execution_source="external",
    )
    assert (decision.action, decision.reason) == ("skip", "external_main_execution")
    assert _admission_count(db) == 0
