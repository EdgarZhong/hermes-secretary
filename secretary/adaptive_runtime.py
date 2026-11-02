"""Fail-safe observations and policy calls at existing native maintenance seams."""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import replace

from secretary import adaptive_config as settings
from secretary import adaptive_store as store

logger = logging.getLogger(__name__)


class SourceInput(str):
    """In-process origin evidence; never serialized or reconstructed from message text."""


def mark_input(value, source, event_id=None):
    if not isinstance(value, str):
        return value
    from agent.message_metadata import TrustedUserInput
    marked = value if isinstance(value, TrustedUserInput) else SourceInput(value)
    marked._adaptive_source = source
    marked._adaptive_event_id = event_id or uuid.uuid4().hex
    return marked


def origin(value):
    source = getattr(value, "_adaptive_source", "unknown")
    return source if source in {"user", "heartbeat", "reminder", "framework"} else "unknown"


def _owner(parent):
    try:
        return _read_owner(parent)
    except Exception:
        logger.debug("Adaptive owner unavailable", exc_info=True)
        return None


def _read_owner(parent):
    from secretary.noting_runtime import is_main_conversation_agent, _main_conversation_ref
    if not is_main_conversation_agent(parent):
        return None
    db, ref = parent._session_db, _main_conversation_ref(parent)
    config = settings.for_db(db, ref, parent=parent)
    from secretary.noting_scope import settings_for_db
    return (db, ref, config) if ref and config and settings_for_db(db, ref).enabled else None


def record_event(db, ref, kind, *, source="unknown", verified=False, event_id=None, at=None, parent=None, config=None, **values):
    config = config or settings.for_db(db, ref, parent=parent)
    if not config or not ref:
        return False
    try:
        event = {"event_id": event_id or uuid.uuid4().hex, "at": time.time() if at is None else float(at),
                 "kind": kind, "source": source, "verified": verified,
                 "model_identity": config["model_identity"], "model_contract": config["model_contract"],
                 "model_key": _contract_key(config["model_contract"]), **values}
        return db._execute_write(lambda conn: store.event_conn(conn, ref, event))
    except Exception:
        logger.debug("Adaptive event unavailable", exc_info=True)
        return False


def user_arrived(db, session_id, *, event_id=None, at=None, parent=None, ingress="unknown", activity="submission"):
    """Called only by verified native user-input entrances, before queue/admission."""
    if db is None:
        return False
    try:
        ref = db.resolve_conversation_ref(session_id)
        config = settings.for_db(db, ref, parent=parent, session_id=session_id)
        if config is None:
            return False
        moment = time.time() if at is None else at
        inserted = record_event(db, ref, "user_activity", source="user", verified=True,
                                event_id=event_id, at=moment, ingress=ingress, activity=activity, config=config)
        if inserted:
            db._execute_write(lambda conn: store.invalidate_conn(db, conn, ref, moment))
            if parent is not None:
                from agent.compression_read import compression_state
                active = compression_state(parent)
                if active.get("active"):
                    # A send is a collision only when the actual host refuses it; see blocked_send().
                    parent._adaptive_last_arrival_operation = active.get("operation_id")
        return inserted
    except Exception:
        logger.debug("Adaptive user arrival unavailable", exc_info=True)
        return False


def _settle_existing_heartbeat(parent, value):
    from secretary.noting_runtime import is_main_conversation_agent, _main_conversation_ref
    if origin(value) != "heartbeat" or not is_main_conversation_agent(parent):
        return
    db, ref = parent._session_db, _main_conversation_ref(parent)
    if ref:
        db._execute_write(lambda conn: store.settle_claim_conn(conn, ref))


def turn_started(parent, value, *, at=None):
    owner = _owner(parent)
    if owner is None:
        # A claim already accepted under its old contract still crosses the native
        # admitted-Turn boundary when configuration has since been removed.
        _settle_existing_heartbeat(parent, value)
        return
    db, ref, _config = owner
    now = time.time() if at is None else at
    parent._adaptive_turn_source = origin(value)
    parent._adaptive_turn_started_at = now
    parent._adaptive_turn_id = getattr(value, "_adaptive_event_id", None) or uuid.uuid4().hex
    def write(conn):
        store.invalidate_conn(db, conn, ref, now)
        if parent._adaptive_turn_source == "heartbeat":
            store.settle_claim_conn(conn, ref)
    db._execute_write(write)


