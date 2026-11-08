"""Content-free maintenance receipts, attached to existing execution owners only."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import logging
import threading
import time
import uuid

from secretary.adaptive_features import number

logger = logging.getLogger(__name__)
BUCKETS = ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens")
_active = ContextVar("secretary_adaptive_maintenance", default=None)


def _path_witness(db, ref, session_id):
    """Existing durable path facts only; no new publication or identity is created."""
    with db._read_ctx() as conn:
        row = conn.execute(
            "SELECT s.rewind_count FROM sessions s JOIN secretary_session_bindings b ON b.session_id=s.id "
            "WHERE s.id=? AND b.conversation_ref=?", (session_id, ref)).fetchone()
        if row is None:
            return None
        summary = conn.execute(
            "SELECT id,message_uid FROM messages WHERE session_id=? AND active=1 AND _compressed_summary=1 "
            "ORDER BY id DESC LIMIT 1", (session_id,)).fetchone()
    return (session_id, row[0], tuple(summary) if summary else None)


def normalize_sample(raw):
    """Strict numeric projection shared by explicit imports and live receipts."""
    from secretary.adaptive_import import _model_tags, _text
    if not isinstance(raw, dict) or raw.get("kind") != "maintenance_sample":
        raise ValueError("maintenance_sample required")
    if raw.get("component") not in {"compaction", "noting"}:
        raise ValueError("unknown maintenance component")
    result = {key: _text(raw.get(key), key) for key in ("event_id", "operation_id", "component")}
    for key in ("at", "available_at"):
        value = number(raw.get(key, raw.get("at")))
        if value is None:
            raise ValueError("invalid sample timestamp")
        result[key] = value
    if result["available_at"] < result["at"]:
        raise ValueError("sample available before settlement")
    result.update(_measurements(raw))
    for key in ("model_key", "parent_model_key", "joint_operation_id", "duration_scope", "block_scope",
                "outcome", "context_epoch", "context_after_source", "source_kind", "ownership",
                "source_conversation_ref"):
        if raw.get(key) is not None:
            result[key] = _text(raw[key], key)
    result["usage"] = _usage_buckets(raw.get("usage"))
    observed = raw.get("observed_usage")
    if observed is not None:
        if not isinstance(observed, dict) or any(number(observed.get(key)) is None for key in BUCKETS):
            raise ValueError("invalid observed usage lower bound")
        result["observed_usage"] = {key: number(observed[key]) for key in BUCKETS}
    if raw.get("input_semantics", "fresh") != "fresh":
        raise ValueError("maintenance usage requires disjoint fresh-input buckets")
    result.update(kind="maintenance_sample", input_semantics="fresh", source="framework",
                  verified=raw.get("verified") is True,
                  usage_complete=raw.get("usage_complete") is True and all(
                      value is not None for value in result["usage"].values()))
    result["proof"] = _proof(raw.get("proof", {}))
    result.update(_model_tags(raw))
    return result


def _measurements(raw):
    result = {}
    for key in ("start_at", "duration_seconds", "block_seconds", "context_before", "context_after"):
        value = raw.get(key)
        parsed = number(value)
        if value is not None and parsed is None:
            raise ValueError("invalid maintenance measurement")
        result[key] = parsed if key not in {"context_before", "context_after"} or parsed else None
    return result


def _usage_buckets(usage):
    if usage is not None and not isinstance(usage, dict):
        raise ValueError("invalid usage")
    result = {}
    for key in BUCKETS:
        value = (usage or {}).get(key)
        parsed = number(value)
        if value is not None and parsed is None:
            raise ValueError("invalid usage bucket")
        result[key] = parsed
    return result


def _proof(proof):
    from secretary.adaptive_import import _text
    if not isinstance(proof, dict) or len(proof) > 32:
        raise ValueError("invalid sample proof")
    result = {}
    for key, value in proof.items():
        _text(key, "proof key")
        if isinstance(value, str):
            _text(value, "proof label")
        elif value is not None and not isinstance(value, bool) and number(value) is None:
            raise ValueError("proof must contain bounded labels or numeric facts")
        result[key] = value
    return result


class Collector:
    def __init__(self, parent, component, operation_id, *, joint_operation_id=None, db=None, ref=None,
                 admission_id=None):
        from secretary.adaptive_runtime import _owner, model_key
        owner = _owner(parent)
        self.enabled = owner is not None
        self.closed = False
        self.lock = threading.RLock()
        if not self.enabled:
            return
        self.parent = parent
        self.session_id = getattr(parent, "session_id", None)
        self.compressor = getattr(parent, "context_compressor", None)
        self.db, self.ref, self.config = owner
        if db is not None:
            # Child has a dedicated handle on exactly the same Profile database.
            from pathlib import Path
            if Path(db.db_path).resolve() != Path(self.db.db_path).resolve() or ref != self.ref:
                self.enabled = False
                return
            self.db = db
        self.component, self.operation_id = component, operation_id
        self.joint_operation_id = joint_operation_id
        self.admission_id = admission_id
        self.parent_key = model_key(parent)
        self.initial_path = _path_witness(self.db, self.ref, self.session_id)
        self.publication_path = None
        self.had_runtime_binding = getattr(parent, "_secretary_main_runtime_binding", None) is not None
        self.started_at = time.time()
        self.receipt_count = self.incomplete_requests = 0
        self.observed_usage = dict.fromkeys(BUCKETS, 0)
        self.unknown = set()
        self.identities = set()
        self.mixed_routes = False
        self.first_input_tokens = None
        self.dispatched = 0

    def same_runtime(self, parent):
        from pathlib import Path
        if (parent is not self.parent or getattr(parent, "_secretary_conversation_ref", None) != self.ref
                or getattr(parent, "_secretary_parent_closed", False)
                or Path(getattr(getattr(parent, "_session_db", None), "db_path", "")).resolve()
                != Path(self.db.db_path).resolve()):
            return False
        if self.had_runtime_binding:
            from secretary.noting_scope import is_current_main_runtime
            return is_current_main_runtime(parent)
        return True

    def matches_parent(self, parent):
        if not self.same_runtime(parent):
            return False
        expected = self.publication_path or self.initial_path
        try:
            return expected is not None and _path_witness(self.db, self.ref, parent.session_id) == expected
        except Exception:
            logger.debug("Adaptive committed-path witness unavailable", exc_info=True)
            return False

    def native_publication(self, parent, commit):
        """Called only inside this operation's successful native commit fence."""
        with self.lock:
            if (self.closed or self.component != "compaction" or not self.same_runtime(parent)
                    or getattr(parent, "context_compressor", None) is not self.compressor
                    or commit.session_commit_succeeded is not True):
                return
            rotated = commit.split_status == "rotated_committed" and commit.old_session_id == self.session_id
            in_place = (commit.split_status == "in_place_committed" and commit.compacted_in_place is True
                        and parent.session_id == self.session_id)
            if not (rotated or in_place):
                return
            path = _path_witness(self.db, self.ref, parent.session_id)
            if path is None or path[2] is None or path == self.initial_path:
                return
            if rotated:
                with self.db._read_ctx() as conn:
                    lineage = conn.execute(
                        "SELECT 1 FROM sessions p JOIN sessions c ON c.parent_session_id=p.id "
                        "WHERE p.id=? AND c.id=? AND p.end_reason='compression'",
                        (self.session_id, parent.session_id)).fetchone()
                if lineage is None:
                    return
            self.publication_path = path

    def dispatch(self):
        if self.enabled:
            with self.lock:
                if not self.closed:
                    self.dispatched += 1

    def receipt(self, response, *, provider, model, api_mode, failed=False, streaming=False, canonical=None):
        if not self.enabled:
            return
        from types import SimpleNamespace
        from agent.usage_pricing import normalize_usage
        from agent.usage_read import _unknown_buckets
        raw = getattr(response, "usage", None)
        model = getattr(response, "model", None) or model
        values = dict.fromkeys(BUCKETS)
        if raw is not None and not streaming:
            usage = canonical or normalize_usage(raw, provider=provider, api_mode=api_mode)
            proxy = SimpleNamespace(provider=provider, api_mode=api_mode)
            unknown = _unknown_buckets(proxy, response, usage)
            # Native canonical prompt totals prove an absent separate write bucket is zero
            # only when the raw complete prompt reconciles all disjoint buckets.
            if "total_tokens" in unknown:
                unknown.add("cache_write_tokens")
            values = {key: None if key in unknown else getattr(usage, key) for key in BUCKETS}
        with self.lock:
            if self.closed:
                return  # A detached late callback cannot mutate a settled or successor operation.
            if self.receipt_count == 0 and all(values[key] is not None for key in BUCKETS[:-1]):
                self.first_input_tokens = sum(values[key] for key in BUCKETS[:-1])
            self.receipt_count += 1
            self.incomplete_requests += any(value is None for value in values.values())
            for key, value in values.items():
                if value is None:
                    self.unknown.add(key)
                else:
                    self.observed_usage[key] += value
            identity = tuple(sorted(dict(provider=provider or "unknown", model=model or "unknown", api_mode=api_mode).items()))
            if len(self.identities) < 32:
                self.identities.add(identity)
            elif identity not in self.identities:
                self.mixed_routes = True
            from secretary.adaptive_runtime import record_event
            from secretary.adaptive_model_config import digest
            contract = dict(provider=provider or "unknown", model=model or "unknown", api_mode=api_mode)
            record_event(self.db, self.ref, "maintenance_usage", config=self.config,
                         source="framework", verified=True,
                         event_id=self.operation_id + ":usage:" + uuid.uuid4().hex,
                         operation_id=self.operation_id, component=self.component,
                         model_identity={key: contract[key] for key in ("provider", "model")},
                         model_contract=contract, model_key=digest(contract), parent_model_key=self.parent_key,
                         usage=values, outcome="failed" if failed else "observed")

    def finish(self, outcome, *, context_before=None, context_after=None, context_after_source=None,
               block_seconds=None, block_scope=None):
        if not self.enabled:
            return
        with self.lock:
            if self.closed:
                return
            self.closed = True
            now = time.time()
            usage = {key: self.observed_usage[key] if self.receipt_count and key not in self.unknown else None
                     for key in BUCKETS}
            contract = (dict(next(iter(self.identities))) if len(self.identities) == 1 and not self.mixed_routes
                        else dict(provider="mixed", model="mixed"))
            if self.admission_id is not None:
                # Idle can dispatch Noting before native Compact registers its identity.
                # Only this task's durable same-owner association can close that race.
                row = self.db.noting_admission(self.admission_id)
                if row and row["conversation_ref"] == self.ref:
                    self.joint_operation_id = row.get("operation_id")
            from secretary.adaptive_model_config import digest
            sample = normalize_sample(dict(
                kind="maintenance_sample", component=self.component, event_id=self.operation_id + ":sample:" + self.component,
                operation_id=self.operation_id, joint_operation_id=self.joint_operation_id,
                start_at=self.started_at, at=now, available_at=now, outcome=outcome,
                parent_model_key=self.parent_key, model_key=digest(contract), model_contract=contract,
                model_identity={key: contract[key] for key in ("provider", "model")},
                duration_seconds=now - self.started_at, duration_scope="component_execution",
                block_seconds=block_seconds, block_scope=block_scope, context_before=context_before,
                context_after=context_after, context_after_source=context_after_source,
                usage=usage, usage_complete=bool(self.receipt_count) and self.receipt_count == self.dispatched
                and all(v is not None for v in usage.values()),
                observed_usage=dict(self.observed_usage),
                verified=True, proof=dict(source="native_dispatch_receipts", requests=self.receipt_count,
                                          dispatches=self.dispatched,
                                          model_routes=len(self.identities), mixed_routes=self.mixed_routes,
                                          incomplete_requests=self.incomplete_requests,
                                          component_first_input_tokens=self.first_input_tokens,
                                          owner_verified=True, owner_conversation_ref=self.ref)))
            sample.update(source_kind="conversation", ownership="verified_native_owner",
                          source_conversation_ref=self.ref)
            sample["model_key"] = digest(sample.get("model_contract", {}))
            from secretary.adaptive_runtime import record_event
            record_event(self.db, self.ref, config=self.config, **sample)


