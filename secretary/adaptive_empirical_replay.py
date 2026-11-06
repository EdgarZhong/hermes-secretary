"""Chronological execution of the real policy against fixed historical demand.

This is an explicitly conditional counterfactual, never an observed savings
claim. The policy receives no future queue and owns its state after divergence.
"""
from __future__ import annotations

from copy import deepcopy
import heapq
import importlib
import math
from statistics import median
import time

from secretary.adaptive_empirical_replay_data import coverage_at, past_events


class Replay:
    def __init__(self, package, case, policy, *, variant="base", component_pool="all", seed=2,
                 comparison_end=None):
        self.package, self.case, self.policy = package, case, policy
        self.cfg, self.snapshot_base = deepcopy(package["config"]), deepcopy(package["snapshot"])
        self.variant, self.pool, self.seed = variant, component_pool, seed
        if variant == "whole_invoice":
            self.cfg["_maintenance_scale_mode"] = "whole_invoice"
        if variant == "short_cache":
            self.cfg["cache_ttl_seconds"] /= 2
        self.now = case["start"]
        self.end = min(comparison_end if comparison_end is not None else case["end"], package["cutoff"])
        self.history = past_events(package, self.now)
        if component_pool != "all":
            self.history = [r for r in self.history if self._in_pool(r)]
        previous = [j for j in package["jobs"] if j["end"] <= self.now]
        following = [j for j in package["jobs"] if j["end"] > self.now]
        last = max(previous, key=lambda j: j["end"]) if previous else None
        self.initial_completed_turn_at = last["end"] if last else None
        first = min(following, key=lambda j: j["start"]) if following else None
        changed = bool(last and first and last["epoch"] != first["epoch"])
        self.context = first["first_input"] if changed else last["context_tokens"] if last else self.snapshot_base["context_tokens"]
        self.epoch = first["epoch"] if changed else last["epoch"] if last else "replay-initial"
        self.last_request = max((r["at"] for r in self.history if r["kind"] == "request"), default=None)
        self.template_pool = {s: [j for j in previous if j["source"] == s][-12:]
                              for s in ("user", "heartbeat", "reminder", "unknown")}
        decisions = [r for r in package["events"] if r["kind"] == "decision" and r["at"] <= self.now]
        self.mode = decisions[-1]["decision"]["mode"] if decisions else "business"
        if variant == "initial_hot":
            self.mode = "hot"
        hb = [j["start"] for j in previous if j["source"] == "heartbeat"]
        self.anchor = max(hb) if hb else self.now
        self.cost, self.serial, self.generation, self.hb_generation = 0.0, 0, 0, 0
        self.busy_until, self.pending, self.running, self.recovery = self.now, None, None, 0.0
        self.queue, self.decisions, self.actions, self.waits, self.states = [], [], [], [], []
        self.counts = dict(heartbeat=0, reminder=0, user=0, unknown=0, maintenance=0, completed=0, failed=0, collisions=0)
        self.seconds, self.operation_index, self.maximum_events = [], 0, 50000
        self.initial_context = self.context
        self.maximum_context = self.context
        self.known_arrival_ids = {r["event_id"] for r in package["events"] if r["kind"] == "user_activity"}
        self.colliding_arrivals = set()
        self.waiting_collisions = {}
        self._prepare_queue()

    def _in_pool(self, row):
        if row.get("kind") != "maintenance_sample":
            return True
        if self.pool == "gpt-only":
            identity = row.get("model_identity", {})
            current = self.cfg.get("model_identity", {})
            return bool(current.get("provider") and current.get("model")
                        and all(identity.get(key) == current[key] for key in ("provider", "model")))
        return row.get("proof", {}).get("source_conversation_evidence") in {
            "same_target_binding", "same_target_parent_chain"}

    def _push(self, at, kind, value=None):
        priority = {"arrival": 0, "maintenance_end": 1, "turn_end": 2, "external": 3,
                    "maintenance_due": 4, "heartbeat": 5}[kind]
        self.serial += 1
        heapq.heappush(self.queue, (at, priority, self.serial, kind, value))

    def _prepare_queue(self):
        for row in self.package["events"]:
            if row["kind"] == "user_activity":
                at = max(row["at"], row.get("available_at", row["at"]))
                if self.now <= at < self.end:
                    self._push(at, "arrival", row)
        for job in self.package["jobs"]:
            if job["source"] != "heartbeat" and self.now <= job["start"] < self.end:
                self._push(job["start"], "external", job)
            elif job["source"] != "heartbeat" and job["start"] < self.now < job["end"]:
                partial = dict(job, duration=job["end"] - self.now, calls=0, growth_tokens=0,
                               first_suffix_tokens=0, output_tokens=0,
                               partial_initial_job="already_running_initial_cost_sunk")
                self._push(self.now, "external", partial)
        self._schedule_hb()

    def _interval(self):
        key = "hot_interval_seconds" if self.mode == "hot" else "business_interval_seconds"
        return self.cfg.get(key)

    def _schedule_hb(self):
        self.hb_generation += 1
        interval = self._interval()
        if interval is not None:
            self._push(max(self.now, self.anchor + interval), "heartbeat", self.hb_generation)

    def _observe(self, row):
        self.history.append(row)

    def _known_history(self):
        self.history = [r for r in self.history if r["kind"] != "coverage"]
        if self.variant == "raw_coverage_only":
            self.history.extend(deepcopy(r) for r in self.package["events"] if r["kind"] == "coverage"
                                and max(r["at"], r.get("available_at", r["at"])) <= self.now)
        else:
            self.history.extend(coverage_at(self.package["events"], self.now))
        identities = {r["event_id"] for r in self.history}
        for row in self.package["maintenance_samples"]:
            if row["event_id"] not in identities and max(row["at"], row.get("available_at", row["at"])) <= self.now:
                if self.pool == "all" or self._in_pool(row):
                    self.history.append(deepcopy(row))
        self.history.sort(key=lambda row: (row["at"], row["event_id"]))
        return self.history[-2048:]

    def _snapshot(self):
        snap = deepcopy(self.snapshot_base)
        reminders = [j["start"] for j in self.package["jobs"]
                     if j["source"] == "reminder" and self.now <= j["start"] < self.end]
        known = self.variant != "unknown_reminders"
        interval = self._interval()
        snap.update(now=self.now, context_tokens=self.context, context_epoch=self.epoch,
                    heartbeat_mode=self.mode, heartbeat_interval_seconds=interval,
                    heartbeat_anchor=self.anchor, heartbeat_next_due=self.anchor + interval if interval else None,
                    heartbeat_status="active", current_mode_native=False,
                    next_reminder_known=known, next_reminder_at=min(reminders) if known and reminders else None,
                    reminder_due_times=reminders if known else [], maintenance_running=self.running is not None,
                    idle_enabled=True, last_maintenance_at=max((a["at"] for a in self.actions if a["kind"] == "maintenance_end"), default=None))
        return snap

    def _decision(self, *, mode_only=False):
        snapshot, history = self._snapshot(), self._known_history()
        started = time.perf_counter()
        decision = self.policy.decide(snapshot, history, self.cfg)
        elapsed = time.perf_counter() - started
        self.seconds.append(elapsed)
        self.decisions.append(dict(at=self.now, context=self.context, decision=decision, elapsed_seconds=elapsed,
                                   adoption="mode_only" if mode_only else "main_end_plan",
                                   visible_event_max=max((max(r["at"], r.get("available_at", r["at"])) for r in history), default=None)))
        if not decision.get("fallback"):
            self.mode = decision["mode"]
        return snapshot, history, decision

    def _plan(self):
        snapshot, history, decision = self._decision()
        self.generation += 1
        self.pending = None
        if not decision.get("fallback"):
            if decision.get("delay_seconds") is not None and decision.get("threshold_tokens") is not None:
                cfg = self.policy._settings(self.cfg)
                features = self.policy.build_features(snapshot, history, cfg)
                features["pricing_context_tokens"] = self.context
                profile = self.policy._maintenance(features, cfg)
                if profile is not None:
                    self.pending = dict(due=self.now + decision["delay_seconds"],
                                        threshold=decision["threshold_tokens"], generation=self.generation, profile=profile)
                    self._push(self.pending["due"], "maintenance_due", self.generation)
        self._schedule_hb()

    def _template(self, source):
        rows = self.template_pool.get(source, [])
        def estimate(key, fallback):
            values = [j[key] for j in rows if isinstance(j.get(key), (int, float))]
            return median(values) if values else fallback
        return dict(id="generated-hb:" + str(self.serial), source=source,
                    calls=max(1, round(estimate("calls", 1))),
                    growth_tokens=estimate("growth_tokens", self.cfg["heartbeat_fresh_tokens"]),
                    first_suffix_tokens=estimate("first_suffix_tokens", self.cfg["heartbeat_fresh_tokens"]),
                    output_tokens=estimate("output_tokens", self.cfg["heartbeat_output_tokens"]),
                    duration=estimate("duration", 30), template_source="past_completed_same_source_medians")

    def _work_values(self, job):
        template = self._template(job["source"])
        values = {key: job.get(key) if job.get(key) is not None else template[key]
                  for key in ("calls", "growth_tokens", "first_suffix_tokens", "output_tokens", "duration")}
        if self.variant == "suffix_double":
            values["first_suffix_tokens"] *= 2
        return values

    def _charge(self, job, values):
        calls, suffix, growth, output = (values[k] for k in ("calls", "first_suffix_tokens", "growth_tokens", "output_tokens"))
        if calls == 0:
            return []
        start_context = self.context
        rows = []
        previous = self.last_request
        for index in range(calls):
            at = self.now + values["duration"] * (index + 1) / calls
            prompt = start_context + suffix + growth * index / max(1, calls - 1)
            threshold = self.snapshot_base.get("native_threshold_tokens")
            if threshold and prompt >= threshold:
                raise ValueError("Native capacity reached; cannot claim an uncompressed counterfactual past this boundary")
            self.maximum_context = max(self.maximum_context, prompt)
            gap = at - previous if previous is not None else math.inf
            fraction = self.cfg["hot_cache_fraction"] if 0 <= gap < self.cfg["cache_ttl_seconds"] else 0
            cache = max(0, min(prompt, (start_context if index == 0 else prompt) * fraction))
            cost = prompt - cache + cache * self.cfg["cache_ratio"] + output / calls * self.cfg["output_ratio"]
            self.cost += cost
            rows.append(dict(event_id="replay-request:" + str(self.serial) + ":" + str(index), at=at,
                             kind="request", source=job["source"], verified=True, outcome="observed",
                             input_tokens=prompt, cache_read_tokens=cache, cache_write_tokens=0,
                             output_tokens=output / calls, input_semantics="total", turn_id=job["id"],
                             model_key=self.snapshot_base.get("model_key")))
            previous = at
        self.context += suffix + growth
        self.maximum_context = max(self.maximum_context, self.context)
        self.last_request = previous
        return rows

    def _start_job(self, job):
        if self.now >= self.end and job.get("start", self.now) >= self.end:
            return
        if self.now < self.busy_until:
            if self.running and job["source"] == "user" and job["id"] not in self.known_arrival_ids:
                self._record_collision()
            self._push(self.busy_until, "external", job)
            return
        self.generation += 1
        self.pending = None
        values = self._work_values(job)
        before_cost = self.cost
        if job["source"] == "user" and self.recovery:
            self.cost += self.recovery
            self.recovery = 0
        requests = self._charge(job, values)
        self.busy_until = self.now + values["duration"]
        self.counts[job["source"]] += 1
        self.actions.append(dict(kind="main_start", at=self.now, source=job["source"],
                                 id=job["id"], duration=values["duration"], context_after_work=self.context,
                                 cost=self.cost-before_cost, cumulative_cost=self.cost,
                                 unknown_work_fields=[key for key in values if job.get(key) is None]))
        self._push(self.busy_until, "turn_end", dict(job=job, values=values, requests=requests))

    def _finish_job(self, value):
        job, values = value["job"], value["values"]
        self.history.extend(value["requests"])
        self._observe(dict(kind="turn_end", source=job["source"], verified=True, at=self.now,
                           event_id="turn:" + job["id"], context_tokens=self.context, context_epoch=self.epoch,
                           model_key=self.snapshot_base.get("model_key"), duration_seconds=values["duration"]))
        self.template_pool.setdefault(job["source"], []).append(dict(job, **values, end=self.now))
        self.template_pool[job["source"]] = self.template_pool[job["source"]][-12:]
        self.states.append(dict(at=self.now, context=self.context, mode=self.mode, source=job["source"],
                                cumulative_cost=self.cost))
        if self.now < self.end:
            self._plan()

    def _draw(self, profile):
        rows = list(getattr(profile, "scenarios", ()) or [profile])
        # Explicit Stop is part of shared external demand. Sampling one without
        # a historical cancellation would fabricate a user action. Its receipt
        # stays in the policy's risk/cost evidence and in cancel sensitivities.
        rows = [p for p in rows if not (
            p.diagnostics.get("scenario", {}).get("outcome") == "cancelled"
            and p.diagnostics.get("scenario", {}).get("proof", {}).get("failure_class") == "explicit_interrupt")]
        if not rows:
            return None
        if self.variant == "mechanical_failure" and self.operation_index == 0:
            failures = [p for p in rows if p.diagnostics.get("scenario", {}).get("outcome") == "failed"]
            if failures:
                return max(failures, key=lambda p: p.duration)
            self.actions.append(dict(kind="stress_evidence_missing", at=self.now,
                                     reason="no_admissible_mechanical_failure_scenario"))
        rows.sort(key=lambda p: (p.cost, p.duration, p.retained))
        position = ((self.seed + self.operation_index) % 5 + .5) / 5
        weights = [p.diagnostics.get("weight", 1 / len(rows)) for p in rows]
        boundary = position * sum(weights)
        cumulative = 0
        for candidate, weight in zip(rows, weights):
            cumulative += weight
            if cumulative >= boundary:
                return candidate
        return rows[-1]

    def _start_maintenance(self, generation):
        plan = self.pending
        if not plan or generation != self.generation or self.now < self.busy_until or self.context < plan["threshold"]:
            return
        selected = self._draw(plan["profile"])
        if selected is None:
            self.pending = None
            self.actions.append(dict(kind="maintenance_not_executed", at=self.now,
                                     reason="only_explicit_user_cancel_scenarios_without_external_cancel"))
            return
        self.operation_index += 1
        duration = selected.duration * (2 if self.variant == "slow_block" else 1)
        expense = selected.cost * (2 if self.variant == "cost_double" else 1)
        outcome = selected.diagnostics.get("scenario", {}).get("outcome", "completed")
        cost_module = importlib.import_module("secretary.adaptive_cost")
        transfer = getattr(cost_module, "post_maintenance_context", None)
        # Older frozen policy roots retain their original ratio semantics.
        after = transfer(self.context, selected) if transfer else self.context * selected.retained
        retained = after / self.context if self.context > 0 else 1.0
        self.running = dict(id="replay-maintenance:" + str(self.operation_index), before=self.context,
                            retained=retained, after=after, outcome=outcome, cost=expense,
                            source=selected.diagnostics, duration=duration, started_at=self.now,
                            cancellation_profile=plan["profile"])
        self.cost += expense
        self.pending = None
        self.counts["maintenance"] += 1
        self.busy_until = self.now + duration
        self.actions.append(dict(kind="maintenance_start", at=self.now, context=self.context, duration=duration,
                                 cost=expense, retained=retained, context_after=after, outcome=outcome,
                                 cumulative_cost=self.cost,
                                 experience_timing_guard=self._timing_guard(),
                                 source=selected.diagnostics))
        self._observe(dict(event_id=self.running["id"] + ":start", kind="maintenance_start", source="framework",
                           verified=True, at=self.now, trigger="idle", operation_id=self.running["id"], idle=True))
        self._push(self.busy_until, "maintenance_end", dict(id=self.running["id"], recovery=selected.recovery))

    def _timing_guard(self):
        # This acceptance check deliberately uses all verified contracts. It
        # records a policy violation rather than silently blocking/correcting it.
        known = [r for r in self.history if r.get("verified") is True and r.get("source") == "user"
                 and max(r["at"], r.get("available_at", r["at"])) <= self.now]
        activity = max((r["at"] for r in known if r["kind"] == "user_activity"), default=None)
        work = max((r["at"] for r in known if r["kind"] == "turn_end"), default=None)
        anchors = [value for value in (activity, work) if value is not None]
        quiet = self.now-max(anchors) if anchors else None
        required = self.cfg.get("min_user_quiet_seconds", 1800)
        return dict(last_user_activity=activity, last_known_user_work_end=work,
                    actual_quiet_seconds=quiet, required_quiet_seconds=required,
                    satisfied=quiet >= required-1e-6 if quiet is not None else None,
                    contract="verified_work_end_cross_model_timing_only_not_workload_transfer")

    def _finish_maintenance(self, recovery):
        active = self.running
        for waiting in self.waiting_collisions.pop(active["id"], []):
            actual_wait = max(0, self.now-waiting["at"])
            self.waits[waiting["index"]] = actual_wait
            waiting["action"].update(wait_seconds=actual_wait, release_at=self.now, settled=True)
        self.context = active["after"]
        self.epoch = active["id"]
        self.last_request = None
        self.recovery = recovery
        key = "completed" if active["outcome"] in ("completed", "partial") else "failed"
        self.counts[key] += 1
        self.actions.append(dict(kind="maintenance_end", at=self.now, context=self.context, outcome=active["outcome"]))
        self._observe(dict(event_id=active["id"] + ":end", kind="maintenance_end", source="framework",
                           verified=True, at=self.now, operation_id=active["id"], outcome=active["outcome"],
                           context_before=active["before"], context_after=self.context,
                           duration_seconds=active["duration"], duration_scope="joint_main_block", usage_complete=False))
        self.running = None
        # Match runtime._maintenance: settle first, refresh only the HB mode,
        # then publish framework state. A consumed Idle never becomes a new plan.
        self._decision(mode_only=True)
        self._observe(dict(event_id=active["id"] + ":state_refresh", kind="state_refresh", source="framework",
                           verified=True, at=self.now, context_tokens=self.context, context_epoch=self.epoch,
                           model_key=self.snapshot_base.get("model_key")))
        self.states.append(dict(at=self.now, context=self.context, mode=self.mode, source="maintenance",
                                cumulative_cost=self.cost))
        # Retain the original anchor; queued user/Reminder Main remains ahead of HB.
        self._schedule_hb()

    def _record_collision(self):
        action = dict(kind="real_arrival_collision", at=self.now,
                      operation_id=self.running["id"], wait_seconds=max(0, self.busy_until-self.now), settled=False)
        self.counts["collisions"] += 1
        index = len(self.waits)
        self.waits.append(action["wait_seconds"])
        self.actions.append(action)
        self.waiting_collisions.setdefault(self.running["id"], []).append(
            dict(at=self.now, index=index, action=action))

    def _cancel_running(self):
        active = self.running
        if active is None:
            return
        elapsed = self.now - active["started_at"]
        cancellation = getattr(active["cancellation_profile"], "cancellation_scenarios", ())
        paid, source = active["cost"], "unknown_cancellation_cost_full_sampled_cost_proxy"
        if cancellation:
            nearest = min(cancellation, key=lambda p: (abs(p.duration - elapsed), -p.cost))
            helper = importlib.import_module("secretary.adaptive_rollout")._cancelled_cost
            paid = helper(active["cancellation_profile"], elapsed)
            if self.variant == "cost_double":
                paid *= 2
            source = nearest.diagnostics
            self.cost += paid - active["cost"]
        active.update(outcome="cancelled", retained=1.0, after=active["before"], duration=elapsed)
        self.busy_until = self.now
        self.actions.append(dict(kind="actual_user_cancel", at=self.now,
                                 operation_id=active["id"], paid_cost=paid,
                                 sampled_completion_cost_reference=active["cost"], cancellation_cost_source=source,
                                 cumulative_cost=self.cost))
        self._finish_maintenance(0)
        # Native Stop releases already waiting work; do not keep it asleep until
        # the old hypothetical finish. The outstanding periodic HB stays one due.
        self.queue = [(self.now if kind == "external" and value.get("start", at) <= self.now else at,
                       priority, serial, kind, value) for at, priority, serial, kind, value in self.queue]
        heapq.heapify(self.queue)

    def _dispatch(self, kind, value):
        if kind == "arrival":
            self._observe(deepcopy(value))
            self.generation += 1
            self.pending = None
            if value.get("activity") == "cancel":
                self._cancel_running()
            elif self.running is not None and value["event_id"] not in self.colliding_arrivals:
                self.colliding_arrivals.add(value["event_id"])
                self._record_collision()
        elif kind == "external":
            self._start_job(value)
        elif kind == "turn_end":
            self._finish_job(value)
        elif kind == "maintenance_due":
            self._start_maintenance(value)
        elif kind == "maintenance_end":
            if self.running is not None and self.running["id"] == value["id"]:
                self._finish_maintenance(value["recovery"])
        elif kind == "heartbeat" and value == self.hb_generation and self.now < self.end:
            if self.now < self.busy_until:
                self._push(self.busy_until, "heartbeat", value)
            else:
                self.anchor = self.now
                self._start_job(self._template("heartbeat"))

    def run(self):
        started = time.perf_counter()
        # The initial boundary represents the last real completed Main, never a
        # fabricated source submission. A case starting in a new epoch begins busy.
        active = [j for j in self.package["jobs"] if j["start"] <= self.now < j["end"] and j["source"] != "heartbeat"]
        at_real_boundary = self.initial_completed_turn_at is not None and 0 <= self.now - self.initial_completed_turn_at <= 1
        if not active and at_real_boundary:
            self._plan()
        for _ in range(self.maximum_events):
            if not self.queue:
                break
            at, _, _, kind, value = heapq.heappop(self.queue)
            accepted_external = kind == "external" and value.get("start", at) < self.end
            if at > self.end and kind not in ("turn_end", "maintenance_end") and not accepted_external:
                continue
            self.now = at
            self._dispatch(kind, value)
        else:
            raise RuntimeError("Replay event bound exhausted")
        return dict(case_id=self.case["id"], variant=self.variant, component_pool=self.pool, seed=self.seed,
                    start=self.case["start"], end=self.end, settled_at=self.now,
                    original_phase_end=self.case["end"],
                    initial_context=self.initial_context, final_context=self.context,
                    maximum_context=self.maximum_context,
                    native_capacity=dict(threshold=self.snapshot_base.get("native_threshold_tokens"),
                                         crossed=False, handling="bounded_replay_refuses_unsupported_native_overflow"),
                    input_equivalent_cost=self.cost, terminal_cold_read_stress=self.cost + self.context,
                    counts=self.counts, max_wait_seconds=max(self.waits, default=0), total_wait_seconds=sum(self.waits),
                    decisions=self.decisions, actions=self.actions, states=self.states,
                    elapsed_seconds=time.perf_counter() - started,
                    single_decision_seconds=dict(count=len(self.seconds), median=median(self.seconds) if self.seconds else None,
                                                 maximum=max(self.seconds, default=0)),
                    interpretation="conditional_policy_execution_not_realized_savings")
