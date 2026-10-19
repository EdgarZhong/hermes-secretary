"""Profile identity preserves registered names through externally stored homes."""

from pathlib import Path

import pytest

from hermes_cli.profiles import get_active_profile_name
from hermes_constants import reset_hermes_home_override, set_hermes_home_override


@pytest.mark.require_symlinks
@pytest.mark.parametrize("physical", [False, True])
def test_symlink_identity_preserves_profile_name(tmp_path, monkeypatch, physical):
    root = tmp_path / ".hermes"
    external = tmp_path / "homes" / "Alex"
    external.mkdir(parents=True)
    (external / "config.yaml").touch()
    alias = root / "profiles" / "alex"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(alias))
    token = set_hermes_home_override(external if physical else alias)
    try:
        assert get_active_profile_name() == "alex"
        (alias.parent / "second").symlink_to(external, target_is_directory=True)
        assert get_active_profile_name() == ("custom" if physical else "alex")
    finally:
        reset_hermes_home_override(token)


def test_symlink_identity_keeps_non_home_custom_fallback(tmp_path, monkeypatch):
    home = tmp_path / ".hermes" / "profiles" / "coder"
    (home / "skills").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home / "skills"))
    assert get_active_profile_name() == "custom"