def _contract_key(contract):
    from secretary.adaptive_model_config import digest
    return digest(contract)


def model_key(parent):
    from secretary.adaptive_model_config import parent_contract
    return _contract_key(parent_contract(parent))


def context_contract(parent):
    compressor = getattr(parent, "context_compressor", None)
    return [getattr(compressor, "context_length", None), getattr(compressor, "threshold_tokens", None)]


def _epoch(db, ref):
    with db._read_ctx() as conn:
        row = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?", (ref,)).fetchone()
    return row[0] if row else db._execute_write(lambda conn: db.noting_compaction_interval_conn(conn, ref))


def snapshot(parent, db, ref, config, at):
    from agent.context_compaction_request import read_context_usage
    from agent.compression_read import compression_state
    usage, threshold = read_context_usage(parent)
    history = store.history(db, ref, at)
    from secretary.adaptive_features import clean_events
    known_history = clean_events(history, at)
    with db._read_ctx() as conn:
        hb = conn.execute("SELECT * FROM secretary_heartbeats WHERE conversation_ref=?", (ref,)).fetchone()
        mode = store.heartbeat_conn(conn, ref)
        path_version = conn.execute("SELECT rewind_count FROM sessions WHERE id=?", (parent.session_id,)).fetchone()
    adaptive_current = bool(mode and (mode["config_version"] == config["config_version"] or mode["claim_revision"] is not None))
    anchor = (hb["last_fired_at"] or hb["created_at"] or (mode["fallback_anchor"] if adaptive_current else 0)) if hb else None
    interval = mode["interval_seconds"] if adaptive_current else hb["interval_seconds"] if hb else None
    users = [event["at"] for event in known_history if event["kind"] == "user_activity"
             and event.get("verified") is True and event.get("source") == "user"]
    maintenance = [event["at"] for event in known_history if event["kind"] == "maintenance_end"]
    from secretary.noting_scope import settings_for_db
    reminder_due, reminder_known = _next_reminder(db, ref, at)
    current = settings_for_db(db, ref)
    from secretary.noting_runtime import noting_local_enabled
    from secretary.adaptive_bootstrap import read as read_bootstrap
    value = {"now": at, "conversation_ref": ref, "context_tokens": usage or None,
             "context_limit": getattr(getattr(parent, "context_compressor", None), "context_length", None),
             "native_threshold_tokens": threshold or None, "last_user_at": max(users) if users else None,
             "last_maintenance_at": max(maintenance) if maintenance else None,
             "heartbeat_mode": mode["mode"] if adaptive_current else "business",
             "heartbeat_interval_seconds": interval,
             "current_mode_native": not adaptive_current or mode["config_version"] == "native", "heartbeat_anchor": anchor,
             "heartbeat_next_due": anchor + interval if anchor is not None and interval is not None else None,
             "heartbeat_status": hb["status"] if hb else "absent", "next_reminder_at": reminder_due,
             "next_reminder_known": reminder_known,
             "idle_enabled": current.idle_enabled and noting_local_enabled(db, ref), "maintenance_running": compression_state(parent)["active"],
             "idle_period": db.noting_idle_state(ref), "timezone": config.get("timezone"),
             "model": getattr(parent, "model", None), "provider": getattr(parent, "provider", None),
             "model_key": model_key(parent), "context_epoch": _epoch(db, ref),
             "context_path": [parent.session_id, path_version[0]] if path_version else None,
             "idle_config": [current.idle_enabled, current.idle_delay_seconds, current.idle_threshold_tokens],
             "historical_cohorts": store.imported_history(db, ref, at),
             "bootstrap_priors": read_bootstrap(db, ref, at)}
    return value, history


