"""Deterministic event simulator, separate from the policy's expectation model.

Synthetic workloads are not production savings evidence. External demand and
arrival timestamps are shared; each policy generates its own heartbeat traffic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math
import time

from secretary.adaptive_policy import decide
from secretary.adaptive_features import context_growth


@dataclass
class Scenario:
    name: str
    start: float
    hours: float = 12
    initial_context: int = 330000
    users: list[tuple[float, int]] = field(default_factory=list)
    reminders: list[float] = field(default_factory=list)
    actual_ttl: float = 1860
    cache_fraction: float = 1.0
    hb_output: int = 160
    hb_fresh: int = 256
    maintenance_duration: float = 600
    maintenance_cost: float = 90000
    retained_ratio: float = .18
    failure_every: int = 0
    cancel_on_collision: bool = False
    native_threshold: int = 440000


class Simulation:
    def __init__(self, scenario, config, training, policy='adaptive', *, threshold=98304, delay=1800):
        self.scenario, self.config, self.policy = scenario, config, policy
        self.threshold, self.delay = threshold, delay
        self.now, self.context = scenario.start, float(scenario.initial_context)
        self.end = scenario.start + scenario.hours * 3600
        self.history = list(training)
        self.mode, self.anchor = ('hot' if policy.startswith('hot') else 'business'), self.now
        self.epoch = 0
        self.last_request, self.last_input, self.last_maintenance = None, 0.0, None
        self.idle_due, self.idle_threshold, self.maintenance = None, None, None
        self.pending, self.queue = [], []
        self.busy_until = self.now
        self.cost, self.context_hours = 0.0, 0.0
        self.counts = dict(user=0, heartbeat=0, reminder=0, maintenance=0, native=0,
                           failed=0, cancelled=0, collisions=0)
        self.waits, self.decision_seconds, self.decisions = [], [], []
        self.maintenance_waits = {'idle': [], 'auto': []}
        self.maintenance_collisions = {'idle': 0, 'auto': 0}
        self.coverage_start = min((e.get('start_at', self.now) for e in training
                                   if e.get('kind') == 'coverage'), default=self.now)
        self.counter = 0
        for index, (offset, growth) in enumerate(scenario.users):
            heapq.heappush(self.queue, (scenario.start + offset, 0, 'user', (index, growth)))
        for index, offset in enumerate(scenario.reminders):
            heapq.heappush(self.queue, (scenario.start + offset, 1, 'reminder', (index, 0)))

    def _event(self, kind, **data):
        self.counter += 1
        self.history.append(dict(event_id=f'sim-{self.counter}', at=self.now, kind=kind,
                                 verified=True, model_key='test', **data))

    def _request(self, source, growth=0):
        cached = 0
        if self.last_request is not None and self.now - self.last_request < self.scenario.actual_ttl:
            reusable = min(self.context, self.last_input) * self.scenario.cache_fraction
            cached = math.floor(reusable / 256) * 256
        fresh = self.scenario.hb_fresh if source == 'heartbeat' else max(growth // 2, 100)
        output = self.scenario.hb_output if source == 'heartbeat' else max(growth // 2, 100)
        total = self.context + fresh
        self.cost += total - cached + cached * self.config['cache_ratio'] + output * self.config['output_ratio']
        self._event('request', source=source, input_tokens=total,
                    cache_read_tokens=cached, output_tokens=output)
        self.context += fresh + output
        self.last_request, self.last_input = self.now, total
        self.counts[source] += 1

    def _heartbeat_due(self):
        interval = self.config['hot_interval_seconds'] if self.mode == 'hot' else self.config.get('business_interval_seconds')
        return self.anchor + interval if interval is not None else math.inf

    def _plan(self, *, record_turn=True):
        if record_turn:
            self._event('turn_end', source='unknown', context_tokens=self.context, context_epoch=str(self.epoch))
        if record_turn and self.context >= self.scenario.native_threshold:
            self._start_maintenance(native=True)
            return
        if self.policy != 'adaptive':
            self.idle_threshold = None if self.policy.endswith('none') else self.threshold
            self.idle_due = self.now + self.delay if self.idle_threshold is not None else None
            if self.policy.endswith('guarded'):
                self._guard_fixed_plan()
            return
        self.history = [e for e in self.history if e.get('event_id') != 'sim-coverage']
        self.history.append(dict(event_id='sim-coverage', at=self.now, kind='coverage', source='user',
                                 verified=True, start_at=self.coverage_start, end_at=self.now))
        future = [at for at, _, kind, _ in self.queue if kind == 'reminder']
        snapshot = dict(now=self.now, context_tokens=int(self.context), context_limit=512000,
                        heartbeat_mode=self.mode, heartbeat_status='active', heartbeat_anchor=self.anchor,
                        heartbeat_next_due=self._heartbeat_due(), idle_enabled=True, model_key='test',
                        next_reminder_at=min(future, default=None), reminder_due_times=future,
                        last_maintenance_at=self.last_maintenance, maintenance_running=False)
        started = time.perf_counter()
        result = decide(snapshot, self.history, self.config)
        self.decision_seconds.append(time.perf_counter() - started)
        self.decisions.append(dict(at=self.now, **result))
        if result.get('fallback'):
            self.idle_threshold, self.idle_due = self.threshold, self.now + self.delay
        else:
            self.mode = result['mode']
            self.idle_threshold = result['threshold_tokens']
            self.idle_due = self.now + result['delay_seconds'] if result['delay_seconds'] is not None else None

    def _guard_fixed_plan(self):
        users = [e['at'] for e in self.history if e.get('kind') == 'user_activity' and e.get('source') == 'user']
        recent = sum(e.get('kind') == 'maintenance_start' and e.get('trigger') == 'idle'
                     and e['at'] > self.now - 86400 for e in self.history)
        growth = context_growth(self.history)
        if (recent >= self.config.get('max_maintenance_per_day', 2)
                or self.last_maintenance is not None and self.now - self.last_maintenance < self.config.get('min_maintenance_interval_seconds', 14400)
                or growth is not None and growth > self.config.get('max_growth_tokens_per_second', 50)):
            self.idle_due = None
        elif users:
            self.idle_due = max(self.idle_due, max(users) + self.config.get('min_user_quiet_seconds', 1800))

    def _start_maintenance(self, *, native=False):
        self.idle_due = None
        self.counts['maintenance'] += 1
        if native:
            self.counts['native'] += 1
        operation = f"maintenance-{self.counts['maintenance']}"
        self.maintenance = dict(operation_id=operation, start=self.now, before=self.context,
                                end=self.now + self.scenario.maintenance_duration,
                                trigger='auto' if native else 'idle', blocked={})
        self.cost += self.scenario.maintenance_cost
        self._event('maintenance_start', source='framework', operation_id=operation,
                    trigger=self.maintenance['trigger'], context_before=self.context)
        # Explicit synthetic aggregate invoice; this is not a production usage record.
        self._event('request', source='framework', operation_id=operation,
                    input_tokens=self.scenario.maintenance_cost, cache_read_tokens=0, output_tokens=0)

    def _finish_maintenance(self, *, cancelled=False):
        operation = self.maintenance
        self.maintenance_waits[operation['trigger']].extend(
            self.now - at for at in operation['blocked'].values())
        failed = bool(self.scenario.failure_every and self.counts['maintenance'] % self.scenario.failure_every == 0)
        outcome = 'cancelled' if cancelled else ('failed' if failed else 'completed')
        if cancelled:
            self.counts['cancelled'] += 1
            self._event('cancel', source='user', operation_id=operation['operation_id'],
                        trigger=operation['trigger'], outcome='cancelled')
        elif failed:
            self.counts['failed'] += 1
        else:
            self.context = max(12000, self.context * self.scenario.retained_ratio)
            self.epoch += 1
            self.last_request, self.last_input = None, 0
        self._event('maintenance_end', source='framework', operation_id=operation['operation_id'],
                    trigger=operation['trigger'], outcome=outcome,
                    context_before=operation['before'], context_after=self.context,
                    duration_seconds=self.now - operation['start'], usage_complete=True)
        self.last_maintenance = self.now
        self.maintenance, self.idle_due = None, None
        # Policy refresh may change mode, but must not rearm the consumed Idle period.
        self._plan(record_turn=False)
        self.idle_due = None

    def _external(self, kind, work, arrived, *, observe=True):
        if kind == 'user' and observe:
            self._event('user_activity', source='user')
        if self.maintenance:
            if kind == 'user':
                self.counts['collisions'] += 1
                self.maintenance_collisions[self.maintenance['trigger']] += 1
                self.maintenance['blocked'].setdefault(work[0], self.now)
                self._event('blocked_send', source='user', operation_id=self.maintenance['operation_id'],
                            trigger=self.maintenance['trigger'])
                if self.scenario.cancel_on_collision:
                    self._finish_maintenance(cancelled=True)
                else:
                    self.pending.append((kind, work, arrived))
                    return
            else:
                self.pending.append((kind, work, arrived))
                return
        if self.now < self.busy_until:
            self.pending.append((kind, work, arrived))
            return
        self.waits.append(self.now - arrived) if kind == 'user' else None
        self.idle_due = None
        self._request(kind, work[1])
        self.busy_until = self.now + (60 if kind == 'user' else 15)

    def _next_time(self):
        choices = [self.queue[0][0] if self.queue else math.inf]
        if self.maintenance:
            choices.append(self.maintenance['end'])
        elif self.busy_until > self.now:
            choices.append(self.busy_until)
        else:
            if self.pending:
                choices.append(self.now)
            if self.now < self.end:
                choices.extend([max(self.now, self._heartbeat_due()), self.idle_due or math.inf, self.end])
        return min(choices)

    def run(self):
        self._plan(record_turn=False)
        for _ in range(20000):
            at = self._next_time()
            if not math.isfinite(at):
                break
            self.context_hours += self.context * max(0, min(at, self.end) - self.now) / 3600
            finished_main = self.busy_until > self.now and at >= self.busy_until
            self.now = at
            if self.maintenance and self.maintenance['end'] <= self.now:
                self._finish_maintenance()
            # Real work takes priority at exact maintenance/Idle/HB boundaries.
            while self.queue and self.queue[0][0] <= self.now:
                arrived, _, kind, work = heapq.heappop(self.queue)
                self._external(kind, work, arrived)
            if self.maintenance or self.now < self.busy_until:
                continue
            if self.pending:
                kind, work, arrived = self.pending.pop(0)
                self._external(kind, work, arrived, observe=False)
                continue
            if finished_main:
                self._plan()
            if self.now >= self.end:
                break
            if self.idle_due is not None and self.idle_due <= self.now:
                self.idle_due = None
                if self.idle_threshold is not None and self.context >= self.idle_threshold:
                    self._start_maintenance()
                    continue
            if self._heartbeat_due() <= self.now:
                self.anchor, self.idle_due = self.now, None
                self._request('heartbeat')
                self.busy_until = self.now + 15
        else:
            raise RuntimeError('Simulation failed to converge')
        if self.pending or self.queue:
            raise RuntimeError('Unsettled external work at comparison end')
        return dict(scenario=self.scenario.name, policy=self.policy, input_equivalent_cost=self.cost,
                    terminal_cold_read_stress=self.cost + self.context, context_token_hours=self.context_hours,
                    max_wait_seconds=max(self.waits, default=0), total_wait_seconds=sum(self.waits),
                    maintenance_wait_seconds={key: sum(values) for key, values in self.maintenance_waits.items()},
                    maintenance_collisions=self.maintenance_collisions,
                    final_context=self.context, counts=self.counts,
                    max_decision_seconds=max(self.decision_seconds, default=0),
                    decision_count=len(self.decisions))
