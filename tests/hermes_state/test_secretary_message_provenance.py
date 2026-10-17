"""History provenance and digest helpers; durable role is not source truth."""

from hermes_state_message_provenance import (
    ASSISTANT, FRAMEWORK, HUMAN, NOTEBOOK, SYSTEM, TOOL,
    argument_digest, content_digest, message_provenance, tool_call_digests,
)


def test_role_and_metadata_drive_coarse_provenance():
    assert message_provenance({"role": "user", "content": "hello"}) == (HUMAN, "human")
    assert message_provenance({"role": "user", "content": "steer", "display_kind": "steer"}) == (HUMAN, "human")
    assert message_provenance({"role": "assistant", "content": ""}) == (ASSISTANT, "assistant")
    assert message_provenance({"role": "tool", "tool_name": "terminal"}) == (TOOL, "tool:terminal")
    assert message_provenance({"role": "system", "content": "event"}) == (SYSTEM, "system")
    assert message_provenance({
        "role": "user", "display_kind": "process_complete",
        "display_metadata": {"display_text": "NOTING RESULT\nCURRENT NOTEBOOK SNAPSHOT", "noting_run_output": True},
    }) == (NOTEBOOK, "notebook:noting_result")
    assert message_provenance({
        "role": "user", "display_kind": "process_complete",
        "display_metadata": {"display_text": "reminder", "reminder_ids": ["r1"]},
    }) == (FRAMEWORK, "framework:process_complete")
    assert message_provenance({
        "role": "user", "display_kind": "process_complete",
        "display_metadata": {"display_text": "framework", "origin": "framework", "producer": "external_unavailability"},
    }) == (FRAMEWORK, "framework:external_unavailability")


def test_wrappers_and_unknown_display_kinds_fail_closed():
    assert message_provenance({"role": "user", "content": "<instant-reminder>\ndue"}) == (
        FRAMEWORK, "framework:instant_reminder")
    assert message_provenance({"role": "user", "content": "<deferred-reminder>\ndue"}) == (
        FRAMEWORK, "framework:deferred_reminder")
    assert message_provenance({"role": "user", "content": "<noting-task>\ntask"}) == (
        FRAMEWORK, "framework:noting_task")
    assert message_provenance({"role": "user", "content": "<framework-message>\nNOTING RESULT\nCURRENT NOTEBOOK SNAPSHOT"}) == (
        NOTEBOOK, "notebook:noting_result")
    assert message_provenance({"role": "user", "content": "x", "display_kind": "future_carrier"}) == (
        FRAMEWORK, "framework:unknown:future_carrier")


def test_digests_are_canonical_and_malformed_tool_calls_are_reported():
    first = tool_call_digests('[{"id": "1", "function": {"name": "terminal", "arguments": "{\\"b\\": 2, \\"a\\": 1}"}}]')
    second = tool_call_digests([{"function": {"name": "terminal", "arguments": '{"a":1,"b":2}'}}])
    assert first == second == [{"name": "terminal", "args_digest": argument_digest('{"a":1,"b":2}')}]
    assert tool_call_digests("not-json") is None
    assert tool_call_digests(None) == []
    assert content_digest("same") == content_digest("same")
    assert content_digest("same") != content_digest("different")
