"""Gateway recovery envelopes stay model-only across both public history readers."""
from copy import deepcopy

import pytest

from hermes_cli.web_routers.sessions import _project_for_display
from tui_gateway.server import _history_to_messages


PREFIX = "<timestamp>2026-11-10T09:00:00+08:00</timestamp>\n"
WRAPPED = '<gateway-message from="微信">\nactual message\n</gateway-message>'
RECOVERY = "[System note: A new message has arrived. The conversation history contains pending tool outputs from an interrupted turn.]\n\n"


def row(content=PREFIX + WRAPPED, api=PREFIX + RECOVERY + WRAPPED):
    return {"id": 1, "row_id": 1, "role": "user", "message_uid": "source-uid", "content": content,
            "api_content": api, "display_metadata": {"gateway_input_owner": "native-owner",
                "turn_source": {"message_uid": "source-uid", "turn_id": "native-turn"}}}


def test_recovery_wrapper_has_one_clean_display_without_changing_source():
    source = row()
    original = deepcopy(source)
    public = _project_for_display([source])[0]
    compact = _history_to_messages([source])[0]
    assert public.get("display_content") == PREFIX + "actual message"
    assert compact["text"] == PREFIX + "actual message"
    assert source == original
    assert public["content"] == original["content"]
    assert public["api_content"] == original["api_content"]


@pytest.mark.parametrize("updates", [
    pytest.param({"display_metadata": None}, id="ordinary"),
    pytest.param({"role": "assistant"}, id="assistant"),
    pytest.param({"content": "```xml\n" + WRAPPED + "\n```"}, id="quoted"),
    pytest.param({"api_content": None}, id="missing_api"),
    pytest.param({"message_uid": "another-message"}, id="mismatched_uid"),
    pytest.param({"api_content": PREFIX + RECOVERY + '<gateway-message from="微信">\n' + WRAPPED + '\n</gateway-message>'}, id="nested_authored"),
    pytest.param({"content": PREFIX + WRAPPED.removesuffix("</gateway-message>")}, id="incomplete"),
])
def test_unproven_or_authored_gateway_xml_is_not_removed(updates):
    source = row()
    source.update(updates)
    public = _project_for_display([source])[0]
    assert public.get("display_content", public["content"]) == source["content"]
