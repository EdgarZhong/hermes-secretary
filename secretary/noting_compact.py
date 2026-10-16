"""Parent-only adapter to Hermes native compaction requests; no Noting tool exists here."""


def request_parent_compaction(parent, *, threshold_tokens=None):
    """Reuse the native lock/fence/cooldown path, never await a Noting child."""
    request = getattr(parent, "request_context_compaction", None)
    if not callable(request):
        raise RuntimeError("The parent has no native compaction request interface")
    return request(relevant_threshold_tokens=threshold_tokens, wait_seconds=5.0)
