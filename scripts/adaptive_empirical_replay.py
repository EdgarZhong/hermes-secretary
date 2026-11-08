#!/usr/bin/env python3
"""Prepare audited inputs or replay the formal policy without host/network access."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from secretary.adaptive_empirical_replay import Replay  # noqa: E402
from secretary.adaptive_empirical_replay_data import file_sha, prepare, read_json  # noqa: E402
from secretary.adaptive_empirical_replay_report import FixedMode, SimpleStage, audit_case, phase_projection, summarize  # noqa: E402

RUNTIME_SHA = {str(path.relative_to(ROOT)): file_sha(path) for path in (
    Path(__file__).resolve(), ROOT / "secretary/adaptive_empirical_replay.py",
    ROOT / "secretary/adaptive_empirical_replay_data.py", ROOT / "secretary/adaptive_empirical_replay_report.py",
    ROOT / "secretary/adaptive_empirical_replay_stage.py")}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def policy_from_root(path):
    # Replay helpers are loaded first, but no adaptive policy/features/costs yet.
    # A fresh CLI process then resolves every formal policy dependency from the
    # same frozen source root. No current-module reuse in a baseline comparison.
    import secretary
    path = Path(path).resolve()
    loaded = [name for name in sys.modules if name.startswith("secretary.adaptive_") and "replay" not in name]
    if loaded:
        raise ValueError("Run in a fresh process; policy modules already loaded: " + ",".join(loaded))
    secretary.__path__ = [str(path / "secretary")]
    policy = importlib.import_module("secretary.adaptive_policy")
    if Path(policy.__file__).resolve() != path / "secretary/adaptive_policy.py":
        raise ValueError("Policy source root mismatch")
    return policy


def run(args):
    package = read_json(args.input)
    policy = policy_from_root(args.source_root)
    if args.simple_stage:
        policy = SimpleStage(policy)
    selected = [c for c in package["cases"] if not args.cases or c["id"] in args.cases.split(",")]
    if not selected:
        raise ValueError("No selected cases")
    started = time.perf_counter()
    rows = []
    for case in selected:
        comparison_end = min(package["cutoff"], max(c["end"] for c in package["cases"])) if args.extend_to_cutoff else None
        if args.horizon_hours is not None:
            comparison_end = min(package["cutoff"], case["start"] + args.horizon_hours * 3600)
        candidate = Replay(package, case, policy, variant=args.variant,
                           component_pool=args.component_pool, seed=args.seed, comparison_end=comparison_end).run()
        comparators = []
        for mode in ("business", "hot"):
            result = Replay(package, case, FixedMode(mode), variant=args.variant,
                            component_pool=args.component_pool, seed=args.seed, comparison_end=comparison_end).run()
            result["comparator"] = mode + "_no_early_maintenance"
            # Full candidate diagnostics remain; simple comparators need only
            # executed actions/states and aggregate cost, not repeated no-op rows.
            result.pop("decisions")
            comparators.append(result)
        row = dict(candidate=candidate, comparators=comparators, audit=audit_case(case, candidate, comparators))
        if args.extend_to_cutoff:
            phases = [c for c in package["cases"] if candidate["start"] <= c["start"] and c["end"] <= candidate["end"]]
            row["phase_projections"] = [dict(candidate=phase_projection(c, candidate),
                                               comparators=[phase_projection(c, dict(r, decisions=[])) for r in comparators]) for c in phases]
        rows.append(row)
        print(json.dumps(dict(case=case["id"], maintenance=candidate["counts"]["maintenance"],
                              cost=candidate["input_equivalent_cost"], errors=rows[-1]["audit"]["automatic_errors"])), flush=True)
    return dict(version=package["version"], policy_label=args.policy_label, simple_stage=args.simple_stage,
                horizon_hours=args.horizon_hours,
                expectation_contract_sha256=package.get("expectation_contract_sha256"), source_root=str(Path(args.source_root).resolve()),
                source_sha256={str(p.relative_to(args.source_root)): file_sha(p)
                               for p in sorted((Path(args.source_root) / "secretary").glob("adaptive_*.py"))
                               if "replay" not in p.name},
                replay_runtime_sha256=RUNTIME_SHA,
                input_sha256=file_sha(args.input), experience_sha256=package["experience_sha256"],
                variant=args.variant, component_pool=args.component_pool, seed=args.seed,
                comparison_contract="shared_observed_cutoff_continuation" if args.extend_to_cutoff else "original_independent_phase_cut",
                assumptions=package["assumptions"], results=rows,
                elapsed_seconds=time.perf_counter() - started,
                status="human_adjudication_required; automatic_counterexamples_retained")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare")
    make.add_argument("--input-dir", type=Path, required=True)
    make.add_argument("--manifest", type=Path, required=True)
    make.add_argument("--components", type=Path, required=True)
    make.add_argument("--experience-cases", type=Path, required=True)
    make.add_argument("--output", type=Path, required=True)
    replay = sub.add_parser("run")
    replay.add_argument("--input", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--source-root", type=Path, default=ROOT)
    replay.add_argument("--policy-label", default="candidate")
    replay.add_argument("--simple-stage", action="store_true", help="Declared hot protection then frozen V2 economics comparator")
    replay.add_argument("--horizon-hours", type=float, choices=(6, 24), help="Pre-frozen common cost horizon, clipped at observed cutoff")
    replay.add_argument("--cases")
    replay.add_argument("--extend-to-cutoff", action="store_true",
                        help="Continue every policy to the existing common observed case cutoff; preserve original phase projections")
    replay.add_argument("--variant", choices=("base", "whole_invoice", "short_cache", "suffix_double", "slow_block", "cost_double", "unknown_reminders", "mechanical_failure", "raw_coverage_only", "initial_hot"), default="base")
    replay.add_argument("--component-pool", choices=("all", "same-target", "gpt-only"), default="all")
    replay.add_argument("--seed", type=int, default=2,
                        help="Fixed empirical settlement stratum; base starts at median-cost stratum")
    stage = sub.add_parser("prepare-stage")
    stage.add_argument("--legacy-input", type=Path, required=True)
    stage.add_argument("--afternoon", type=Path, required=True)
    stage.add_argument("--expectations", type=Path, required=True)
    stage.add_argument("--output-dir", type=Path, required=True)
    stage.add_argument("--freeze-expectations", action="store_true", help="Create expectations only, with zero policy calls; refuses overwrite")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.input_dir, args.manifest, args.components, args.experience_cases)
        write(args.output, result)
        print(json.dumps(dict(output=str(args.output), experience_sha256=result["experience_sha256"],
                              samples=len(result["maintenance_samples"]), policy_calls=0)))
    elif args.command == "prepare-stage":
        from secretary.adaptive_empirical_replay_stage import prepare_stage, scenario_contract
        if args.freeze_expectations:
            if args.expectations.exists():
                raise ValueError("Frozen expectations already exist; do not overwrite")
            write(args.expectations, scenario_contract(args.legacy_input, args.afternoon))
            print(json.dumps(dict(output=str(args.expectations), policy_calls=0)))
        else:
            for name, value in prepare_stage(args.legacy_input, args.afternoon, args.expectations).items():
                write(args.output_dir / (name + ".json"), value)
            print(json.dumps(dict(output=str(args.output_dir), policy_calls=0)))
    else:
        result = run(args)
        write(args.output, result)
        args.output.with_suffix(".md").write_text(summarize(result), encoding="utf-8")


if __name__ == "__main__":
    main()
