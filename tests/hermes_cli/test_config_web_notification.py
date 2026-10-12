"""The native config commit precedes optional Web invalidation, with unchanged failures."""

import pytest

from hermes_cli.config import atomic_config_replace
from secretary import web_events


def test_committed_config_is_visible_to_owner_qualified_observer(tmp_path):
    from hermes_yaml import safe_load

    path = tmp_path / "profile" / "config.yaml"
    path.parent.mkdir()
    observed = []

    def observer(home, ref, reason):
        observed.append((home, ref, reason, safe_load(path.read_text())))

    web_events.subscribe("config-integration-test", observer)
    try:
        atomic_config_replace(path, {"secretary": {"enabled": False}})
    finally:
        web_events.unsubscribe("config-integration-test")
    assert observed == [(path.parent.resolve(), None, "global_changed", {"secretary": {"enabled": False}})]


def test_observer_failure_does_not_change_native_write_result(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"

    def fail(_path):
        raise RuntimeError("observer unavailable")

    monkeypatch.setattr(web_events, "config_changed", fail)
    assert atomic_config_replace(path, {"model": "example"}) is None
    assert "example" in path.read_text()


def test_native_write_failure_never_publishes_invalidation(tmp_path, monkeypatch):
    import utils

    observed = []

    def fail(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(utils, "atomic_roundtrip_yaml_save", fail)
    monkeypatch.setattr(web_events, "config_changed", observed.append)
    with pytest.raises(OSError, match="disk unavailable"):
        atomic_config_replace(tmp_path / "config.yaml", {"model": "example"})
    assert observed == []
