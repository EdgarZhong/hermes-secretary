"""Idle-only Web submit over the existing native prompt/admission owner."""
from contextlib import contextmanager
from contextvars import ContextVar

from .inflight_output import _set_session_running
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method
_idle_submit_mode = ContextVar("hermes_idle_only_submit", default=False)
_idle_submission_id = ContextVar("hermes_idle_submission_id", default=None)
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
def _idle_submit_scope(submission_id=None):
    token = _idle_submit_mode.set(True)
    identity_token = _idle_submission_id.set(submission_id)
    try:
        yield
    finally:
        _idle_submission_id.reset(identity_token)
        _idle_submit_mode.reset(token)


def _idle_submit_metadata():
    identity = _idle_submission_id.get() if _idle_submit_requested() else None
    return {"client_submission_id": identity} if identity else None


def _idle_submission_identity_error(rid, identity, *, required=False):
    if identity is None and not required:
        return None
    if not isinstance(identity, str) or not identity.strip() or len(identity) > 128:
        return _err(rid, 4000, "client_submission_id must be a nonblank string of at most 128 characters")
    return None


def _idle_submission_receipt(session, identity):
    """Read an acceptance fact in this Profile/Conversation, including retired row copies."""
    if not identity:
        return None
    with _session_db(session) as db:
        if db is None:
            return None
        owner = _submit_row_target_key(session)
        row = db._read_one(
            "SELECT m.id,m.session_id,m.role,m.content,m.timestamp,m.message_uid,m.display_kind,m.display_metadata "
            "FROM messages m JOIN secretary_session_bindings b ON b.session_id=m.session_id "
            "WHERE b.conversation_ref=(SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?) "
            "AND m.role='user' AND json_valid(m.display_metadata) "
            "AND json_extract(m.display_metadata,'$.client_submission_id')=? "
            "ORDER BY m.id DESC LIMIT 1", (owner, identity))
        if row is None or not row["message_uid"]:
            return None
        message = {key: row[key] for key in ("role", "content", "timestamp", "message_uid")}
        message["content"] = db._decode_content(message["content"])
        message["row_id"] = row["id"]
        if row["display_kind"]:
            message["display_kind"] = row["display_kind"]
        if row["display_metadata"]:
            message["display_metadata"] = json.loads(row["display_metadata"])
        return {"stored_session_id": owner, "message": message, "client_submission_id": identity}


def _idle_submission_reuse_error(rid, session):
    if _idle_submit_requested() and _idle_submission_receipt(session, _idle_submission_id.get()):
        return _err(rid, 4031, "submission already accepted", {"accepted": True, "reason": "already_submitted"})
    return None


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
    identity = (message.get("display_metadata") or {}).get("client_submission_id")
    if identity:
        payload["client_submission_id"] = identity
    MessageUserCommittedPayload.model_validate(payload)
    return payload


def _submit_persist_with_receipt(rid, sid, session, text, display_kind, fields, image_paths=None):
    """Capture the native committed row before any worker can consume its staging dict."""
    previous = session.get("_submit_user_row")
    error = _persist_session_row_for_submit(
        rid, session, text, display_kind, **({"image_paths": image_paths} if image_paths else {}))
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
            if isinstance(turn := session.get("inflight_turn"), dict):
                turn["_committed_user_display_uid"] = payload["message"]["message_uid"]
    except Exception:
        logger.debug("idle submit committed-user display unavailable", exc_info=True)
    return None


@method("prompt.submit_idle")
def _(rid, params):
    if (error := _idle_submission_identity_error(rid, params.get("client_submission_id"))) is not None:
        return error
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
    with _idle_submit_scope(params.get("client_submission_id")):
        return _native_prompt_submit_handler(rid, params)


@method("prompt.submission_status")
def _submission_status(rid, params):
    if (error := _idle_submission_identity_error(rid, params.get("client_submission_id"), required=True)) is not None:
        return error
    session, error = _sess_nowait(params, rid)
    if error:
        return error
    if params.get("profile") is not None:
        requested = _profile_home(params["profile"])
        actual = session.get("profile_home") or _hermes_home
        if Path(requested or _hermes_home).resolve() != Path(actual).resolve():
            return _err(rid, 4003, "runtime profile mismatch")
    receipt = _idle_submission_receipt(session, params["client_submission_id"])
    return _ok(rid, {"status": "accepted", "accepted_user": receipt} if receipt else {"status": "unknown"})


def register(server):
    bind_module(globals(), server, skip=("_",))
