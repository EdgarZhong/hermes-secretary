"""Attachment staging: image sniffing, size caps, per-session attachment dirs, path resolution.

Bodies are rebound onto server.py's globals at install time (see
method_ctx.bind_module), so they reference server.py globals bare.
"""

from __future__ import annotations

import re as _re

from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()


_ATTACH_BYTES_MAX_BYTES = 25 * 1024 * 1024
_PDF_ATTACH_MAX_BYTES = 50 * 1024 * 1024
_PDF_ATTACH_MAX_PAGES = 25
_FILE_ATTACH_CHUNK_BYTES = 4 * 1024 * 1024
_FILE_ATTACH_TOTAL_BYTES = 500_000_000

# Leading magic bytes -> file extension, for filename-less uploads.
_IMAGE_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", ".png"), (b"\xff\xd8\xff", ".jpg"), (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"), (b"BM", ".bmp"))

# Context-ref values containing any of these must be quoted (desktop formatRefValue parity).
_ATTACHMENT_REF_NEEDS_QUOTING_RE = _re.compile(r"""[\s()\[\]{}<>"'`]""")
del _re  # bodies are rebound onto server globals: import inside functions only


def _b64_payload(raw: str, data_url_re: str, flags: int) -> bytes:
    """Strip an optional ``data:...;base64,`` wrapper and all whitespace, then strictly decode."""
    import base64 as _base64
    import re as _re
    cleaned = (raw or "").strip()
    if m := _re.match(data_url_re, cleaned, flags):
        cleaned = m.group(1)
    return _base64.b64decode(_re.sub(r"\s+", "", cleaned), validate=True)


def _decode_attach_base64(raw: str, *, mime_prefix: str) -> bytes | None:
    """Decode a (``data:<mime_prefix>...;base64,``-wrapped) payload; None when invalid."""
    import re as _re
    try:
        return _b64_payload(
            raw, rf"^data:{_re.escape(mime_prefix)}[a-zA-Z0-9.+-]*;base64,(.*)$", _re.DOTALL)
    except Exception:
        return None


def _decode_attach_payload(
    rid, raw_b64: str, *, mime_prefix: str, max_bytes: int, label: str, empty_msg: str):
    """``(bytes, None)`` or ``(None, error)``: 4017 on bad/empty base64, 4018 over *max_bytes*."""
    data = _decode_attach_base64(raw_b64, mime_prefix=mime_prefix)
    if data is None:
        return None, _err(rid, 4017, "data is not valid base64")
    if not data:
        return None, _err(rid, 4017, empty_msg)
    if len(data) > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return None, _err(rid, 4018, f"{label} too large ({len(data)} bytes; cap is {mb} MB)")
    return data, None


def _sniff_image_ext(img_bytes: bytes, filename: str = "") -> str:
    """Extension from the filename hint, else magic bytes (WebP: RIFF container), else ``.png``."""
    if filename and (suffix := Path(filename).suffix.lower()):
        return suffix
    head = img_bytes[:16]
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    return next((ext for sig, ext in _IMAGE_MAGIC if head.startswith(sig)), ".png")


def _allowed_image_extensions() -> frozenset[str]:
    try:
        from cli import _IMAGE_EXTENSIONS
        return frozenset(_IMAGE_EXTENSIONS)
    except Exception:
        return frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"})


def _session_home_dir(session: dict, name: str) -> Path:
    """``<session home>/<name>``, anchored on the session's stored ``profile_home``: attach
    RPCs run BEFORE ``prompt.submit`` installs the profile HERMES_HOME override, while
    the sandbox mounts and the vision host-read allowlist resolve the *session profile's*
    dirs at run time — writing anywhere else means the agent can never see the file.

    ``attachments`` instead follows the session workspace when the profile's config opts
    in via ``attachments.storage: workspace`` (#110662): staging then lands inside the
    allowed ref root, so the ``@file:`` ref stays workspace-relative."""
    profile_home = session.get("profile_home")
    if name == "attachments" and _profile_attachments_storage(profile_home) == "workspace":
        if workspace := _session_attachments_workspace(session):
            return workspace / ".hermes" / "attachments"
    return (Path(profile_home) if profile_home else _hermes_home) / name


def _profile_attachments_storage(profile_home) -> str:
    """The session profile's ``attachments.storage`` ("" unless it opts into "workspace").

    Read from THAT profile's config.yaml — ``file.attach`` runs before ``prompt.submit``
    installs the profile scope, so the process config still belongs to the launch profile
    (same reason as ``_profile_configured_cwd``)."""
    import contextlib as _contextlib
    home = Path(profile_home) if profile_home else _hermes_home
    with _contextlib.suppress(Exception):
        from hermes_cli.config_effective import load_user_config_effective
        cfg_path = home / "config.yaml"
        if cfg_path.exists():
            attachments_cfg = load_user_config_effective(cfg_path).get("attachments")
            if isinstance(attachments_cfg, dict):
                return str(attachments_cfg.get("storage") or "").strip().lower()
    return ""


