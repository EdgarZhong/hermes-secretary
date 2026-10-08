"""Bind Secretary background/request policy reads to the owning state.db profile."""

from contextlib import contextmanager
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@contextmanager
def owning_db_scope(db):
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override

    path = getattr(db, "db_path", None)
    if path is None:
        raise ValueError("Secretary runtime requires an owning state.db")
    token = set_hermes_home_override(Path(path).parent)
    try:
        yield
    finally:
        reset_hermes_home_override(token)


def settings_for_db(db):
    from secretary.noting_policy import disabled_noting_settings, resolve_noting_settings

    try:
        with owning_db_scope(db):
            return resolve_noting_settings()
    except Exception:
        logger.debug("Owning-profile Noting policy unavailable", exc_info=True)
        return disabled_noting_settings()