def finish_turn(parent, at, *, idle_allowed=True):
    """Return adopted deadline/disabled marker, or None to retain the native path."""
    try:
        owner = _owner(parent)
        if owner is None:
            return None
        db, ref, config = owner
        source = getattr(parent, "_adaptive_turn_source", "unknown")
        from agent.context_compaction_request import read_context_usage
        started = getattr(parent, "_adaptive_turn_started_at", None)
        duration = at - started if isinstance(started, (int, float)) and at >= started else None
        record_event(db, ref, "turn_end", source=source, verified=source != "unknown", at=at, parent=parent,
                     event_id="turn:" + getattr(parent, "_adaptive_turn_id", uuid.uuid4().hex),
                     context_tokens=read_context_usage(parent)[0] or None, model_key=model_key(parent),
                     context_epoch=_epoch(db, ref), context_contract=context_contract(parent), duration_seconds=duration)
        measured, history = snapshot(parent, db, ref, config, at)
        from secretary.adaptive_policy import decide
        decision = settings.validate_decision(decide(measured, history, config))
        record_event(db, ref, "decision", source="framework", verified=True, at=at, parent=parent,
                     decision=decision, model_key=model_key(parent), stage="proposed",
                     shadow_only=config.get("shadow_only") is True)
        if config.get("shadow_only") is True or decision.get("fallback") is True:
            db._execute_write(lambda conn: store.native_mode_conn(conn, ref))
            return None
        decision["model_key"] = model_key(parent)
        decision["context_path"] = measured["context_path"]
        decision["context_contract"] = context_contract(parent)
        decision["idle_config"] = measured["idle_config"]
        if not idle_allowed:
            db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, decision["mode"], config))
            return None
        if not store.commit_plan(db, ref, at=at, expected_period=measured["idle_period"],
                                 decision=decision, config=config, context_epoch=_epoch(db, ref)):
            return None
        return {"due_at": at + decision["delay_seconds"] if decision["delay_seconds"] is not None else None}
    except Exception:
        logger.warning("Adaptive policy failed; retaining native maintenance", exc_info=True)
        return None


def _idle_plan_valid(parent, original, config, plan, path, epoch):
    return bool(config and path and plan["status"] == "pending"
                and plan["config_version"] == config["config_version"]
                and plan["decision"].get("context_path") == [parent.session_id, path[0]]
                and plan["decision"]["context_epoch"] == epoch
                and plan["decision"].get("model_key") == model_key(parent)
                and plan["decision"].get("context_contract") == context_contract(parent)
                and plan["decision"].get("idle_config") == [original.idle_enabled, original.idle_delay_seconds,
                                                            original.idle_threshold_tokens])


def _restore_native_idle(parent, db, ref, plan, period):
    from secretary.noting_scope import is_current_main_runtime, settings_for_db
    def recheck(conn, current_plan, _period):
        if not is_current_main_runtime(parent):
            return None
        original = settings_for_db(db, ref)
        config = settings.for_db(db, ref, parent=parent, conn=conn)
        path = conn.execute("SELECT rewind_count FROM sessions WHERE id=?", (parent.session_id,)).fetchone()
        epoch = db.noting_compaction_interval_conn(conn, ref)
        return (None if _idle_plan_valid(parent, original, config, current_plan, path, epoch)
                else original.idle_delay_seconds)
    return store.restore_native_idle(db, ref, expected_plan=plan, expected_period=period, recheck=recheck)


