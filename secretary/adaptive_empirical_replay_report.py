"""Whole-segment acceptance and opportunity evidence, separate from predictions."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


class FixedMode:
    """A declared comparator, not a replacement implementation of the policy."""
    def __init__(self, mode):
        self.mode = mode

    def decide(self, snapshot, history, config):
        return dict(mode=self.mode, threshold_tokens=None, delay_seconds=None, fallback=False,
                    reason="declared_fixed_mode_no_early_maintenance", diagnostics={})


def audit_case(case, result, comparators):
    maintenance = [a for a in result["actions"] if a["kind"] == "maintenance_start"
                   and case["start"] <= a["at"] < case["end"]]
    errors = []
    expectation = case["expectation_type"]
    if expectation in ("long_idle_opportunity", "whole_segment_opportunity") and not maintenance:
        errors.append("missed_whole_segment_maintenance_opportunity")
    if expectation in ("protect_active_batch", "protect_short_return") and maintenance:
        errors.append("maintenance_during_protected_real_work_or_short_gap")
    if any(row.get("experience_timing_guard", {}).get("satisfied") is False for row in maintenance):
        errors.append("insufficient_quiet_after_known_user_work_end")
    if any(d["visible_event_max"] is not None and d["visible_event_max"] > d["at"] for d in result["decisions"]):
        errors.append("future_information_visible")
    best_fixed = min(comparators, key=lambda r: r["input_equivalent_cost"]) if comparators else None
    saving = best_fixed["input_equivalent_cost"] - result["input_equivalent_cost"] if best_fixed else None
    if maintenance and expectation in ("long_idle_opportunity", "whole_segment_opportunity") and saving is not None and saving <= 0:
        errors.append("maintenance_did_not_improve_against_best_fixed_no_maintenance")
    checks = [dict(at=d["at"], context=d["context"], mode=d["decision"]["mode"],
                   threshold=d["decision"].get("threshold_tokens"), delay=d["decision"].get("delay_seconds"),
                   reason=d["decision"].get("reason"),
                   candidates=d["decision"].get("diagnostics", {}).get("candidate_evaluations", [])) for d in result["decisions"]]
    return dict(case_id=case["id"], expected=case["expected"], automated_status="counterexample" if errors else "needs_human_whole_segment_review",
                automatic_errors=errors, maintenance_starts=len(maintenance),
                observed_collision_count=result["counts"]["collisions"],
                conditional_saving_against_best_fixed=saving,
                best_fixed_mode=best_fixed.get("comparator") if best_fixed else None,
                decision_opportunity_audit=checks,
                acceptance_boundary="Positive automated checks do not replace root qualitative adjudication.")


def phase_projection(case, result):
    """Project one continuous journey; never reset its context at phase cuts."""
    def context(at):
        values = [row for row in result["states"] if row["at"] <= at]
        return values[-1]["context"] if values else result["initial_context"]
    def cost(at):
        values = [row for row in result["actions"] if row["at"] < at and "cumulative_cost" in row]
        return values[-1]["cumulative_cost"] if values else 0
    actions = [row for row in result["actions"] if case["start"] <= row["at"] < case["end"]]
    decisions = [row for row in result["decisions"] if case["start"] <= row["at"] < case["end"]]
    return dict(case_id=case["id"], start=case["start"], phase_end=case["end"],
                context_at_start=context(case["start"]), context_at_end=context(case["end"]),
                phase_input_equivalent_cost=cost(case["end"])-cost(case["start"]),
                maintenance_starts=[row for row in actions if row["kind"] == "maintenance_start"],
                maintenance_completions=[row for row in actions if row["kind"] == "maintenance_end"],
                background_counts={source: sum(row["kind"] == "main_start" and row["source"] == source for row in actions)
                                   for source in ("heartbeat", "reminder")},
                collisions=[row for row in actions if row["kind"] == "real_arrival_collision"],
                modes=[dict(at=row["at"], mode=row["decision"]["mode"], delay=row["decision"].get("delay_seconds")) for row in decisions],
                interpretation="inherited journey state; a previously shortened phase need not repeat an independent-case rewrite")


def summarize(report):
    zone = ZoneInfo("Asia/Shanghai")
    date = lambda t: datetime.fromtimestamp(t, zone).strftime("%m-%d %H:%M")
    lines = ["# 真实历史逐时策略回放", "", "本报告为声明条件下的动作执行模拟；不是实际节费或生产运行结果。经验预期SHA：`" + report["experience_sha256"] + "`。", "",
             "|案例|区间|维护/完成|HB|费用代理|对最佳固定档条件差额|自动反例|", "|---|---|---:|---:|---:|---:|---|"]
    for row in report["results"]:
        result, audit = row["candidate"], row["audit"]
        saving = audit["conditional_saving_against_best_fixed"]
        lines.append(f"|{result['case_id']}|{date(result['start'])}–{date(result['end'])}|{result['counts']['maintenance']}/{result['counts']['completed']}|{result['counts']['heartbeat']}|{result['input_equivalent_cost']:.1f}|{saving:.1f}|{', '.join(audit['automatic_errors']) or '待人逐段判断'}|")
    lines += ["", "自动失败保留；没有维护不通过合成正例豁免。高成本、慢占用、缓存与来源子集敏感性应分别报告，不能替换本报告基础情景。", "", "## 声明条件"]
    lines += ["", *["- " + item for item in report["assumptions"]]]
    return "\n".join(lines) + "\n"