def start(parent, component, operation_id, **kwargs):
    try:
        return Collector(parent, component, operation_id, **kwargs)
    except Exception:
        logger.debug("Adaptive maintenance start unavailable", exc_info=True)
        return None


def finish(collector, outcome, **kwargs):
    try:
        if collector is not None:
            collector.finish(outcome, **kwargs)
    except Exception:
        logger.debug("Adaptive maintenance settlement unavailable", exc_info=True)


@contextmanager
def scope(collector):
    token = _active.set(collector if collector is not None and collector.enabled else None)
    try:
        yield
    finally:
        _active.reset(token)


def auxiliary_receipt(response=None, error=None, **route):
    """Called at the existing physical auxiliary relay, including failed attempts."""
    try:
        collector = _active.get()
        if collector is not None and route.get("aux_task") == "compression":
            collector.receipt(response, failed=error is not None,
                              **{key: route.get(key) for key in ("provider", "model", "api_mode", "streaming")})
    except Exception:
        logger.debug("Adaptive auxiliary receipt unavailable", exc_info=True)


def native_publication(parent, commit):
    """Fail-open numeric observation at the existing successful publication site."""
    try:
        collector = _active.get()
        if collector is not None and collector.enabled:
            collector.native_publication(parent, commit)
    except Exception:
        logger.debug("Adaptive native publication observation unavailable", exc_info=True)


def auxiliary_dispatch(aux_task):
    try:
        collector = _active.get()
        if collector is not None and aux_task == "compression":
            collector.dispatch()
    except Exception:
        logger.debug("Adaptive auxiliary dispatch unavailable", exc_info=True)


def child_dispatch(child):
    try:
        collector = getattr(child, "_adaptive_maintenance_collector", None)
        if collector is not None:
            collector.dispatch()
    except Exception:
        logger.debug("Adaptive child dispatch unavailable", exc_info=True)


def child_receipt(child, response=None, canonical=None, *, failed=False):
    try:
        collector = getattr(child, "_adaptive_maintenance_collector", None)
        if collector is not None:
            collector.receipt(response, canonical=canonical, failed=failed,
                              provider=getattr(child, "provider", None), model=getattr(child, "model", None),
                              api_mode=getattr(child, "api_mode", None))
    except Exception:
        logger.debug("Adaptive child receipt unavailable", exc_info=True)
