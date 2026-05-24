# build_state_benchmark.py
# -*- coding: utf-8 -*-

"""
Build state-aware retrieval benchmark queries from timeline summaries and MU outputs.

This is the generic successor to the early keyword-based benchmark builder. It uses
the latent timeline's final_state_summary as the source of state labels, then maps
those target_ids back to extracted memory units through the extraction log.

Example:
  py build_state_benchmark.py L01
  py build_state_benchmark.py --all
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TIMELINE_DIR = BASE_DIR / "outputs" / "timelines"
DEFAULT_MU_DIR = BASE_DIR / "outputs" / "mu"
DEFAULT_OUT_DIR = BASE_DIR / "outputs" / "benchmark_state"


SUMMARY_FIELDS = [
    "current_plans",
    "stale_plans",
    "active_tasks",
    "completed_tasks",
    "cancelled_tasks",
    "postponed_tasks",
    "current_constraints",
    "stable_preferences",
    "old_preferences",
    "updated_preferences",
    "important_not_urgent_tasks",
    "urgent_low_value_tasks",
    "noise_events",
    "hard_negative_sources",
]


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def unique(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x) for x in value if x is not None and str(x)]
    if value is None:
        return []
    return [str(value)]


def canonical_target_id(raw: str) -> str:
    """Drop state suffixes such as pref_x:old_format or recur_x:day88_outdated."""
    return str(raw).split(":", 1)[0]


def day_of(mu: Dict[str, Any]) -> int:
    ts = mu.get("timestamp")
    value = ts.get("day") if isinstance(ts, dict) else ts
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def event_id_of(mu: Dict[str, Any]) -> str:
    return str(mu.get("eventid") or mu.get("event_id") or "")


def target_lists(summary: Dict[str, Any], *fields: str) -> List[str]:
    values: List[str] = []
    for field in fields:
        values.extend(canonical_target_id(x) for x in as_list(summary.get(field)))
    return unique(values)


def build_target_maps(
    logs: List[Dict[str, Any]],
    all_mus: List[Dict[str, Any]],
) -> tuple[Dict[str, str], Dict[str, List[str]], Dict[str, List[str]]]:
    target_to_current_mu: Dict[str, str] = {}
    target_to_event_ids: Dict[str, List[str]] = {}

    for row in logs:
        target_id = row.get("target_id")
        affected = row.get("affected_mu_ids") or []
        event_id = str(row.get("event_id") or "")
        if not target_id:
            continue
        target = canonical_target_id(str(target_id))
        if affected:
            target_to_current_mu[target] = str(affected[-1])
        if event_id:
            target_to_event_ids.setdefault(target, []).append(event_id)

    event_to_all_mu_ids: Dict[str, List[str]] = {}
    for mu in all_mus:
        event_id = event_id_of(mu)
        if event_id:
            event_to_all_mu_ids.setdefault(event_id, []).append(str(mu.get("id") or ""))

    target_to_all_mu_ids: Dict[str, List[str]] = {}
    for target, event_ids in target_to_event_ids.items():
        ids: List[str] = []
        for event_id in event_ids:
            ids.extend(event_to_all_mu_ids.get(event_id, []))
        target_to_all_mu_ids[target] = unique(ids)

    return target_to_current_mu, target_to_all_mu_ids, target_to_event_ids


def current_mu_ids_for_targets(targets: Iterable[str], target_to_current_mu: Dict[str, str]) -> List[str]:
    return unique(
        target_to_current_mu.get(canonical_target_id(target), "")
        for target in targets
    )


def all_mu_ids_for_targets(targets: Iterable[str], target_to_all_mu_ids: Dict[str, List[str]]) -> List[str]:
    ids: List[str] = []
    for target in targets:
        ids.extend(target_to_all_mu_ids.get(canonical_target_id(target), []))
    return unique(ids)


def hard_all_mu_ids_for_targets(
    targets: Iterable[str],
    *,
    gold_targets: Iterable[str],
    target_to_all_mu_ids: Dict[str, List[str]],
) -> List[str]:
    ids: List[str] = []
    gold = {canonical_target_id(target) for target in gold_targets}
    for raw_target in targets:
        target = canonical_target_id(raw_target)
        target_ids = target_to_all_mu_ids.get(target, [])
        if target in gold:
            # For the same target, older versions are valid hard negatives, but
            # the latest all-MU is the current state and should not be a negative.
            ids.extend(target_ids[:-1])
        else:
            ids.extend(target_ids)
    return unique(ids)


def event_ids_for_targets(targets: Iterable[str], target_to_event_ids: Dict[str, List[str]]) -> List[str]:
    ids: List[str] = []
    for target in targets:
        ids.extend(target_to_event_ids.get(canonical_target_id(target), []))
    return unique(ids)


def query_day(current_mus: List[Dict[str, Any]], timeline: Dict[str, Any]) -> int:
    max_mu_day = max([day_of(mu) for mu in current_mus] + [0])
    time_span = timeline.get("time_span") or {}
    try:
        max_timeline_day = int(time_span.get("end_day") or 0)
    except (TypeError, ValueError):
        max_timeline_day = 0
    return max(max_mu_day, max_timeline_day) + 1


def make_query(
    *,
    user_id: str,
    query_id: str,
    query_day_value: int,
    case_type: str,
    query: str,
    gold_targets: List[str],
    hard_current_targets: List[str],
    hard_all_targets: List[str],
    target_to_current_mu: Dict[str, str],
    target_to_all_mu_ids: Dict[str, List[str]],
    target_to_event_ids: Dict[str, List[str]],
    rationale: str,
) -> Optional[Dict[str, Any]]:
    gold_mu_ids = current_mu_ids_for_targets(gold_targets, target_to_current_mu)
    if not gold_mu_ids:
        return None

    hard_current_mu_ids = [
        mu_id
        for mu_id in current_mu_ids_for_targets(hard_current_targets, target_to_current_mu)
        if mu_id not in set(gold_mu_ids)
    ]
    hard_all_mu_ids = hard_all_mu_ids_for_targets(
        hard_all_targets,
        gold_targets=gold_targets,
        target_to_all_mu_ids=target_to_all_mu_ids,
    )

    return {
        "user_id": user_id,
        "query_id": query_id,
        "query_day": query_day_value,
        "case_type": case_type,
        "query": query,
        "gold_targets": gold_targets,
        "gold_mu_ids": gold_mu_ids,
        "gold_event_ids": event_ids_for_targets(gold_targets, target_to_event_ids),
        "hard_negative_targets": unique(hard_current_targets + hard_all_targets),
        "hard_negative_current_mu_ids": unique(hard_current_mu_ids),
        "hard_negative_all_mu_ids": unique(hard_all_mu_ids),
        "candidate_sets": {
            "primary": "current_memory_units",
            "hard_negative_pool": "all_memory_units",
        },
        "rationale": rationale,
    }


def build_queries_for_user(
    user_id: str,
    *,
    timeline_dir: Path,
    mu_dir: Path,
) -> List[Dict[str, Any]]:
    timeline_path = timeline_dir / f"{user_id}_timeline.json"
    current_path = mu_dir / f"{user_id}_memory_units_current.jsonl"
    all_path = mu_dir / f"{user_id}_memory_units_all.jsonl"
    log_path = mu_dir / f"{user_id}_extraction_log.jsonl"

    missing = [p for p in [timeline_path, current_path, all_path, log_path] if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required files: " + ", ".join(str(p) for p in missing))

    timeline = read_json(timeline_path)
    current_mus = read_jsonl(current_path)
    all_mus = read_jsonl(all_path)
    logs = read_jsonl(log_path)
    summary = timeline.get("final_state_summary") or {}

    target_to_current_mu, target_to_all_mu_ids, target_to_event_ids = build_target_maps(logs, all_mus)
    qday = query_day(current_mus, timeline)

    current_plan_targets = target_lists(summary, "current_plans")
    stale_plan_targets = target_lists(summary, "stale_plans")
    active_task_targets = target_lists(summary, "active_tasks", "postponed_tasks")
    completed_task_targets = target_lists(summary, "completed_tasks")
    cancelled_task_targets = target_lists(summary, "cancelled_tasks")
    constraint_targets = target_lists(summary, "current_constraints")
    current_pref_targets = target_lists(summary, "stable_preferences", "updated_preferences")
    old_pref_targets = target_lists(summary, "old_preferences")
    noise_targets = target_lists(summary, "noise_events", "urgent_low_value_tasks")
    hard_source_targets = target_lists(summary, "hard_negative_sources")

    recurring_targets = [
        target for target in hard_source_targets
        if target.startswith("recur_") and target in target_to_current_mu
    ]

    specs = [
        {
            "case_type": "active_task_currentness",
            "query": "我现在还没完成、接下来需要继续推进的事项有哪些？",
            "gold": active_task_targets,
            "hard_current": completed_task_targets + cancelled_task_targets + noise_targets,
            "hard_all": completed_task_targets + cancelled_task_targets + stale_plan_targets + hard_source_targets,
            "rationale": "Tests whether retrieval prioritizes currently active or postponed tasks over completed, cancelled, stale, and noisy memories.",
        },
        {
            "case_type": "current_plan_vs_stale_plan",
            "query": "我现在有效的计划是什么？请不要把已经被替换或降级的旧方案当成当前方案。",
            "gold": current_plan_targets,
            "hard_current": stale_plan_targets + completed_task_targets,
            "hard_all": stale_plan_targets + hard_source_targets,
            "rationale": "Tests whether retrieval selects current plans while suppressing stale plans and old same-domain artifacts.",
        },
        {
            "case_type": "completed_result_as_evidence",
            "query": "之前已经完成的任务里，有哪些结果或结论现在仍然可以作为参考？",
            "gold": completed_task_targets,
            "hard_current": active_task_targets + cancelled_task_targets,
            "hard_all": active_task_targets + cancelled_task_targets + hard_source_targets,
            "rationale": "Tests whether completed task results can be retrieved as evidence without being confused with still-open tasks.",
        },
        {
            "case_type": "preference_currentness",
            "query": "我当前稳定或最新的偏好是什么？请不要沿用已经改掉的旧偏好。",
            "gold": current_pref_targets,
            "hard_current": old_pref_targets + noise_targets,
            "hard_all": old_pref_targets + hard_source_targets,
            "rationale": "Tests stable and updated preference retrieval under old-preference and temporary-noise distractors.",
        },
        {
            "case_type": "constraint_vs_noise",
            "query": "我现在需要遵守哪些约束？请优先找当前有效约束，不要被临时想法或噪音带偏。",
            "gold": constraint_targets,
            "hard_current": noise_targets + cancelled_task_targets,
            "hard_all": noise_targets + hard_source_targets,
            "rationale": "Tests current constraint retrieval against nearby noisy or low-value memories.",
        },
        {
            "case_type": "recurring_latest_status",
            "query": "最近一次周期复盘后，当前状态和下一步安排是什么？请不要召回过期复盘。",
            "gold": recurring_targets,
            "hard_current": stale_plan_targets + completed_task_targets,
            "hard_all": recurring_targets + hard_source_targets,
            "rationale": "Tests latest recurring-state retrieval and suppression of older recurring instances.",
        },
    ]

    rows: List[Dict[str, Any]] = []
    for index, spec in enumerate(specs, start=1):
        row = make_query(
            user_id=user_id,
            query_id=f"{user_id}_sq{index:03d}",
            query_day_value=qday,
            case_type=spec["case_type"],
            query=spec["query"],
            gold_targets=unique(spec["gold"]),
            hard_current_targets=unique(spec["hard_current"]),
            hard_all_targets=unique(spec["hard_all"]),
            target_to_current_mu=target_to_current_mu,
            target_to_all_mu_ids=target_to_all_mu_ids,
            target_to_event_ids=target_to_event_ids,
            rationale=spec["rationale"],
        )
        if row:
            row["source_artifacts"] = {
                "timeline": str(timeline_path.relative_to(BASE_DIR)),
                "current_memory_units": str(current_path.relative_to(BASE_DIR)),
                "all_memory_units": str(all_path.relative_to(BASE_DIR)),
                "extraction_log": str(log_path.relative_to(BASE_DIR)),
            }
            row["summary_fields_used"] = SUMMARY_FIELDS
            rows.append(row)

    return rows


def discover_users(mu_dir: Path) -> List[str]:
    return [
        path.name.removesuffix("_memory_units_current.jsonl")
        for path in sorted(mu_dir.glob("*_memory_units_current.jsonl"))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build generic state-aware benchmark queries.")
    parser.add_argument("user_ids", nargs="*", help="User ids, for example L01 S01.")
    parser.add_argument("--all", action="store_true", help="Use all users found in the MU directory.")
    parser.add_argument("--timeline-dir", type=Path, default=DEFAULT_TIMELINE_DIR)
    parser.add_argument("--mu-dir", type=Path, default=DEFAULT_MU_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    if args.all:
        user_ids = discover_users(args.mu_dir)
    else:
        user_ids = args.user_ids

    if not user_ids:
        raise ValueError("Provide at least one user id or pass --all.")

    summary: Dict[str, Any] = {
        "timeline_dir": str(args.timeline_dir),
        "mu_dir": str(args.mu_dir),
        "out_dir": str(args.out_dir),
        "users": {},
    }
    all_rows: List[Dict[str, Any]] = []

    for user_id in user_ids:
        rows = build_queries_for_user(user_id, timeline_dir=args.timeline_dir, mu_dir=args.mu_dir)
        out_path = args.out_dir / f"{user_id}_state_queries.jsonl"
        write_jsonl(out_path, rows)
        summary["users"][user_id] = {
            "query_count": len(rows),
            "output": str(out_path),
            "case_types": [row["case_type"] for row in rows],
        }
        all_rows.extend(rows)
        print(f"{user_id}: wrote {len(rows)} state-aware queries -> {out_path}")

    if len(user_ids) > 1:
        write_jsonl(args.out_dir / "all_state_queries.jsonl", all_rows)

    summary_path = args.out_dir / "state_benchmark_summary.json"
    write_json(summary_path, summary)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
