"""Optional surface observation attached to the existing native redirect text."""

import logging

logger = logging.getLogger(__name__)


class ObservedRedirect(str):
    def __new__(cls, text, observers=()):
        value = super().__new__(cls, text)
        value.observers = tuple(observers)
        return value


def merge_redirect(existing, cleaned, observer=None):
    text = f"{existing}\n\n[Additional user correction]\n{cleaned}" if existing else cleaned
    observers = getattr(existing, "observers", ())
    if observer is not None:
        observers += (observer,)
    return ObservedRedirect(text, observers) if observers else text


def redirect_applied(text, visible):
    """Observe the committed checkpoint once; coalesced corrections share one partial."""
    for index, observer in enumerate(getattr(text, "observers", ())):
        try:
            observer(visible if index == 0 else "")
        except Exception:
            logger.debug("Redirect presentation observer failed", exc_info=True)
