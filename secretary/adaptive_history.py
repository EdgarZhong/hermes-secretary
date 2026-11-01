"""Read-only normalization of historical numeric logs and native source evidence.

This module does not infer people from roles/platform labels, manufacture monitoring
coverage, or execute a policy. Classification predicates require audited producer facts.
"""
from __future__ import annotations

from collections import defaultdict
import math


def _real(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def classify_source(row):
    """A carrier's shape is a hint; a native Turn identity is not a human witness."""
    result = {"origin": "unknown", "verified": False, "ingress": "unknown", "evidence": [],
              "carrier_hint": row.get("wrapper_tag"), "potential_user_input": True}
    if row.get("role") != "user":
        result["potential_user_input"] = False
        return result
    if any(row.get("flag_" + key) is True for key in ("is_bot", "internal", "synthetic_prompt", "hermes_plugin_injection", "replay", "retry")):
        result["evidence"].append("explicit_nonhuman_or_replay_flag")
        return result
    client = row.get("client_submission_id_hash")
    gateway = row.get("gateway_input_owner_hash")
    machine = row.get("display_kind") == "process_complete"
    if client and not gateway and not machine:
        result.update(origin="user", verified=True, ingress="web_submit", evidence=["closed_submit_idle_schema_and_native_client_submission_writer"])
        return result
    if gateway and row.get("platform_message_id_hash") and row.get("api_gateway_native_transform") and not client and not machine:
        result.update(origin="user", verified=True, ingress="gateway_adapter", evidence=["gateway_owner_and_inbound_id_and_native_api_body_transform"])
        return result
    if machine and row.get("framework_display_text_matches") and row.get("metadata_origin") in {"framework", "notebook"} and not client:
        result.update(origin="framework", verified=True, potential_user_input=False, evidence=["framework_producer_metadata_and_exact_carrier_projection"])
        return result
    if (machine and row.get("metadata_origin") == "reminder" and row.get("wrapper_tag") == "deferred-reminder"
            and row.get("metadata_producer") == "reminder"
            and "reminder_ids" in row.get("metadata_keys", []) and not client):
        result.update(origin="reminder", verified=True, potential_user_input=False, evidence=["durable_deferred_reminder_producer_metadata"])
        return result
    if row.get("turn_source"):
        result["evidence"].append("native_turn_source_identity_only")
    if gateway:
        result["evidence"].append("gateway_owner_is_not_human_proof")
    if row.get("wrapper_tag"):
        result["evidence"].append("carrier_shape_has_no_persisted_trusted_input_witness")
    if not result["evidence"]:
        result["evidence"].append("no_audited_ingress_witness")
    return result


def source_records(rows, cutoff):
    """Deduplicate native compression clones by UID, preserving source conflicts."""
    grouped = defaultdict(list)
    for row in rows:
        if row.get("role") == "user" and _real(row.get("timestamp")) and row["timestamp"] <= cutoff and row.get("uid_hash"):
            grouped[(row.get("session_hash"), row["uid_hash"])].append(row)
    records = []
    for (session, uid), copies in grouped.items():
        copies.sort(key=lambda row: row["row_id"])
        classifications = [classify_source(row) for row in copies]
        proved = [value for value in classifications if value["verified"]]
        identities = {row.get("client_submission_id_hash") or row.get("gateway_input_owner_hash") for row in copies}
        identities.discard(None)
        outcomes = {(value["origin"], value["ingress"]) for value in proved}
        classification = proved[0] if proved else classifications[0]
        conflict = len(outcomes) > 1 or len(identities) > 1
        if conflict:
            classification = {**classification, "origin": "unknown", "verified": False,
                              "potential_user_input": True, "evidence": ["conflicting_source_versions"]}
        times = [row["timestamp"] for row in copies]
        records.append({"event_id": "uid:" + uid, "uid_hash": uid, "session_hash": session,
                        "at": min(times), "timestamp_range": [min(times), max(times)], "available_at": None,
                        "row_ids": [row["row_id"] for row in copies], "physical_copies": len(copies),
                        "entry_identity_hash": next(iter(identities)) if len(identities) == 1 else None,
                        "native_source_identity_present": any(row.get("turn_source") and row["turn_source"].get("uid_matches") for row in copies),
                        "display_kinds": sorted({row["display_kind"] for row in copies if row.get("display_kind")}),
                        "origin_evidence": classification, "source_metadata_available_at_exact": False,
                        "uncertainties": (["source_identity_conflict"] if conflict else []) +
                                         (["timestamp_versions_disagree"] if max(times) != min(times) else [])})
    return sorted(records, key=lambda record: (record["at"], record["uid_hash"]))


def match_turn_sources(turns, sources, *, max_before_seconds=5.0, max_after_seconds=1.0):
    """Mutually unique bounded time joins; never pick the nearest ambiguous candidate."""
    candidates, owners = {}, defaultdict(list)
    for index, turn in enumerate(turns):
        possible = []
        for source_index, source in enumerate(sources):
            kinds = source["display_kinds"]
            non_start = kinds and set(kinds) <= {"steer", "process_complete"} and not source["native_source_identity_present"]
            difference = source["at"] - turn["start"]
            if (source["session_hash"] == turn["session"] and not non_start
                    and -max_before_seconds <= difference <= max_after_seconds):
                possible.append(source_index)
                owners[source_index].append(index)
        candidates[index] = possible
    result = []
    for index, turn in enumerate(turns):
        possible = candidates[index]
        match = possible[0] if len(possible) == 1 and len(owners[possible[0]]) == 1 else None
        result.append({"source_index": match, "candidate_count": len(possible),
                       "method": "mutually_unique_time_window" if match is not None else "unmatched_or_ambiguous",
                       "source_minus_turn_start_seconds": sources[match]["at"] - turn["start"] if match is not None else None,
                       "max_before_seconds": max_before_seconds, "max_after_seconds": max_after_seconds})
    return result


def normalize_request(request, numeric_index):
    """Collector input_total is whole prompt; its absent-cache placeholder is unknown."""
    total, cache = request["input_total"], request.get("cache")
    known = request.get("cache_reported") is True
    if not _real(total) or total < 0 or not _real(request["output"]) or request["output"] < 0:
        raise ValueError("invalid original token measurement")
    if known and (not _real(cache) or not 0 <= cache <= total or request.get("fresh") != total - cache):
        raise ValueError("inconsistent cache/total/fresh receipt")
    return {"numeric_request_index": numeric_index, "at": request["at"], "available_at": request["at"],
            "input_total": total, "cache": cache if known else None, "cache_reported": known,
            "fresh": total - cache if known else None, "output": request["output"], "latency": request.get("latency"),
            "at_semantics": "completed_response_log_timestamp", "raw": dict(request)}


def submission_records(sources):
    """Retain proven submissions even when they have no corresponding model/API Turn."""
    grouped = defaultdict(list)
    for source in sources:
        proof = source["origin_evidence"]
        if proof["verified"] and proof["origin"] == "user":
            identity = source["entry_identity_hash"] or source["uid_hash"]
            grouped[(proof["ingress"], identity)].append(source)
    submissions = []
    for (ingress, identity), records in grouped.items():
        earliest = min(records, key=lambda record: record["at"])
        known = [record["available_at"] for record in records if record["available_at"] is not None]
        submissions.append({"event_id": ingress + ":" + identity, "at": earliest["at"],
                            "available_at": min(known) if known else None, "ingress": ingress,
                            "identity_hash": identity, "uid_hashes": sorted({record["uid_hash"] for record in records}),
                            "verified": True, "origin_evidence": earliest["origin_evidence"]["evidence"],
                            "time_semantics": "native_accepted_or_adapter_observed_timestamp_not_user_send_time",
                            "availability_semantics": "matched_first_response_upper_bound" if known else "historical_commit_time_unavailable",
                            "uncertainties": sorted({value for record in records for value in record["uncertainties"]})})
    return sorted(submissions, key=lambda value: (value["at"], value["event_id"]))


def restricted_window(start, end, *, storage_start, cutoff, submissions, unknown_sources, maintenance, uncertain_turns=()):
    """Assess retrospective persisted-stream labels, without claiming live coverage."""
    reasons = []
    if start < storage_start or end > cutoff or end <= start:
        reasons.append("outside_frozen_storage_bounds")
    if any(start < row["at"] <= end for row in unknown_sources):
        reasons.append("unclassified_persisted_input")
    if any(row["start"] < end and row.get("censor_end", cutoff) > start for row in maintenance):
        reasons.append("maintenance_or_unknown_termination")
    if any(start < row["start"] <= end for row in uncertain_turns):
        reasons.append("source_turn_match_unresolved")
    selected = [row for row in submissions if start < row["at"] <= end]
    if any("timestamp_versions_disagree" in row.get("uncertainties", []) for row in selected):
        reasons.append("submission_event_time_ambiguous")
    if any(row["available_at"] is None for row in selected):
        reasons.append("label_availability_unproven")
    return {"known_count": len(selected), "exact_count": len(selected) if not reasons else None,
            "negative_proven_for_restricted_stream": not reasons and not selected,
            "censor_reasons": reasons, "runtime_monitoring_coverage": False,
            "label_scope": "conditional_persisted_submission_sequence",
            "label_available_at": max([end, *(row["available_at"] for row in selected if row["available_at"] is not None)]) if not reasons else None}
