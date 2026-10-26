"""Schedule advice reaches the actual durable Framework carrier without a new Turn."""


import pytest

from secretary.noting_notifications import SCHEDULE_SUGGESTION_INSTRUCTION
from tests.secretary.test_r3_framework import (
    book, commit, config, notices, publish, runtime as runtime,
)

ADVICE = {
    "content": "Review the museum booking with the user's family after their dates arrive; no tickets have been purchased. Ask which available date works before taking action.",
    "schedule": "when the family replies, otherwise consider a suitable follow-up time",
}


@pytest.mark.parametrize("proposal", [False, True])
def test_advice_is_last_after_complete_notebook_and_optional_persistence(runtime, proposal):
    parent, db = runtime
    config(parent, 1 if proposal else 999999, 1 if proposal else 999999)
    store = book(parent)
    entry = store.create("matter", {"description": "Family museum visit awaits dates", "completion_condition": "Dates agreed"},
                         source_message_uids=["m1"], schedule_suggestion=ADVICE)["entry"]
    result = commit(store)
    assert publish(parent, result)
    row = notices(db)[-1]
    body = row["display_metadata"]["display_text"]
    assert body.endswith(SCHEDULE_SUGGESTION_INSTRUCTION)
    assert body.count(SCHEDULE_SUGGESTION_INSTRUCTION) == 1
    assert ADVICE["content"] in body and ADVICE["schedule"] in body
    assert entry["entry_id"] in body
    assert ("PERSISTENCE PROPOSAL REQUEST" in body) is proposal
    if proposal:
        assert body.index("PERSISTENCE PROPOSAL REQUEST") < body.index(SCHEDULE_SUGGESTION_INSTRUCTION)
    assert row["content"].endswith(SCHEDULE_SUGGESTION_INSTRUCTION + "\n</framework-message>")
    assert parent._session_messages[-1]["content"] == row["content"]
    parent.run_conversation.assert_not_called()


@pytest.mark.parametrize("clear", [False, True])
def test_absent_or_cleared_suggestion_adds_no_main_instruction(runtime, clear):
    parent, db = runtime
    store = book(parent)
    entry = store.create("matter", {"description": "Museum visit", "completion_condition": "Dates agreed"},
                         source_message_uids=["m1"], **({"schedule_suggestion": ADVICE} if clear else {}))["entry"]
    if clear:
        assert store.update(entry["entry_id"], {"source_message_uids": ["m1"], "schedule_suggestion": None})["changed"]
    assert publish(parent, commit(store))
    assert SCHEDULE_SUGGESTION_INSTRUCTION not in notices(db)[-1]["content"]
    parent.run_conversation.assert_not_called()
