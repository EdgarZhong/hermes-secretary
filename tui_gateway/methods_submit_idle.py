"""Idle-only Web submit over the existing native prompt/admission owner."""
from contextlib import contextmanager
from contextvars import ContextVar

from .inflight_output import _set_session_running
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method
_idle_submit_mode = ContextVar("hermes_idle_only_submit", default=False)
_idle_submit_retry = object()


def _idle_submit_requested():
    return _idle_submit_mode.get()


def _submit_request_images(params):
    """Capture once on the request thread; legacy None retains native staging semantics."""
    return list(params.get("image_paths", [])) if _idle_submit_requested() else None


def _idle_submit_validate_images(rid, paths):
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        return None, _err(rid, 4000, "image_paths must be a list of strings")
    from cli import _IMAGE_EXTENSIONS, _resolve_attachment_path
    canonical = []
    for raw in paths:
        if not raw.strip():
            return None, _err(rid, 4015, "path required")
        try:
            path = _resolve_attachment_path(raw)
            if path is None:
                return None, _err(rid, 4016, f"image not found: {raw}")
            if path.suffix.lower() not in _IMAGE_EXTENSIONS:
                return None, _err(rid, 4016, f"unsupported image: {path.name}")
            with path.open("rb") as image:
                image.read(1)
        except (OSError, ValueError) as exc:
            return None, _err(rid, 5027, str(exc))
        canonical.append(str(path))
    return canonical, None


@contextmanager
def _idle_submit_scope():
    token = _idle_submit_mode.set(True)
    try:
        yield
    finally:
        _idle_submit_mode.reset(token)


def _idle_submit_busy(rid):
    return _err(rid, 4009, "session busy", {"accepted": False, "reason": "session_busy"})


def _idle_submit_claim_error(rid, session):
    """Called only inside native admission/history_lock; no independent admission state."""
    if not session.get("running"):
        return None
    if _idle_submit_requested():
        return _idle_submit_busy(rid)
    if session.get("_idle_only_running_claim"):
        return _idle_submit_retry
    return None


def _submit_client_surface(session, params, *, claimed=False):
    # Legacy keeps its original preflight write; Web writes only after it owns the native claim.
    if _idle_submit_requested() != claimed:
        return
    session["client_surface"] = params.get("surface") if params.get("surface") in _CLIENT_SURFACES else ""
    voice_context = params.get("voice_context")
    session["voice_live_context"] = (
        voice_context[:6000] if session["client_surface"] == "voice-live" and isinstance(voice_context, str) else "")
    session["voice_turn"] = params.get("voice_turn") is True


def _submit_commit_running_claim(session, text, params, hosted_task, display_kind):
    """Commit native running/inflight and its source in the one admission critical section."""
    _set_session_running(session, True)
    session["_turn_cancel_requested"] = False
    session["last_active"] = time.time()
    if hosted_task is not None:
        session["_hosted_room_task"] = dict(hosted_task)
    _start_inflight_turn(session, text, display_kind=display_kind)
    if _idle_submit_requested():
        session["_idle_only_running_claim"] = True
        _submit_client_surface(session, params, claimed=True)
    else:
        session.pop("_idle_only_running_claim", None)


def _submit_claim_with_busy_policy(
    rid, sid, session, text, params, has_truncation, requested_rebind_ids, hosted_task, display_kind,
    *, internal_hosted_submit=False, turn_author=None, transport=None,
):
    """Native busy behavior, with an idle-only branch and new/legacy claim retry."""
    # New requests have one authoritative decision, inside native admission.
    if _idle_submit_requested():
        return _lock_in_submit_turn(
            rid, sid, session, text, params, has_truncation, requested_rebind_ids, hosted_task, display_kind)
    while True:
        with session["history_lock"]:
            busy = bool(session.get("running"))
            busy_transport = transport or session.get("transport")
        if busy:
            if internal_hosted_submit:
                return _err(rid, 4091, "hosted room member session is busy"), {}
            if has_truncation:
                return _err(rid, 4009, "session busy"), {}
            response = _handle_busy_submit(
                rid, sid, session, text, busy_transport, queued=bool(params.get("queued")),
                turn_author=turn_author, display_kind=display_kind)
            if response is not None:
                return response, {}
            continue
        error, fields = _lock_in_submit_turn(
            rid, sid, session, text, params, has_truncation, requested_rebind_ids, hosted_task, display_kind)
        if error is not _idle_submit_retry:
            return error, fields


def _idle_committed_user(session, staged):
    """Read only the freshly staged row from its recorded profile/store and owner."""
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from tui_gateway.contracts.events import MessageUserCommittedPayload

    if not isinstance(staged, dict) or not staged.get(_DB_PERSISTED_MARKER):
        return None
    row_id, uid = staged.get("_row_id"), staged.get("message_uid")
    owner, path = staged.get("_submit_row_session_id"), staged.get("_submit_row_db_path")
    if (not isinstance(row_id, int) or isinstance(row_id, bool) or row_id <= 0
            or not isinstance(uid, str) or not uid or not owner or not path):
        return None
    with _session_db(session) as db:
        if db is None or Path(db.db_path).resolve() != Path(path).resolve():
            return None
        row = db._read_one(
            "SELECT id, role, content, timestamp, message_uid, display_kind, display_metadata "
            "FROM messages WHERE id = ? AND session_id = ? AND message_uid = ? AND role = 'user' AND active = 1",
            (row_id, owner, uid))
        if row is None:
            return None
        message = {key: row[key] for key in ("role", "content", "timestamp", "message_uid")}
        message["row_id"] = row["id"]
        if row["display_kind"] is not None:
            message["display_kind"] = row["display_kind"]
        if row["display_metadata"] is not None:
            message["display_metadata"] = json.loads(row["display_metadata"])
    payload = {"stored_session_id": owner, "message": message}
    MessageUserCommittedPayload.model_validate(payload)
    return payload


def _submit_persist_with_receipt(rid, sid, session, text, display_kind, fields):
    """Capture the native committed row before any worker can consume its staging dict."""
    previous = session.get("_submit_user_row")
    error = _persist_session_row_for_submit(rid, session, text, display_kind)
    if error is not None:
        return error
    staged = session.get("_submit_user_row") or {}
    if isinstance(staged.get("_row_id"), int):
        fields["user_row_id"] = staged["_row_id"]
    if not _idle_submit_requested() or staged is previous:
        return None
    try:
        payload = _idle_committed_user(session, staged)
        if payload is not None:
            fields["accepted_user"] = payload
            _emit("message.user_committed", sid, payload)
    except Exception:
        logger.debug("idle submit committed-user display unavailable", exc_info=True)
    return None


@method("prompt.submit_idle")
def _(rid, params):
    session, error = _sess_nowait(params, rid)
    if error:
        return error
    if params.get("profile") is not None:
        requested = _profile_home(params["profile"])
        actual = session.get("profile_home") or _hermes_home
        if Path(requested or _hermes_home).resolve() != Path(actual).resolve():
            return _err(rid, 4003, "runtime profile mismatch")
    paths, error = _idle_submit_validate_images(rid, params.get("image_paths", []))
    if error:
        return error
    params = {**params, "image_paths": paths}
    # This alias is the actual handler rebound by methods_prompt.register, not a raw module function.
    with _idle_submit_scope():
        return _native_prompt_submit_handler(rid, params)


def register(server):
    bind_module(globals(), server, skip=("_",))
