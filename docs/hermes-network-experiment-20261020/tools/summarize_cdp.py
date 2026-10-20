#!/usr/bin/env python3
"""Offline, allowlisted HTTP summaries for the redacted phone_observer JSONL.

Python 3.9+; standard library only. No network, browser, or device operations.
The input is the collector's flattened JSONL, not a HAR or raw CDP session.
"""

import argparse
import collections
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import tempfile


UNKNOWN = "unknown"
SCHEMA_VERSION = 1
HTTP_EVENTS = {
    "Network.requestWillBeSent", "Network.responseReceived",
    "Network.dataReceived", "Network.loadingFinished", "Network.loadingFailed",
}
SAFE_HEADERS = {
    "content-type", "content-length", "content-encoding", "cache-control",
    "cf-cache-status", "cf-ray", "age",
}
TIMING_FIELDS = {
    "requestTime", "proxyStart", "proxyEnd", "dnsStart", "dnsEnd",
    "connectStart", "connectEnd", "sslStart", "sslEnd", "sendStart", "sendEnd",
    "receiveHeadersStart", "receiveHeadersEnd",
}
OUTCOMES = (
    "completed", "failed", "cancelled", "redirected", "capture_truncated",
    "superseded_without_redirect",
)


class InputError(Exception):
    pass


