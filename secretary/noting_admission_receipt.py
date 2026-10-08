"""Observation of native compression admission; owns no lock, gate, or scheduling."""


def observe_native_admission(agent, fence, receipt=None):
    """Called only after the native snapshot/rotation/cooldown safety checks."""
    if fence is not None and fence.is_cancelled:
        return
    stop = getattr(agent, "_hard_interrupt_requested", None)
    if stop is not None and stop.is_set() is True:
        return
    if fence is not None:
        fence._secretary_native_admitted = True
    if receipt is not None:
        receipt.set()


def dispatch_codex_compaction(agent, session, fence, receipt, snapshot_is_current):
    """Keep ordinary dispatch unchanged; observe the transport's actual successful RPC ACK."""
    if receipt is None:
        return session.compact_thread()
    if snapshot_is_current is not None and not snapshot_is_current():
        raise RuntimeError("Native snapshot stale before Codex compaction dispatch")
    return session.compact_thread(on_admitted=lambda: observe_native_admission(agent, fence, receipt))
