"""Conversation bindings operated by the live Gateway through its native control socket."""

import asyncio
import json
import re

from gateway.conversation_binding import BINDING_KEY, _RUNTIME_ENDS, bind_conversation, is_bound
from hermes_state_common import _BOUNDARY_END_REASONS


class BindingError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class ConversationBindingControl:
    def __init__(self, runner):
        self.runner = runner
        self.store = runner.session_store

    def _peer(self, profile):
        if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", profile):
            raise BindingError("invalid_profile", "An exact registered Profile is required")
        prefix = f"agent:{profile}:weixin:dm:"
        self.store._ensure_loaded()
        with self.store._lock:
            matches = [entry for key, entry in self.store._entries.items() if key.startswith(prefix)]
        if len(matches) != 1:
            raise BindingError("peer_unavailable", "Exactly one WeChat DM route must exist in this Profile")
        entry = matches[0]
        db = self.store._db_for_key(entry.session_key)
        if db is None:
            raise BindingError("storage_unavailable", "The owning Profile storage is unavailable")
        return entry, db

    @staticmethod
    def _conversation(db, ref):
        if not isinstance(ref, str) or not re.fullmatch(r"conv_[0-9a-f]{32}", ref):
            raise BindingError("invalid_ref", "Supply the full conversation_ref returned by current or list")
        row = db.resolve_conversation_route(ref)
        if not row or row.get("archived") or row.get("end_reason") in _BOUNDARY_END_REASONS:
            raise BindingError("conversation_unavailable", "The Conversation is unavailable")
        if row.get("end_reason") and row["end_reason"] not in _RUNTIME_ENDS:
            raise BindingError("conversation_unavailable", "The Conversation was explicitly ended")
        from secretary.noting_runtime import _CHILD_SOURCES, _delegate_child_row
        if row.get("source") in _CHILD_SOURCES or _delegate_child_row(row):
            raise BindingError("not_main", "Only a Main Conversation can be bound")
        return row

    @staticmethod
    def _view(ref, row):
        return {"conversation_ref": ref, "title": row.get("title") or "", "available": True}

    def _status(self, entry, db):
        if not is_bound(entry):
            return {"bound": False, "conversation": None}
        ref = entry.metadata[BINDING_KEY].get("conversation_ref")
        try:
            conversation = self._view(ref, self._conversation(db, ref))
        except BindingError:
            conversation = {"conversation_ref": ref, "available": False}
        return {"bound": True, "conversation": conversation}

    def _current(self, db, params):
        caller = params.get("caller_locator")
        if not isinstance(caller, str) or not caller:
            raise BindingError("current_unavailable", "Caller context is missing; use list and an explicit conversation_ref")
        if db.get_session(caller) is None:
            raise BindingError("current_unavailable", "Caller context does not belong to this Profile")
        ref = db.resolve_conversation_ref(caller)
        return self._view(ref, self._conversation(db, ref))

    def _list(self, db, limit):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise BindingError("invalid_limit", "limit must be between 1 and 100")
        rows = db._read_all("SELECT id FROM sessions WHERE COALESCE(archived,0)=0 "
                            "ORDER BY COALESCE(last_activity_at,started_at) DESC")
        result, seen = [], set()
        for row in rows:
            ref = db.resolve_conversation_ref(row["id"])
            if ref in seen:
                continue
            seen.add(ref)
            try:
                result.append(self._view(ref, self._conversation(db, ref)))
            except BindingError:
                continue
            if len(result) == limit:
                break
        return result

    def _bind(self, entry, db, ref):
        row = self._conversation(db, ref)
        if is_bound(entry) and entry.metadata[BINDING_KEY].get("conversation_ref") == ref:
            return {"changed": False, "binding": self._status(entry, db)}
        moving = entry.session_id != row["id"]
        if moving and (entry.active_turn_token or self.runner._running_agents.get(entry.session_key)):
            raise BindingError("route_busy", "The WeChat route has an active turn; retry after it finishes")
        bind_conversation(self.store, entry.session_key, row["id"])
        if moving:
            self.runner._evict_cached_agent(entry.session_key)
            self.runner._clear_conversation_scope(entry.session_key, reason="explicit_conversation_binding")
        # A success is backed by the persisted route, not merely the in-memory object.
        host = self.store._routing_db_method("load_gateway_routing_entries")
        saved = host(scope=self.store._routing_scope()) if host else {}
        durable = json.loads(saved.get(entry.session_key, "{}"))
        if durable.get("metadata", {}).get(BINDING_KEY, {}).get("conversation_ref") != ref:
            raise BindingError("outcome_unknown", "Binding persistence was not confirmed; inspect status before retrying")
        return {"changed": True, "binding": self._status(entry, db)}

    def _unbind(self, entry, db):
        if not is_bound(entry):
            return {"changed": False, "binding": self._status(entry, db)}
        if entry.active_turn_token or self.runner._running_agents.get(entry.session_key):
            raise BindingError("route_busy", "The WeChat route has an active turn; retry after it finishes")
        if entry.origin is None:
            raise BindingError("peer_unavailable", "The native WeChat origin is unavailable")
        # A user-requested unbind creates an independent native route, leaving the Main intact.
        replacement = self.store.get_or_create_session(entry.origin, force_new=True)
        self.runner._evict_cached_agent(entry.session_key)
        self.runner._clear_conversation_scope(entry.session_key, reason="explicit_conversation_unbind")
        return {"changed": True, "binding": self._status(replacement, db)}

    def execute(self, params):
        try:
            if not isinstance(params, dict) or set(params) - {"profile", "action", "conversation_ref", "caller_locator", "limit"}:
                raise BindingError("invalid_arguments", "Invalid binding operation")
            entry, db = self._peer(params.get("profile"))
            action = params.get("action")
            def bind():
                ref = params["conversation_ref"] if "conversation_ref" in params else self._current(db, params)["conversation_ref"]
                return self._bind(entry, db, ref)

            handlers = {
                "status": lambda: {"binding": self._status(entry, db)},
                "current": lambda: {"conversation": self._current(db, params)},
                "list": lambda: {"conversations": self._list(db, params.get("limit", 20))},
                "bind": bind, "unbind": lambda: self._unbind(entry, db),
            }
            if action not in handlers:
                raise BindingError("invalid_action", "Use current, list, status, bind or unbind")
            result = handlers[action]()
            return {"ok": True, "action": action, "profile": params["profile"], **result}
        except BindingError as exc:
            return {"ok": False, "error": {"code": exc.code, "message": str(exc)}}


def conversation_binding_verb(runner, loop):
    control = ConversationBindingControl(runner)

    async def execute(params):
        return control.execute(params)

    def handler(params):
        future = asyncio.run_coroutine_threadsafe(execute(params), loop)
        return future.result(timeout=20)

    return handler