def number(value):
    """Missing, non-finite and boolean values are not numerical zero."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            if math.isfinite(value):
                return value
        except OverflowError:
            pass
    return None


def nonnegative(value):
    value = number(value)
    return value if value is not None and value >= 0 else None


def known(value):
    return UNKNOWN if value is None else value


def first(mapping, *names):
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return None


def boolean(value):
    return value if isinstance(value, bool) else None


def one(value):
    if isinstance(value, list):
        return value[0] if len(value) == 1 else None
    return value


def token(value):
    value = one(value)
    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:/-]{1,160}", value):
        return value
    return None


def safe_path(value):
    # Never copy a full URL, query string or fragment into the result.
    if not isinstance(value, str) or not value.startswith("/"):
        return None
    return value.split("?", 1)[0].split("#", 1)[0]


def query_integer(value):
    value = one(value)
    if isinstance(value, str) and re.fullmatch(r"\d{1,12}", value):
        return int(value)
    value = nonnegative(value)
    return int(value) if value is not None and int(value) == value else None


def query_boolean(value):
    value = one(value)
    if isinstance(value, bool):
        return value
    return {"true": True, "false": False}.get(value) if isinstance(value, str) else None


def wall_iso(value):
    value = number(value)
    if value is None:
        return UNKNOWN
    try:
        return datetime.datetime.fromtimestamp(
            value, datetime.timezone.utc
        ).isoformat(timespec="milliseconds")
    except (OverflowError, OSError, ValueError):
        return UNKNOWN


def rounded(value):
    return round(value, 6) if value is not None else UNKNOWN


def interval(start, end, anomalies, name):
    if start is None or end is None:
        return None
    value = end - start
    if value < 0:
        anomalies.add(name + ":negative_timestamp_interval")
        return None
    return value


def request_kind(path, query):
    if path and path.endswith("/messages"):
        if query["detail_count"] is not None:
            return "history_details"
        return "history_cards" if query["view"] == "cards" else "history_messages"
    if path and re.fullmatch(r"/api/sessions/[^/]+", path):
        return "session_metadata"
    if path == "/api/sessions":
        return "session_list"
    if path and path.startswith("/api/fs/"):
        return "file_api"
    return "other"


class Request:
    def __init__(self, source, target, request_id, hop, line, ui):
        self.source = source
        self.target = target
        self.request_id = request_id
        self.hop = hop
        self.first_line = line
        self.last_line = line
        self.start = None
        self.headers = None
        self.end = None
        self.start_wall = None
        self.end_wall = None
        self.start_observed = False
        self.outcome = None
        self.reason = None
        self.status = None
        self.host = None
        self.path = None
        self.verb = None
        self.query = dict.fromkeys(("view", "summary", "limit", "offset", "detail_count"))
        self.response = dict.fromkeys((
            "protocol", "connection_id", "connection_reused", "remote_ip", "remote_port",
            "from_disk_cache", "from_service_worker", "from_prefetch_cache",
        ))
        self.safe_headers = {}
        self.timing = {}
        self.data = []
        self.encoded_bytes = None
        self.error_code = None
        self.canceled_flag = None
        self.cancellation_evidence = None
        self.blocked_reason = None
        self.redirect_to = None
        self.anomalies = set()
        self.network_types = []
        self.visibility_at_start = (ui or {}).get("visibility")
        self.note_ui(ui)

    def note_ui(self, ui):
        network = (ui or {}).get("network")
        if network and network not in self.network_types:
            self.network_types.append(network)

    def location(self, row):
        if self.host is None:
            self.host = token(row.get("host"))
        if self.path is None:
            self.path = safe_path(row.get("path"))
        if self.verb is None:
            self.verb = token(row.get("verb"))
        for key in self.query:
            if self.query[key] is not None:
                continue
            if key == "view":
                self.query[key] = token(row.get(key))
            elif key == "summary":
                self.query[key] = query_boolean(row.get(key))
            else:
                self.query[key] = query_integer(row.get(key))

    def receive_headers(self, row):
        self.headers = number(row.get("ts"))
        self.status = query_integer(row.get("status"))
        aliases = {
            "protocol": ("protocol",),
            "connection_id": ("connectionId", "connection_id"),
            "connection_reused": ("reused", "connectionReused", "connection_reused"),
            "remote_ip": ("remoteIPAddress", "remote_ip", "remote_ip_address"),
            "remote_port": ("remotePort", "remote_port"),
            "from_disk_cache": ("cache", "fromDiskCache", "from_disk_cache"),
            "from_service_worker": ("fromServiceWorker", "from_service_worker"),
            "from_prefetch_cache": ("fromPrefetchCache", "from_prefetch_cache"),
        }
        for field, names in aliases.items():
            value = first(row, *names)
            if field == "connection_reused" or field.startswith("from_"):
                value = boolean(value)
            elif field == "remote_port":
                value = query_integer(value)
            elif field == "connection_id":
                value = str(value) if isinstance(value, str) or number(value) is not None else None
            else:
                value = token(value)
            self.response[field] = value
        headers = row.get("headers")
        if isinstance(headers, dict):
            for name, value in headers.items():
                if isinstance(name, str) and name.lower() in SAFE_HEADERS:
                    if isinstance(value, str) or number(value) is not None:
                        self.safe_headers[name.lower()] = value
        timing = row.get("timing")
        if isinstance(timing, dict):
            for name in TIMING_FIELDS:
                if number(timing.get(name)) is not None:
                    self.timing[name] = timing[name]

    def close(self, outcome, row, line, reason=None):
        self.outcome = outcome
        self.reason = reason
        self.last_line = line
        self.end = number(row.get("ts"))
        self.end_wall = number(row.get("wall"))

    def result(self, label, capture_end):
        anomalies = set(self.anomalies)
        total = interval(self.start, self.end, anomalies, "total")
        headers_time = interval(self.start, self.headers, anomalies, "headers")
        body_time = interval(self.headers, self.end, anomalies, "body_after_headers")
        # A zero-byte event is not body progress. Keep arrival order and flag clock
        # anomalies rather than silently sorting events or clamping them to zero.
        progress = [d[0] for d in self.data if d[0] is not None and (
            (d[1] is not None and d[1] > 0) or (d[2] is not None and d[2] > 0)
        )]
        first_gap = interval(self.headers, progress[0], anomalies, "headers_to_first_progress") if progress else None
        last_gap = interval(progress[-1], self.end, anomalies, "last_progress_to_end") if progress else None
        middle = [interval(a, b, anomalies, "between_progress") for a, b in zip(progress, progress[1:])]
        gaps = [g for g in [first_gap, *middle, last_gap] if g is not None]
        # If no positive-byte data event was recorded, headers-to-end is an
        # observation gap, not evidence that the entire body stalled.
        no_progress_gap = interval(self.headers, self.end, anomalies, "headers_to_end_without_progress") if not progress else None
        max_gap = max(gaps) if gaps else None
        full_gap_coverage = bool(progress) and first_gap is not None and last_gap is not None and all(g is not None for g in middle)
        observed_data_bytes = self.data_sum(1)
        observed_encoded_data_bytes = self.data_sum(2)
        if self.status is None:
            http_result = UNKNOWN
        elif 200 <= self.status < 300:
            http_result = "2xx"
        elif 300 <= self.status < 400:
            http_result = "3xx"
        elif self.status >= 400:
            http_result = "http_error"
        else:
            http_result = "other"
        return {
            "source": self.source, "target": self.target, "request_id": self.request_id,
            "hop_index": self.hop, "label": label,
            "first_source_line": self.first_line, "last_source_line": self.last_line,
            "host": known(self.host), "path": known(self.path), "method": known(self.verb),
            "query_summary": {k: known(v) for k, v in self.query.items()},
            "kind": request_kind(self.path, self.query),
            "outcome": self.outcome, "termination_reason": known(self.reason),
            "start_observed": self.start_observed,
            "end_observed": self.outcome in {"completed", "failed", "cancelled", "redirected"},
            "capture_coverage": "missing_request_start" if not self.start_observed else (
                "missing_terminal_event" if self.outcome in {"capture_truncated", "superseded_without_redirect"} else "start_and_end_observed"
            ),
            "status": known(self.status), "http_result": http_result,
            **{k: known(v) for k, v in self.response.items()},
            "is_h2": self.response["protocol"] == "h2" if self.response["protocol"] is not None else UNKNOWN,
            "response_headers": self.safe_headers,
            "cdp_resource_timing": self.timing,
            "start_wall_utc": wall_iso(self.start_wall), "end_wall_utc": wall_iso(self.end_wall),
            "start_monotonic": known(self.start), "headers_monotonic": known(self.headers),
            "end_monotonic": known(self.end),
            "end_time_basis": "next_redirect_request_start" if self.outcome == "redirected" else (
                "terminal_cdp_event" if self.end is not None else UNKNOWN
            ),
            "total_seconds": rounded(total), "headers_seconds": rounded(headers_time),
            "body_after_headers_seconds": rounded(body_time),
            "encoded_bytes": known(self.encoded_bytes),
            "observed_data_bytes": known(observed_data_bytes),
            "observed_encoded_data_bytes": known(observed_encoded_data_bytes),
            "data_event_count": len(self.data), "positive_progress_event_count": len(progress),
            "headers_to_first_progress_seconds": rounded(first_gap),
            "last_progress_to_end_seconds": rounded(last_gap),
            "max_body_progress_gap_seconds": rounded(max_gap),
            "progress_gap_coverage": "complete" if full_gap_coverage else ("partial" if gaps else "unavailable"),
            "headers_to_end_without_progress_event_seconds": rounded(no_progress_gap),
            "observed_until_seconds": rounded(interval(self.start, capture_end, anomalies, "capture_observation_span")) if self.end is None else UNKNOWN,
            "error_code": known(self.error_code), "cdp_canceled": known(self.canceled_flag),
            "cancellation_evidence": known(self.cancellation_evidence), "cancelled_by": UNKNOWN,
            "blocked_reason": known(self.blocked_reason), "redirect_to": known(self.redirect_to),
            "observed_network_types": self.network_types or [UNKNOWN],
            "ui_visibility_at_start": known(self.visibility_at_start),
            "timing_anomalies": sorted(anomalies),
        }

    def data_sum(self, index):
        if not self.data or any(d[index] is None for d in self.data):
            return None
        return sum(d[index] for d in self.data)


def _record_response(request, row, line_number, ts, active, key):
    if request.headers is not None:
        request.anomalies.add("multiple_response_events_without_redirect_marker")
    request.receive_headers(row)


def _record_data(request, row, line_number, ts, active, key):
    request.data.append((ts, nonnegative(row.get("dataLength")), nonnegative(row.get("encodedDataLength"))))


def _record_finished(request, row, line_number, ts, active, key):
    request.encoded_bytes = nonnegative(row.get("encodedDataLength"))
    request.close("completed", row, line_number, "loadingFinished")
    active.pop(key, None)


def _record_failed(request, row, line_number, ts, active, key):
    # Do not copy arbitrary error text; it may contain URLs or queries.
    error = row.get("errorText")
    match = re.search(r"\bnet::[A-Z][A-Z0-9_]*\b", error) if isinstance(error, str) else None
    request.error_code = match.group(0) if match else None
    request.canceled_flag = boolean(row.get("canceled"))
    request.blocked_reason = token(row.get("blockedReason"))
    cancelled = request.canceled_flag is True or request.error_code == "net::ERR_ABORTED"
    if cancelled:
        request.cancellation_evidence = "cdp_canceled_flag" if request.canceled_flag is True else "ERR_ABORTED"
    request.close("cancelled" if cancelled else "failed", row, line_number, "loadingFailed")
    active.pop(key, None)


_HTTP_RECORDERS = {
    "Network.responseReceived": _record_response,
    "Network.dataReceived": _record_data,
    "Network.loadingFinished": _record_finished,
    "Network.loadingFailed": _record_failed,
}


def read_source(path, source, targets):
    active = {}
    latest = {}
    sequence = collections.Counter()
    requests = []
    ui = {}
    last_ts = {}
    counts = collections.Counter()
    digest = hashlib.sha256()

    def create(key, line):
        sequence[key] += 1
        request = Request(source, key[0], key[1], sequence[key] - 1, line, ui.get(key[0]))
        requests.append(request)
        active[key] = request
        latest[key] = request
        return request

    with path.open("rb") as stream:
        for line_number, raw in enumerate(stream, 1):
            digest.update(raw)
            counts["source_lines"] += 1
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise InputError(f"{path.name}:{line_number}: invalid JSONL; source content omitted") from None
            if not isinstance(row, dict):
                raise InputError(f"{path.name}:{line_number}: expected a JSON object")
            target = str(row["target"]) if row.get("target") is not None else None
            if targets and target not in targets:
                counts["rows_excluded_by_target"] += 1
                continue
            ts = number(row.get("ts"))
            if target is not None and ts is not None:
                last_ts[target] = max(last_ts.get(target, ts), ts)
            event = row.get("event")
            if event == "UI_STATE" and target is not None:
                state = row.get("state") if isinstance(row.get("state"), dict) else {}
                connection = state.get("connection") if isinstance(state.get("connection"), dict) else {}
                ui[target] = {"network": token(connection.get("type")), "visibility": token(state.get("visible"))}
                for key, request in active.items():
                    if key[0] == target:
                        request.note_ui(ui[target])
                continue
            if event not in HTTP_EVENTS:
                counts["ignored_non_http_rows"] += 1
                continue
            if target is None or row.get("id") is None:
                counts["http_rows_missing_target_or_id"] += 1
                continue
            counts["http_event_rows"] += 1
            key = (target, str(row["id"]))
            request = active.get(key)
            if event == "Network.requestWillBeSent":
                redirect_status = query_integer(row.get("redirect_status"))
                if redirect_status is not None:
                    # CDP reuses a requestId for redirects. Each hop gets its own
                    # record, including a partial preceding hop if capture began late.
                    previous = request or create(key, line_number)
                    previous.status = redirect_status
                    previous.redirect_to = {
                        "host": known(token(row.get("host"))),
                        "path": known(safe_path(row.get("path"))),
                    }
                    previous.close("redirected", row, line_number, "redirect_observed")
                    active.pop(key, None)
                elif request is not None:
                    request.outcome = "superseded_without_redirect"
                    request.reason = "request_id_reused_without_redirect_marker"
                    request.last_line = line_number
                    active.pop(key, None)
                request = create(key, line_number)
                request.start_observed = True
                request.start = ts
                request.start_wall = number(row.get("wall"))
                request.location(row)
                continue
            request = request or latest.get(key) or create(key, line_number)
            request.last_line = line_number
            request.location(row)
            if request.outcome in {"completed", "failed", "cancelled", "redirected"}:
                if event in {"Network.loadingFinished", "Network.loadingFailed"}:
                    request.anomalies.add("duplicate_terminal_event")
                    continue
                request.anomalies.add("event_received_after_terminal_event")
            _HTTP_RECORDERS[event](request, row, line_number, ts, active, key)
    for request in active.values():
        request.outcome = "capture_truncated"
        request.reason = "end_of_source_without_terminal_event"
    return requests, last_ts, {
        "source": source, "file_name": path.name, "sha256": digest.hexdigest(),
        **dict(counts),
    }


def stats(values):
    values = [v for v in values if number(v) is not None]
    if not values:
        return {"n": 0, "min": UNKNOWN, "median": UNKNOWN, "max": UNKNOWN}
    return {"n": len(values), "min": rounded(min(values)), "median": rounded(statistics.median(values)), "max": rounded(max(values))}


def group_summary(records):
    complete = [r for r in records if r["outcome"] == "completed" and r["http_result"] == "2xx" and r["start_observed"]]
    return {
        "request_hops": len(records),
        "outcomes": {name: sum(r["outcome"] == name for r in records) for name in OUTCOMES},
        "missing_request_start": sum(not r["start_observed"] for r in records),
        "http_status_counts": dict(sorted(collections.Counter(str(r["status"]) for r in records).items())),
        "protocol_counts": dict(sorted(collections.Counter(str(r["protocol"]) for r in records).items())),
        "from_disk_cache_counts": dict(sorted(collections.Counter(str(r["from_disk_cache"]).lower() for r in records).items())),
        "complete_2xx_with_start_count": len(complete),
        "complete_2xx_statistics": {
            field: stats([r[field] for r in complete])
            for field in ("total_seconds", "headers_seconds", "body_after_headers_seconds", "encoded_bytes", "max_body_progress_gap_seconds")
        },
        "requests_with_timing_anomalies": sum(bool(r["timing_anomalies"]) for r in records),
    }


def atomic_json(path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", nargs="+", type=Path, help="one or more redacted phone_observer JSONL files")
    parser.add_argument("--out-dir", type=Path, required=True, help="output directory for requests.json and summary.json")
    parser.add_argument("--target", action="append", help="include this target ID; repeat for multiple IDs")
    parser.add_argument("--label", default="unlabeled", help="condition label; does not infer network routing")
    args = parser.parse_args(argv)
    try:
        paths = [p.expanduser().resolve() for p in args.jsonl]
        if len(set(paths)) != len(paths):
            raise InputError("the same input path was supplied more than once")
        out_dir = args.out_dir.expanduser().resolve()
        if any(out_dir / name in paths for name in ("requests.json", "summary.json")):
            raise InputError("an output path would overwrite an input file")
        results = []
        sources = []
        targets = set(args.target or [])
        for index, path in enumerate(paths, 1):
            requests, last_ts, source = read_source(path, f"source-{index}", targets)
            sources.append(source)
            results.extend(r.result(args.label, last_ts.get(r.target)) for r in requests)
        generated = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        common = {"schema_version": SCHEMA_VERSION, "generated_at_utc": generated,
                  "label": args.label, "target_filter": sorted(targets), "sources": sources}
        groups = collections.defaultdict(list)
        for result in results:
            groups[(result["source"], result["target"], result["kind"])].append(result)
        summary = {
            **common, **group_summary(results),
            "groups": [
                {"source": key[0], "target": key[1], "kind": key[2], **group_summary(records)}
                for key, records in sorted(groups.items())
            ],
            "notes": [
                "Durations use CDP monotonic ts only; wall is display metadata, never a fallback clock.",
                "unknown means missing, invalid or unobservable; it is not zero, false or proof of absence.",
                "Redirect hops, failed requests, cancellations and capture truncation are separate outcomes.",
                "Completed means a loadingFinished event, not HTTP success, JSON parse or visible UI completion.",
                "Statistics include completed 2xx with an observed start; they may mix networks/caches unless inputs are filtered.",
                "Progress gap statistics may have partial coverage; inspect per-request coverage and timing anomalies.",
                "No percentile or SLA assertion is made; counts, min, median and max describe only these samples.",
                "Files are separate capture sources; requests are not joined or deduplicated across files.",
            ],
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        atomic_json(out_dir / "requests.json", {**common, "requests": results})
        atomic_json(out_dir / "summary.json", summary)
        print(json.dumps({"request_hops": len(results), "outcomes": summary["outcomes"],
                          "requests": str(out_dir / "requests.json"), "summary": str(out_dir / "summary.json")}, ensure_ascii=False))
        return 0
    except (InputError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
