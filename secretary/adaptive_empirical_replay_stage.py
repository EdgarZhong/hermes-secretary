"""Frozen V3 scenario preparation; no policy import, simulation or host access."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from secretary.adaptive_empirical_replay_data import file_sha, read_json


SCENARIOS = (
    ("S01", "连续上升／密集工作", ["E01", "E04"], "保护同轮真实工作，不因context大抢整理", "historical"),
    ("S02", "四分钟短返", ["E02"], "hot观察且不整理，不把一次Main结束当长离开", "historical"),
    ("S03", "逐渐确认长离开", ["E06"], "不能恰30分钟预约保护到点维护；沿实际Main边界随新证据重评", "historical"),
    ("S04", "中等存量低读取", ["E03"], "保留原约5h亏损及预存6h／24h／共同末点，不事后延窗求PASS", "historical"),
    ("S05", "夜间后台自增", ["E05"], "HB与Reminder不是真人；夜间不硬编码无人，费用增长有解释", "historical"),
    ("S06", "高存量长期低使用", ["E06", "E08", "E09"], "可完成且有收益的长空档及时维护；昂贵分支保留负结果", "historical"),
    ("S07", "用户回归", ["E07"], "真人回归使旧维护计划失效，连续旅程沿自有context继续", "historical"),
    ("S08", "第二次维护边际收益", ["JOURNEY"], "独立核第二次费用及后续净省，不用总旅程盈利掩盖多余维护", "historical"),
    ("S09", "整理前后HB冷热成本翻转", ["M-CACHE"], "完整四桶及整轮输出共同计价；整理后重新选择，不写死business", "declared_mechanism"),
    ("S10", "临近已知Instant", ["A08-CONDITIONAL"], "按14:50已知16:00约69m排期比较hot接力与立即整理，另列原生事实", "historical_timing_conditional_contract"),
    ("S11", "长Noting及反向慢尾", ["M-DURATION"], "规划max完整任务，Main阻挡另记；11/8 forced拥塞不是正常成功配对", "historical_component_plus_mechanism"),
    ("S12", "无后续读取", ["M01"], "无读取收益不为整理而整理，无真实完整分支不得称历史实测", "declared_mechanism"),
    ("S13", "高费／失败／取消／未知", ["M-FAILURE"], "已付费用保留，失败不缩context，Stop仅由共享真实外部事件触发", "historical_components_plus_mechanism"),
    ("S14", "已登记切模型", ["M-REGISTERED"], "按新合同重算并继承行为；数据不足hot，导入后立即用而非等新真人", "declared_mechanism"),
    ("S15", "未登记切模型", ["A08-NATIVE"], "允许原生10800秒；不能称算法主动选择低频或伪造Kimi登记价", "observed_native_control"),
    ("S16", "观察缺口／迟到／截尾", ["M-KNOWLEDGE"], "不把未知当无人，不看未来排期，窗口外维护及费用全结算", "historical_gaps_plus_mechanism"),
)


def scenario_contract(legacy_path, afternoon_path):
    """The caller writes this result before it can start candidate execution."""
    return dict(version="stage-expectations-v1", candidate_runs=0,
                sources={"legacy_input": dict(path=str(legacy_path), sha256=file_sha(legacy_path)),
                         "afternoon": dict(path=str(afternoon_path), sha256=file_sha(afternoon_path))},
                scenarios=[dict(id=i, name=n, cases=c, expected=e, evidence_level=l) for i, n, c, e, l in SCENARIOS],
                comparison=dict(policies=["old-online", "V2", "simple-stage", "V3"], seed=2,
                                windows=["original", "6h", "24h", "common-cutoff"],
                                history_decay_days=[3, 7, 14], initial_state="shared_per_case",
                                costs="same_external_demand_prices_seed_end; each_policy_owns_context_cache_anchor"),
                acceptance="root whole-segment qualitative review; no averaging away negative cases")


def schedule_witnesses(afternoon):
    rows = []
    for witness in afternoon["schedule_tool_witnesses"]:
        schedule = witness["schedule"]
        if not witness.get("success") or schedule.get("delivery_mode") != "instant":
            continue
        due = datetime.fromisoformat(schedule["next_due_at"]).timestamp()
        rows.append(dict(schedule_id=schedule["schedule_id"], due_at=due, available_at=witness["at"],
                         source="successful_schedule_tool_message", source_message_id=witness["message_id"],
                         enabled=schedule.get("state") == "active"))
    return rows


def prepare_stage(legacy_path, afternoon_path, expectations_path):
    """Prepare old phases plus a separately labelled afternoon counterfactual."""
    expected = read_json(expectations_path)
    for name, path in (("legacy_input", legacy_path), ("afternoon", afternoon_path)):
        if expected["sources"][name]["sha256"] != file_sha(path):
            raise ValueError("Expectation source changed: " + name)
    if expected.get("candidate_runs") != 0 or len(expected.get("scenarios", [])) != 16:
        raise ValueError("Expected a frozen, pre-candidate 16-scenario contract")
    legacy, afternoon = read_json(legacy_path), read_json(afternoon_path)
    historical = deepcopy(legacy)
    historical.update(version="stage-historical-v1", expectation_contract_sha256=file_sha(expectations_path),
                      scenario_contract=expected, historical_input_sha256=file_sha(legacy_path))
    # Original package declared known schedules but had no registration receipts.
    # Retain that condition explicitly, never silently upgrading it to fact.
    first = min(c["start"] for c in legacy["cases"])
    historical["reminder_schedule"] = [dict(schedule_id=j["id"], due_at=j["start"], available_at=first,
        source="legacy_declared_known_schedule_not_registration_evidence") for j in legacy["jobs"] if j["source"] == "reminder"]
    historical["reminder_schedule_known_from"] = first
    historical["assumptions"].append("V3 retains the old known-schedule condition explicitly; original registrations are absent.")
    historical["assumptions"].append("Original 9 phases overlap; they are not independent behavioral experiments.")
    return dict(historical=historical, afternoon=afternoon_counterfactual(historical, afternoon, expected),
                observed_afternoon=dict(evidence_level="observed_native_only", source_sha256=file_sha(afternoon_path),
                    registered_kimi=False, native_interval_seconds=10800,
                    reminder_schedule=schedule_witnesses(afternoon),
                    requests=afternoon["requests"], turns=afternoon["turns"],
                    gaps=["no_registered_Kimi_prices", "no_full_coverage", "no_observed_hot_bridge_counterfactual"],
                    interpretation="request_buckets_are_observed; no_policy_economic_choice_or_realized_savings_claim"))


def afternoon_counterfactual(historical, afternoon, expected):
    """Historical timings with an explicit GPT-priced proxy; never a Kimi bill."""
    value = deepcopy(historical)
    events = []
    key = historical["snapshot"].get("model_key")
    for turn in afternoon["turns"]:
        if not turn.get("end_at"):
            continue
        requests = [r for r in afternoon["requests"] if r["turn_start_at"] == turn["start_at"]]
        if not requests:
            continue
        source = "heartbeat" if turn.get("source_marker") == "heartbeat" else "reminder" if turn.get("source_marker") == "instant_reminder" else "user"
        identity = "afternoon-turn:" + str(turn["start_at"])
        for index, row in enumerate(requests):
            events.append(dict(kind="request", event_id=identity+":"+str(index), turn_id=identity,
                               source=source, verified=True, at=row["at"], available_at=row["at"],
                               input_tokens=row["input_total"], cache_read_tokens=row["cache_read"],
                               cache_write_tokens=0, output_tokens=row["output"], model_key=key,
                               input_semantics="total", context_epoch="afternoon-conditional",
                               evidence_level="observed_Kimi_buckets_target_contract_proxy"))
        events.append(dict(kind="turn_end", event_id="turn:"+identity, turn_id=identity, source=source,
                           verified=True, at=turn["end_at"], available_at=turn["end_at"], model_key=key,
                           duration_seconds=turn["end_at"]-turn["start_at"], context_tokens=requests[-1]["input_total"],
                           context_epoch="afternoon-conditional"))
    for row in afternoon["messages"]:
        if row.get("has_client_submission") or row.get("has_gateway_input_owner"):
            events.append(dict(kind="user_activity", event_id="afternoon-input:"+str(row["id"]),
                               source="user", verified=True, at=row["at"], available_at=row["at"]))
    from secretary.adaptive_empirical_replay_data import _jobs
    value["events"] = historical["events"] + events
    value["jobs"] = historical["jobs"] + _jobs(events)
    value["cutoff"] = max(j["end"] for j in value["jobs"])
    start = next(t["end_at"] for t in afternoon["turns"] if t["time"].startswith("2026-11-08T14:50"))
    reminder = next(t for t in afternoon["turns"] if t["source_marker"] == "instant_reminder")
    anchor = max(t["start_at"] for t in afternoon["heartbeats"] if t["start_at"] < start)
    value["cases"] = [dict(id="A08-CONDITIONAL", name="11/8已登记合同条件反事实", start=start,
                           end=reminder["end_at"]+.001, expectation_type="known_reminder_bridge",
                           expected=expected["scenarios"][9]["expected"], initial_state=dict(context=176496,
                           epoch="afternoon-conditional", heartbeat_anchor=anchor, mode="business"),
                           evidence_level="real_timing_declared_GPT_contract_and_coverage_condition")]
    value["reminder_schedule"] = schedule_witnesses(afternoon)
    value.pop("reminder_schedule_known_from", None)
    value["version"] = "stage-afternoon-conditional-v1"
    value["assumptions"] += [
        "Afternoon historical Kimi timings/work increments are priced with frozen GPT config, NOT registered Kimi prices or observed savings.",
        "Independent 14:50 entry inherits observed 13:35 heartbeat anchor: switching hot makes overdue work immediately due once, never reanchors at 14:50.",
        "Continuous pre-registered-hot scenario requires a separately simulated earlier start; do not copy the independent entry anchor to it.",
        "No new submission/request observed in the log window is NOT full coverage. Coverage below is a declared counterfactual condition.",
        "Bridge cache hits use the target TTL/prefix proxy; observed 175297 fresh tokens are not all claimed recoverable.",
        "Legacy samples are known as historical settled components, with no new production import implied.",
    ]
    value["events"].append(dict(kind="coverage", event_id="afternoon-declared-coverage", source="user", verified=True,
                               at=value["cutoff"], start_at=start, end_at=value["cutoff"],
                               evidence_level="declared_continuous_host_condition_not_observed_full_coverage"))
    return project_declared_contract(value)


def project_declared_contract(package):
    """Complete the already declared target projection without rewriting facts.

    Only the observed afternoon workload proxy is projected. Ordinary historical
    events keep their real contracts; the returned package is a new derivative.
    """
    from secretary.adaptive_model_config import digest
    from secretary.adaptive_empirical_replay_data import _jobs
    from secretary.adaptive_features import number
    value = deepcopy(package)
    contract = value['config']['model_contract']
    identity = {key: contract[key] for key in ('provider', 'model')}
    key = digest(contract)
    projected = [r for r in value['events'] if r.get('evidence_level') == 'observed_Kimi_buckets_target_contract_proxy']
    turns = {r['turn_id'] for r in projected}
    ends = {r.get('turn_id') for r in value['events'] if r.get('kind') == 'turn_end'}
    for row in projected:
        if row['turn_id'] not in ends or any(number(row.get(k)) is None for k in
                ('input_tokens', 'cache_read_tokens', 'cache_write_tokens', 'output_tokens')):
            raise ValueError('Declared workload projection lacks its completed Turn or observed usage')
        row.setdefault('outcome', 'observed')
    for row in value['events']:
        if row.get('turn_id') in turns and row['kind'] in ('request', 'turn_end'):
            row.update(model_key=key, model_contract=deepcopy(contract), model_identity=identity,
                       contract_provenance='declared_counterfactual_target_not_original_Kimi_identity')
    value['snapshot']['model_key'] = key
    value['jobs'] = _jobs(value['events'])
    value['contract_projection'] = dict(source='observed_Kimi_buckets_target_contract_proxy',
        projected_turns=len(turns), target_identity=identity,
        changes='complete_request_outcome_and_consistent_request_turn_contract; times_and_usage_unchanged')
    return value
