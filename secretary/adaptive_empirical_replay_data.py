"""Numeric, provenance-preserving inputs for chronological policy replay."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_components(raw, numeric, gpt_numeric=None):
    """Use the live import projection, retaining unknown invoices and source tags."""
    from secretary.adaptive_samples import normalize_sample

    result = []
    metadata = {row["session"]: row for row in (gpt_numeric or {}).get("sessions", [])}
    target = (gpt_numeric or {}).get("root_session")
    for original in raw["samples"]:
        row = deepcopy(original)
        row["usage"] = {key: row.get(key) for key in
                        ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens")}
        proof = {}
        for key, value in row.get("proof", {}).items():
            if isinstance(value, dict):
                for child, label in value.items():
                    proof[key + ":" + child] = label
            else:
                proof[key] = value
        if row["component"] == "noting" and proof.get("source") == "usage-20261031":
            turn = numeric["turns"][proof["source_index"]]
            proof["calls"] = len(turn["requests"]) or None
            proof["source_session_hash"] = turn["session"]
        elif row["component"] == "compaction" and proof.get("source") == "usage-20261031":
            proof["source_session_hash"] = numeric["compactions"][proof["source_index"]]["session"]
        elif row["component"] == "noting":
            proof["source_session_hash"] = row["operation_id"].removeprefix("noting:")
        else:
            proof["source_session_hash"] = target
        session = proof.get("source_session_hash")
        meta = metadata.get(session, {})
        parent = meta.get("parent_session")
        proof["parent_session_hash"] = parent
        proof["source_conversation_evidence"] = ("same_target_binding" if target is not None and (session == target or meta.get("same_conversation"))
            else "same_target_parent_chain" if target is not None and parent == target
            else "foreign_or_unproven_component_pool")
        row.update(source_kind="component_pool", ownership="declared_historical_component_pool")
        row["proof"] = proof
        result.append(normalize_sample(row))
    return result


def _jobs(events):
    requests = {}
    previous = None
    jobs = []
    for event in sorted(events, key=lambda row: (row["at"], row["event_id"])):
        if event["kind"] == "request" and event.get("turn_id"):
            requests.setdefault(event["turn_id"], []).append(event)
        if event["kind"] != "turn_end":
            continue
        identity = event.get("turn_id") or event["event_id"].removeprefix("turn:")
        rows = requests.get(identity, [])
        inputs = [row.get("input_tokens") for row in rows]
        known = bool(inputs) and all(isinstance(value, (int, float)) for value in inputs)
        monotone = known and all(a <= b for a, b in zip(inputs, inputs[1:]))
        span = inputs[-1] - inputs[0] if monotone else None
        suffix = None
        if known and previous and previous.get("context_epoch") == event.get("context_epoch"):
            difference = inputs[0] - previous["context_tokens"]
            suffix = difference if difference >= 0 else None
        duration = event.get("duration_seconds")
        if duration is None or duration < 0:
            continue  # No start can be reconstructed; do not invent a zero busy interval.
        outputs = [row.get("output_tokens") for row in rows]
        jobs.append(dict(id=identity, start=event["at"] - duration, end=event["at"],
                         source=event.get("source", "unknown"), duration=duration,
                         calls=len(rows), growth_tokens=span, first_suffix_tokens=suffix,
                         output_tokens=sum(outputs) if outputs and all(v is not None for v in outputs) else None,
                         context_tokens=event.get("context_tokens"), epoch=event.get("context_epoch"),
                         first_input=inputs[0] if known else None,
                         input_footprint_contract="within_turn_prompt_span_plus_known_nonnegative_suffix; missing_is_unknown",
                         requests=rows, terminal_event=event))
        previous = event if event.get("context_tokens") is not None else None
    return sorted(jobs, key=lambda row: (row["start"], row["id"]))


def prepare(input_dir, manifest_path, components_path, cases_path):
    """Freeze a replay contract; this function never imports or runs a policy."""
    input_dir = Path(input_dir)
    manifest = read_json(manifest_path)
    sources = {}
    for name, receipt in manifest.items():
        path = input_dir / Path(receipt["frozen_path"]).name
        if file_sha(path) != receipt["sha256"]:
            raise ValueError("Frozen input hash mismatch: " + name)
        sources[name] = read_json(path)
    raw = sources["events-20261106"]
    snapshot = sources["snapshot-20261103"]
    cases = read_json(cases_path)
    components = normalized_components(read_json(components_path), sources["usage-20261031"],
                                       sources["gpt-numeric-20261102"])
    return dict(version="empirical-historical-replay-v1", baseline=cases["baseline"],
                input_manifest=manifest, experience_sha256=file_sha(cases_path),
                component_source_sha256=file_sha(components_path), cases=cases["cases"],
                mechanism_supplements=cases["mechanism_supplements"],
                cutoff=raw["at"], config=snapshot["config"], snapshot=snapshot["result"]["snapshot"],
                events=raw["events"], jobs=_jobs(raw["events"]), maintenance_samples=components,
                reminder_schedule=[dict(schedule_id=job["id"], due_at=job["start"],
                                        available_at=min(case["start"] for case in cases["cases"]),
                                        source="declared_retrospective_known_schedule_condition_not_registration_receipt")
                                   for job in _jobs(raw["events"]) if job["source"] == "reminder"],
                reminder_schedule_known_from=min(case["start"] for case in cases["cases"]),
                job_exclusions=[dict(event_id=r["event_id"], reason="missing_turn_duration_or_start")
                                for r in raw["events"] if r["kind"] == "turn_end"
                                and (r.get("duration_seconds") is None or r["duration_seconds"] < 0)],
                component_censor_audit=read_json(components_path)["censored"],
                assumptions=[
                    "Counterfactual future demand uses historical external submissions and Reminder jobs unchanged.",
                    "Policy sees only at/available_at<=decision time, never the future demand queue.",
                    "Coverage is reconstructed from final certified spans as a declared retrospective host-coverage condition.",
                    "Initial model contract is standardized to the recorded GPT target; behavioral history remains cross-model.",
                    "Initial HB mode uses a recorded proposal as a declared phase assumption, not proof of historical adoption.",
                    "Reminder schedule is a declared known-schedule condition; unknown-schedule sensitivity is separate.",
                    "After action divergence each policy owns context, cache, HB phase, busy time and pending plan.",
                    "Work increments omit unknown first input/final output; past-only suffix proxies and sensitivities are labelled.",
                    "Component availability at historical settlement is retrospective; production imports additionally enforce imported_at.",
                    "Explicit user-Stop receipts are conditional on shared actual cancel events, never sampled as invented user actions; mechanical failures remain sampled.",
                    "Settlement draw uses the fixed seed-2 median-cost stratum first, then deterministic subsequent strata; adverse draws remain sensitivities.",
                    "Context endpoint/rough measurements and missing auxiliary invoices are conditional proxies, not realized savings.",
                ])


def coverage_at(events, at):
    """Materialize only the past part of the explicitly declared coverage condition."""
    result = []
    for row in events:
        if row.get("kind") != "coverage" or row.get("start_at", at) >= at:
            continue
        value = deepcopy(row)
        end = min(at, row["end_at"])
        if end <= row["start_at"]:
            continue
        value.update(at=end, end_at=end, available_at=end,
                     retrospective_condition="final_certified_span_reconstructed_without_future_exposure")
        result.append(value)
    return result


def past_events(package, at):
    result = [deepcopy(row) for row in package["events"]
              if row["kind"] not in ("coverage", "decision")
              and max(row["at"], row.get("available_at", row["at"])) <= at]
    result.extend(coverage_at(package["events"], at))
    result.extend(deepcopy(row) for row in package["maintenance_samples"]
                  if max(row["at"], row.get("available_at", row["at"])) <= at)
    return sorted(result, key=lambda row: (row["at"], row["event_id"]))


def known_reminders(package, at):
    """Read as-of schedule witnesses, independently of the future demand queue."""
    visible = [deepcopy(row) for row in package.get("reminder_schedule", [])
               if max(row.get("at", row["available_at"]), row["available_at"]) <= at]
    latest = {}
    for row in sorted(visible, key=lambda row: row["available_at"]):
        latest[row["schedule_id"]] = row
    due = sorted({row["due_at"] for row in latest.values()
                  if row.get("enabled", True) and row.get("due_at") is not None and row["due_at"] >= at})
    known_from = package.get("reminder_schedule_known_from")
    return dict(known=bool(visible) or (known_from is not None and known_from <= at),
                due_times=due, witnesses=list(latest.values()),
                contract="as_of_schedule_witnesses_not_future_jobs")
