"""Read-only native runtime roster (methods_session sibling, shared by every client)."""
from .method_ctx import HandlerRegistry, bind_module

_registry = HandlerRegistry()
method = _registry.method


@method("session.active_list")
def _(rid, params: dict) -> dict:
    """Live TUI sessions in this process (not a DB browser)."""
    snapshot, err = _snapshot_sessions(rid)
    if err:
        return err
    current = str(params.get("current_session_id") or "")
    # ``_finalized`` sessions linger until the reaper pops them (they inflated the footer). Do NOT filter on
    # the WS-detached sentinel: detached is attachable until grace-reap, and ``hermes --tui`` rides stdio.
    # Keep insertion order (focused must not jump).
    # ``profile`` was historically accepted by ProfileParams but never filtered this global roster.
    rows = []
    for sid, session in snapshot:
        if session.get("_finalized") or session.get("_closing"):
            continue
        rows.append(_session_live_item(sid, session, current))
    return _ok(rid, {"sessions": rows})


def register(server) -> None:
    bind_module(globals(), server, skip=("_",))