def _session_attachments_workspace(session: dict) -> Path | None:
    """The session workspace when ``attachments.storage: workspace`` can actually write to it.

    Only a workspace on THIS host can hold gateway-staged files: an ssh-profile cwd lives
    on the remote execution host and a cwd that doesn't exist locally can't be vouched
    for, so both keep the bind-mounted ``<profile home>/attachments`` that container and
    remote backends receive (#76577)."""
    import contextlib as _contextlib
    if _cwd_is_remote(session.get("profile_home")):
        return None
    with _contextlib.suppress(Exception):
        workspace = Path(_session_cwd(session)).resolve()
        if workspace.is_dir():
            return workspace
    return None


def _session_images_dir(session: dict) -> Path:
    return _session_home_dir(session, "images")


def _queue_attached_image(session: dict, img_bytes: bytes, ext: str, *, prefix: str) -> Path:
    """Write image bytes into the session images dir and queue them for the next submit."""
    img_dir = _session_images_dir(session)
    img_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    counter = session.get("image_counter", 0) + 1
    while True:
        candidate = img_dir / f"{prefix}_{ts}_{counter}{ext}"
        try:
            upload = candidate.open("xb")
        except FileExistsError:
            counter += 1
        else:
            break
    session["image_counter"] = counter
    try:
        with upload:
            upload.write(img_bytes)
    except Exception:
        candidate.unlink(missing_ok=True)
        raise
    session.setdefault("attached_images", []).append(str(candidate))
    return candidate


def _format_ref_value(value: str) -> str:
    """Quote a value with whitespace/brackets/quotes so the ``@file:`` ref round-trips."""
    if not value or not _ATTACHMENT_REF_NEEDS_QUOTING_RE.search(value):
        return value
    for q in ("`", '"', "'"):
        if q not in value:
            return f"{q}{value}{q}"
    return value


def _attachment_ref_path(session: dict, target: Path) -> str:
    """Workspace-relative path for an attachment, or the absolute path if outside."""
    workspace = Path(_session_cwd(session)).resolve()
    try:
        return str(target.resolve().relative_to(workspace)).replace(os.sep, "/")
    except ValueError:
        return str(target.resolve())


def _sanitize_attachment_name(name: str) -> str:
    import re as _re
    candidate = _re.sub(r"[\x00-\x1f]+", "_", Path(str(name or "").strip()).name)
    return candidate.strip().strip(".") or "attachment"


def _attachment_targets(root: Path, filename: str):
    """The shared native exclusive-allocation sequence, including duplicate names."""
    filename = _sanitize_attachment_name(filename)
    yield root / filename
    stem, suffix = Path(filename).stem or "attachment", Path(filename).suffix
    counter = 2
    while True:
        yield root / f"{stem}-{counter}{suffix}"
        counter += 1


def _file_attach_result(session: dict, target: Path, uploaded: bool) -> dict:
    ref_path = _attachment_ref_path(session, target)
    return {"attached": True, "name": target.name, "path": str(target),
            "ref_path": ref_path, "ref_text": f"@file:{_format_ref_value(ref_path)}",
            "uploaded": uploaded}


def _file_attachment_metadata(session: dict, raw_path: str) -> dict:
    """Read a real size without staging, with the same session/profile path ownership."""
    if not raw_path:
        raise ValueError("path is required for attachment metadata")
    workspace = Path(_session_cwd(session)).resolve()
    target = Path(raw_path).expanduser()
    target = (target if target.is_absolute() else workspace / target).resolve()
    roots = [_session_home_dir(session, name).resolve() for name in ("attachments", "images")]
    # A remote cwd is not a host-local path. Never stat a same-named host workspace.
    if not _cwd_is_remote(session.get("profile_home")):
        roots.append(workspace)
    if not any(target == root or target.is_relative_to(root) for root in roots):
        raise ValueError("Attachment size unavailable outside the session's readable roots")
    if not target.is_file():
        raise ValueError("Attachment file is unavailable")
    result = _file_attach_result(session, target, False)
    result.update(attached=False, size_bytes=target.stat().st_size)
    return result


def _file_upload_progress(upload_id: str, state: dict) -> dict:
    return {"attached": False, "name": state["name"], "path": "", "ref_path": "",
            "ref_text": "", "uploaded": False, "upload_id": upload_id,
            "received_bytes": state["offset"]}


def _file_attachment_chunk(session: dict, params: dict) -> dict:
    """Bounded, ordered upload under the native session lock; last-ACK retries are idempotent."""
    import uuid
    upload_id = str(params.get("upload_id") or "")
    try:
        if str(uuid.UUID(upload_id)) != upload_id:
            raise ValueError
    except ValueError as exc:
        raise ValueError("upload_id must be a canonical UUID") from exc
    with session["history_lock"]:
        uploads = session.setdefault("file_uploads", {})
        state = uploads.get(upload_id)
        if params.get("abort_upload"):
            if state and "result" not in state:
                state["temporary"].unlink(missing_ok=True)
                uploads.pop(upload_id, None)
            return _file_upload_progress(upload_id, state or {"name": "", "offset": 0})
        return _append_file_attachment_chunk(session, params, uploads, state, upload_id)


