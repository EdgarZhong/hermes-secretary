"""The removed old Review slash cannot reach its former live callback."""

from hermes_cli.commands import resolve_command
from tui_gateway import server


def test_refine_is_no_longer_a_product_command():
    assert resolve_command("refine") is None
    assert server._live_slash_command_output("gone", None, "refine", "focus") is None
    result = server._methods["command.dispatch"]("test", {"name": "refine", "arg": "focus"})
    assert result["error"]["code"] == 4018
