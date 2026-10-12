"""Notify an already-loaded read projection after a native config write succeeds."""

import logging
import sys


def atomic_roundtrip_yaml_save(config_path, data, **kwargs):
    # Keep the canonical writer (and its patch seam) as the sole persistence owner.
    from utils import atomic_roundtrip_yaml_save as save

    result = save(config_path, data, **kwargs)
    observer = sys.modules.get("secretary.web_events")
    if observer is not None:
        try:
            observer.config_changed(config_path)
        except Exception:
            logging.getLogger(__name__).debug("Config read-projection notification failed", exc_info=True)
    return result