def _append_file_attachment_chunk(session, params, uploads, state, upload_id):
    import hashlib
    import re as _re
    import tempfile
    offset, total = params.get("offset"), params.get("total_bytes")
    if (type(offset) is not int or offset < 0 or type(total) is not int
            or not 0 < total <= _FILE_ATTACH_TOTAL_BYTES):
        raise ValueError("Invalid attachment offset or total_bytes (maximum 500000000)")
    raw = str(params.get("data_url") or "")
    if len(raw) > ((_FILE_ATTACH_CHUNK_BYTES + 2) // 3) * 4 + 1024:
        raise ValueError("Attachment chunk encoding exceeds 4194304 bytes")
    # All ordinary media types, preserving the legacy image/PDF-specific decoder caps.
    try:
        payload = _b64_payload(raw, r"^data:[^;,]*(?:;[^;,=]+=[^;,]+)*;base64,(.*)$", _re.DOTALL | _re.I)
    except Exception as exc:
        raise ValueError("invalid data_url payload") from exc
    if not payload or len(payload) > _FILE_ATTACH_CHUNK_BYTES or offset + len(payload) > total:
        raise ValueError("Invalid attachment chunk length (maximum 4194304)")
    name = _sanitize_attachment_name(params.get("name") or "attachment")
    digest = hashlib.sha256(payload).hexdigest()
    if state:
        if state["total"] != total or state["name"] != name:
            raise ValueError("Upload metadata changed")
        if state.get("last_offset") == offset and state.get("last_digest") == digest:
            return state.get("result") or _file_upload_progress(upload_id, state)
        if state["offset"] != offset or "result" in state:
            raise ValueError("Upload offset does not match received bytes")
    else:
        if offset != 0:
            raise ValueError("Unknown upload; first offset must be zero")
        root = _session_home_dir(session, "attachments")
        root.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".file-upload-", dir=root)
        os.close(fd)
        state = {"temporary": Path(temporary), "name": name, "offset": 0, "total": total}
        uploads[upload_id] = state
    temporary = state["temporary"]
    try:
        with temporary.open("r+b") as stream:
            stream.seek(offset)
            stream.write(payload)
            stream.flush()
        state.update(offset=offset + len(payload), last_offset=offset, last_digest=digest)
        if state["offset"] == total:
            # Hard-link publishes complete bytes atomically with exclusive native name allocation.
            for target in _attachment_targets(temporary.parent, name):
                try:
                    os.link(temporary, target)
                except FileExistsError:
                    continue
                break
            temporary.unlink()
            result = _file_attach_result(session, target.resolve(), True)
            result.update(upload_id=upload_id, received_bytes=total, size_bytes=total)
            state["result"] = result
    except Exception:
        temporary.unlink(missing_ok=True)
        uploads.pop(upload_id, None)
        raise
    return state.get("result") or _file_upload_progress(upload_id, state)


def _stage_session_file_attachment(
    session: dict, *, raw_path: str, data_url: str, name: str) -> tuple[Path, bool]:
    """Make a desktop file attachment available to the gateway agent: ``(stored_path, uploaded)``.
    Inside the workspace -> as-is; gateway-visible but outside -> copied into ``attachments/``
    (bind-mounted into container backends so ``@file:`` resolves in the sandbox); not on the
    gateway -> ``data_url`` bytes decoded into ``attachments/``."""
    workspace = Path(_session_cwd(session)).resolve()
    resolved = None
    if raw_path:
        try:
            from cli import _detect_file_drop, _resolve_attachment_path, _split_path_input
        except Exception:
            _detect_file_drop = None
        if _detect_file_drop is not None:
            dropped = _detect_file_drop(raw_path)
            if dropped:
                resolved = Path(dropped["path"]).resolve()
            else:
                path_token, _remainder = _split_path_input(raw_path)
                found = _resolve_attachment_path(path_token)
                resolved = Path(found).resolve() if found is not None else None
    if resolved is not None:
        try:
            resolved.relative_to(workspace)
            return resolved, False
        except ValueError:
            payload = resolved.read_bytes()
            filename = resolved.name
    else:
        if not data_url:
            raise ValueError("file not found on gateway and no data_url provided")
        # Any media type (unlike the image-specific decoder); bare base64 also accepted.
        import binascii as _binascii
        import re as _re
        try:
            payload = _b64_payload(
                data_url, r"^data:[^;,]*(?:;[^;,=]+=[^;,]+)*;base64,(.*)$", _re.DOTALL | _re.I)
        except (ValueError, _binascii.Error) as exc:
            raise ValueError("invalid data_url payload") from exc
        filename = _sanitize_attachment_name(name or Path(str(raw_path or "")).name)
    root = _session_home_dir(session, "attachments")
    root.mkdir(parents=True, exist_ok=True)
    filename = _sanitize_attachment_name(filename)
    for target in _attachment_targets(root, filename):
        try:
            upload = target.open("xb")
        except FileExistsError:
            continue
        else:
            break
    try:
        with upload:
            upload.write(payload)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target.resolve(), True


def register(server) -> None:
    """Publish this module's helpers + handlers onto ``server``, rebound to its globals."""
    bind_module(globals(), server, skip=("_",))