def idle_settings(parent, original):
    """Adapt an exact plan, or retire its early clock before returning native settings."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref:
        return original
    owner = _owner(parent)
    config = owner[2] if owner else None
    with db._read_ctx() as conn:
        plan = store.plan_conn(conn, ref)
        period = db.noting_idle_state_conn(conn, ref)
        path = conn.execute("SELECT rewind_count FROM sessions WHERE id=?", (parent.session_id,)).fetchone()
    if not plan or not period or plan["finished_at"] != period["last_turn_finished_at"]:
        return original
    if plan["status"] != "pending":
        return original if period["trigger_produced_at"] is None else replace(original, idle_threshold_tokens=None)
    if _idle_plan_valid(parent, original, config, plan, path, _epoch(db, ref)):
        return replace(original, idle_threshold_tokens=plan["decision"]["threshold_tokens"])
    _restore_native_idle(parent, db, ref, plan, period)
    return original


def request_observed(parent, canonical_usage, unknown, *, failed=False):
    owner = _owner(parent)
    if owner is None:
        return
    db, ref, _config = owner
    values = {key: getattr(canonical_usage, key, None) if canonical_usage is not None and key not in unknown else None
              for key in ("input_tokens", "cache_read_tokens", "output_tokens")}
    if canonical_usage is not None and "input_tokens" not in unknown:
        values["input_tokens"] = canonical_usage.prompt_tokens
    total, cache = values["input_tokens"], values["cache_read_tokens"]
    if total is not None and cache is not None and cache > total:
        values["input_tokens"] = values["cache_read_tokens"] = None
    record_event(db, ref, "request", source=getattr(parent, "_adaptive_turn_source", "unknown"),
                 verified=True, parent=parent, outcome="failed" if failed else "observed", input_semantics="total",
                 model_key=model_key(parent), turn_id=getattr(parent, "_adaptive_turn_id", None),
                 cache_write_tokens=getattr(canonical_usage, "cache_write_tokens", None), **values)


def maintenance(parent, registration, *, finished=False, trigger=None):
    try:
        _maintenance(parent, registration, finished=finished, trigger=trigger)
    except Exception:
        logger.debug("Adaptive maintenance observation unavailable", exc_info=True)


def _maintenance(parent, registration, *, finished=False, trigger=None):
    owner = _owner(parent)
    if owner is None:
        return
    db, ref, _config = owner
    observation = registration.observation
    now = time.time()
    if not finished:
        observation._adaptive_started_at = now
        observation._adaptive_idle = trigger == "noting_joint_idle"
        from agent.context_compaction_request import read_context_usage
        observation._adaptive_context_before = read_context_usage(parent)[0]
    started = getattr(observation, "_adaptive_started_at", None)
    from agent.context_compaction_request import read_context_usage
    partial = bool(getattr(getattr(registration.fence, "partial", None), "adopted", False))
    outcome = "partial" if finished and observation.state == "completed" and partial else observation.state
    record_event(db, ref, "maintenance_end" if finished else "maintenance_start", source="framework", verified=True,
                 parent=parent, event_id=observation.operation_id + (":end" if finished else ":start"), at=now,
                 operation_id=observation.operation_id, outcome=outcome, model_key=model_key(parent),
                 trigger="idle" if getattr(observation, "_adaptive_idle", False) else "native",
                 context_before=getattr(observation, "_adaptive_context_before", None),
                 context_after=read_context_usage(parent)[0] if finished else None, usage_complete=False,
                 idle=getattr(observation, "_adaptive_idle", False),
                 duration_seconds=now - started if finished and started is not None else None,
                 duration_scope="native_compaction_registration",
                 cancel_requested=observation.cancel_requested)
    if finished:
        # Refresh audit state only: an already consumed Idle cycle is never rearmed.
        measured, _history = snapshot(parent, db, ref, _config, now)
        from secretary.adaptive_policy import decide
        decision = settings.validate_decision(decide(measured, _history, _config))
        if _config.get("shadow_only") is not True and decision.get("fallback") is not True:
            db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, decision["mode"], _config))
        record_event(db, ref, "state_refresh", source="framework", verified=True, parent=parent,
                     context_tokens=measured["context_tokens"])


def cancelled(parent, operation_id, outcome):
    owner = _owner(parent)
    if owner is not None:
        db, ref, _config = owner
        user_arrived(db, parent.session_id, event_id=operation_id + ":user_cancel_activity",
                     parent=parent, ingress="web_submit", activity="cancel")
        record_event(db, ref, "cancel", source="user", verified=True,
                     event_id=operation_id + ":user_cancel:" + outcome, operation_id=operation_id, outcome=outcome,
                     trigger="idle" if _idle_operation(db, ref, operation_id) else "native")


def _idle_operation(db, ref, operation_id):
    return any(item["kind"] == "maintenance_start" and item.get("operation_id") == operation_id and item.get("idle")
               for item in store.history(db, ref, time.time()))


def composer_cancel(parent, *, operation_id=None):
    from agent.compression_read import compression_state
    state = compression_state(parent)
    identity = operation_id or state.get("operation_id")
    if identity:
        cancelled(parent, identity, "requested" if state["active"] else state["state"])
    else:
        owner = _owner(parent)
        if owner is not None:
            user_arrived(owner[0], parent.session_id, event_id="composer_cancel:" + uuid.uuid4().hex,
                         parent=parent, ingress="web_submit", activity="cancel")
    return identity


def blocked_send(parent, event_id):
    owner = _owner(parent)
    if owner is None:
        return
    from agent.compression_read import compression_state
    state = compression_state(parent)
    db, ref, _config = owner
    if not state["active"]:
        return
    # Prove Idle provenance from the actual operation's persisted start observation.
    events = store.history(db, ref, time.time())
    if not any(item["kind"] == "maintenance_start" and item.get("operation_id") == state["operation_id"]
               and item.get("idle") for item in events):
        return
    record_event(db, ref, "blocked_send", source="user", verified=True, operation_id=state["operation_id"],
                 event_id=state["operation_id"] + ":blocked:" + event_id, trigger="idle")


def web_input(session, text, *, event_id=None):
    """Public prompt.submit only; synthesized host submissions must not call this."""
    parent = session.get("agent")
    db = getattr(parent, "_session_db", None)
    if db is not None and settings.for_db(db, parent=parent):
        identity = event_id or uuid.uuid4().hex
        user_arrived(db, parent.session_id, event_id="web:" + identity, parent=parent, ingress="web_submit")
        return mark_input(text, "user", "web:" + identity)
    if parent is None and session.get("session_key"):
        try:
            from tui_gateway import server
            with server._session_db(session) as db:
                if db is not None and settings.for_db(db, session_id=session["session_key"]):
                    identity = event_id or uuid.uuid4().hex
                    user_arrived(db, session["session_key"], event_id="web:" + identity, ingress="web_submit")
                    return mark_input(text, "user", "web:" + identity)
        except Exception:
            logger.debug("Adaptive cold Web ingress unavailable", exc_info=True)
    return text


def gateway_input(db, session_id, value, event, source):
    """Original adapter event after native routing; internal/bot events never prove human."""
    if (db is None or not settings.for_db(db, session_id=session_id) or getattr(event, "internal", True) is not False
            or (getattr(event, "metadata", {}) or {}).get("synthetic_prompt")
            or (getattr(event, "metadata", {}) or {}).get("hermes_plugin_injection")
            or getattr(event, "allow_gateway_control", True) is not True
            or getattr(event, "_heartbeat_session_id", None)
            or getattr(source, "is_bot", None) is not False or not getattr(source, "user_id", None)):
        return value
    identity = "gateway:" + str(getattr(source, "platform", "")) + ":" + str(getattr(source, "chat_id", "")) + ":" + str(getattr(event, "message_id", None) or uuid.uuid4().hex)
    user_arrived(db, session_id, event_id=identity, ingress="gateway_adapter")
    return mark_input(value, "user", identity)


def gateway_queue_input(owner, session_key, event):
    """Observe the existing accepted queue, without creating another queue or lease."""
    try:
        db = getattr(getattr(owner, "_session_db", None), "_db", getattr(owner, "_session_db", None))
        if db is None:
            return
        sid = owner._lookup_session_id_under_store_lock(owner.session_store, session_key)
        if sid:
            gateway_input(db, sid, event.text, event, event.source)
    except Exception:
        logger.debug("Adaptive Gateway queue observation unavailable", exc_info=True)


def gateway_owned_input(owner, event, value):
    if owner is None:
        return value
    try:
        db = getattr(getattr(owner, "_session_db", None), "_db", getattr(owner, "_session_db", None))
        if db is None:
            return value
        key = owner._session_key_for_source(event.source)
        sid = owner._lookup_session_id_under_store_lock(owner.session_store, key)
        return gateway_input(db, sid, value, event, event.source) if sid else value
    except Exception:
        logger.debug("Adaptive Gateway source observation unavailable", exc_info=True)
        return value


def refresh_heartbeat_priority(parent):
    owner = _owner(parent)
    if owner is None:
        return
    from agent.context_compaction_request import read_context_usage
    db, ref, _config = owner
    record_event(db, ref, "context_read", source="framework", verified=True, parent=parent,
                 context_tokens=read_context_usage(parent)[0], model_key=model_key(parent),
                 context_contract=context_contract(parent))


def web_submit_input(session, text, params, *, internal_hosted_submit=False, turn_author=None):
    if internal_hosted_submit or turn_author is not None:
        return text
    return web_input(session, text, event_id=params.get("client_submission_id"))


def _next_reminder(db, ref, at):
    from secretary.noting_scope import scheduler_settings_for_db
    try:
        scheduler = scheduler_settings_for_db(db)
        if scheduler.configuration_failure:
            return None, False
        if not scheduler.enabled:
            return None, True
        with db._read_ctx() as conn:
            row = conn.execute("SELECT MIN(next_run_at) FROM secretary_schedule_registry WHERE conversation_ref=? "
                               "AND state='pending' AND enabled=1 AND delivery_semantics='user_reminder' "
                               "AND next_run_at IS NOT NULL", (ref,)).fetchone()
        return (max(at, row[0]) if row[0] is not None else None), True
    except Exception:
        logger.debug("Adaptive next Reminder observation unavailable", exc_info=True)
        return None, False
