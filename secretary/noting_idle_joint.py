"""Idle requests the same native pre-summary joint entrance as manual/auto compression."""


def request_idle_joint(parent, *, measurement=None, messages=None, now=None,
                       expected_period=None, expected_owner=None):
    from agent.context_compaction_request import _epoch, _lock
    from secretary import noting_runtime as rt
    from secretary.noting_scope import is_current_main_runtime

    with _lock(parent):
        if (not is_current_main_runtime(parent) or not rt.is_main_conversation_agent(parent)
                or expected_owner is not None and _epoch(parent) is not expected_owner):
            return rt._skip("not_main_owner")
        db, ref, epoch = parent._session_db, rt._main_conversation_ref(parent), _epoch(parent)
        row = db.get_session(parent.session_id)
        with db._read_ctx() as conn:
            route = db.resolve_conversation_route_conn(conn, ref)
        if not row or row.get("archived") or not route or route["id"] != parent.session_id:
            return rt._skip("not_main_owner")
        settings = rt.settings_for_db(db)
        if (not settings.enabled or not settings.idle_enabled
                or not rt.noting_local_enabled(db, ref)):
            return rt.try_admit_idle(db, ref, settings=settings, now=now, expected_period=expected_period)
        # Require the real live prefix before consuming a due period. It is frozen
        # again at the native lease boundary, where the child actually starts.
        from secretary.noting_child import freeze_parent_active_prefix, NotingChildError
        with db._read_ctx() as conn:
            anchor = db.get_foreground_anchor_conn(conn, ref)
        try:
            if anchor is None:
                return rt._skip("parent_context_unavailable")
            freeze_parent_active_prefix(parent, anchor["message_uid"], messages, conversation_ref=ref)
        except NotingChildError:
            return rt._skip("parent_context_unavailable")
        decision = rt._joint_trigger_decision(parent, db, ref, "idle", measurement,
                                               rt._persisted_main_execution(parent), now, expected_period)
    if decision.action != "request":
        if decision.reason == "external_main_execution":
            from secretary.framework_messages import publish_external_execution_notice
            publish_external_execution_notice(parent, expected_conversation_ref=ref)
        return decision
    from secretary.noting_compact import request_parent_compaction
    result = request_parent_compaction(
        parent, threshold_tokens=rt.settings_for_db(db).idle_threshold_tokens,
        expected_owner=(epoch, db, ref), wait_for_completion=False)
    return rt.replace(decision, reuse_status=("idle_compaction_requested" if result.ok else "skip:" + result.status))
