"""Historical input truth contracts, ambiguity, clones and missing information."""
from secretary import adaptive_history as history


def row(**values):
    return {"role": "user", "row_id": 1, "session_hash": "session", "uid_hash": "uid",
            "timestamp": 100.0, "display_kind": None, "metadata_keys": [], **values}


def test_role_turn_source_and_wrapper_do_not_prove_human():
    for value in (row(), row(turn_source={"valid": True, "uid_matches": True}), row(wrapper_tag="heartbeat")):
        assert history.classify_source(value)["origin"] == "unknown"
        assert not history.classify_source(value)["verified"]


def test_web_native_entry_proves_submission_even_if_user_pastes_wrapper():
    proof = history.classify_source(row(client_submission_id_hash="entry", wrapper_tag="heartbeat"))
    assert proof["origin"] == "user" and proof["verified"] and proof["ingress"] == "web_submit"
    assert not history.classify_source(row(client_submission_id_hash="entry", flag_internal=True))["verified"]


def test_gateway_requires_owner_inbound_id_and_native_projection():
    value = row(gateway_input_owner_hash="owner", platform_message_id_hash="inbound", api_gateway_native_transform=True)
    assert history.classify_source(value)["verified"]
    for key in ("gateway_input_owner_hash", "platform_message_id_hash", "api_gateway_native_transform"):
        reduced = dict(value)
        reduced.pop(key)
        assert not history.classify_source(reduced)["verified"]


def test_native_framework_is_not_a_submission():
    proof = history.classify_source(row(display_kind="process_complete", metadata_origin="notebook", framework_display_text_matches=True))
    assert proof["origin"] == "framework" and proof["verified"] and not proof["potential_user_input"]


def test_clones_are_deduplicated_but_source_conflicts_remain_unknown():
    first = row(client_submission_id_hash="entry")
    copies = history.source_records([first, {**first, "row_id": 2}, row(uid_hash="future", timestamp=200)], 150)
    assert len(copies) == 1 and copies[0]["physical_copies"] == 2
    assert len(history.submission_records(copies)) == 1
    conflict = history.source_records([first, {**first, "row_id": 2, "client_submission_id_hash": "other"}], 150)
    assert not conflict[0]["origin_evidence"]["verified"]


def test_time_join_requires_mutual_uniqueness():
    sources = history.source_records([row(client_submission_id_hash="entry")], 200)
    assert history.match_turn_sources([{"session": "session", "start": 100.2}], sources)[0]["source_index"] == 0
    ambiguous = history.match_turn_sources([{"session": "session", "start": 100.2}, {"session": "session", "start": 100.4}], sources)
    assert all(item["source_index"] is None for item in ambiguous)


def test_missing_cache_is_unknown_and_all_original_values_are_retained():
    request = {"at": 100, "input_total": 100, "cache": 0, "cache_reported": False, "fresh": 100, "output": 2}
    normalized = history.normalize_request(request, 0)
    assert normalized["cache"] is None and normalized["fresh"] is None and normalized["raw"] == request
    request.update(cache=80, cache_reported=True, fresh=20)
    assert history.normalize_request(request, 0)["fresh"] == 20


def test_unmatched_submissions_remain_in_independent_sequence():
    sources = history.source_records([row(client_submission_id_hash="entry")], 200)
    assert history.match_turn_sources([], sources) == []
    assert len(history.submission_records(sources)) == 1
    assert history.submission_records(sources)[0]["available_at"] is None


def test_negative_labels_are_restricted_and_unknown_inputs_censor():
    kwargs = {"storage_start": 0, "cutoff": 200, "submissions": [], "unknown_sources": [], "maintenance": []}
    value = history.restricted_window(100, 150, **kwargs)
    assert value["negative_proven_for_restricted_stream"] and not value["runtime_monitoring_coverage"]
    kwargs["unknown_sources"] = [{"at": 125}]
    assert history.restricted_window(100, 150, **kwargs)["exact_count"] is None
    kwargs["unknown_sources"] = []
    kwargs["maintenance"] = [{"start": 110, "censor_end": 160}]
    assert history.restricted_window(100, 150, **kwargs)["exact_count"] is None
    assert history.restricted_window(150, 250, **kwargs)["exact_count"] is None


def test_unmatched_future_turn_censors_even_without_a_surviving_input_row():
    value = history.restricted_window(100, 150, storage_start=0, cutoff=200, submissions=[],
                                      unknown_sources=[], maintenance=[], uncertain_turns=[{"start": 130}])
    assert value["exact_count"] is None and "source_turn_match_unresolved" in value["censor_reasons"]


def test_deferred_reminder_requires_actual_producer_and_ids():
    value = row(display_kind="process_complete", metadata_origin="reminder", metadata_producer="reminder",
                wrapper_tag="deferred-reminder", metadata_keys=["reminder_ids"])
    assert history.classify_source(value)["origin"] == "reminder"
    value.pop("metadata_producer")
    assert not history.classify_source(value)["verified"]
