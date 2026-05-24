# build_retrieval_benchmark.py
# -*- coding: utf-8 -*-

"""
Build retrieval benchmark query/gold files from extracted memory units.

Default:
  py build_retrieval_benchmark.py L01

Input:
  outputs/mu/{user_id}_memory_units_current.jsonl
  outputs/mu/{user_id}_memory_units_all.jsonl
  outputs/mu/{user_id}_extraction_log.jsonl

Output:
  outputs/benchmark/{user_id}_queries.jsonl
  outputs/benchmark/{user_id}_benchmark_summary.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MU_DIR = BASE_DIR / "outputs" / "mu"
DEFAULT_OUT_DIR = BASE_DIR / "outputs" / "benchmark"


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


def day_of(mu: Dict[str, Any]) -> int:
    ts = mu.get("timestamp")
    if isinstance(ts, dict):
        value = ts.get("day", 0)
    else:
        value = ts or 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def ddl_of(mu: Dict[str, Any]) -> Optional[int]:
    value = mu.get("ddl")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def user_id_of(mu: Dict[str, Any]) -> str:
    return str(mu.get("user_id") or mu.get("roleuserid") or "")


def event_id_of(mu: Dict[str, Any]) -> str:
    return str(mu.get("event_id") or mu.get("eventid") or "")


def content_of(mu: Dict[str, Any]) -> str:
    return str(mu.get("content") or "")


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(k in text for k in keywords)


def unique(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def by_keywords(
    mus: List[Dict[str, Any]],
    keywords: Iterable[str],
    *,
    active_only: bool = False,
    min_importance: Optional[float] = None,
    exclude_noise: bool = True,
) -> List[Dict[str, Any]]:
    result = []
    for mu in mus:
        text = content_of(mu)
        if not contains_any(text, keywords):
            continue
        if active_only and not bool(mu.get("istodo", mu.get("is_todo", False))):
            continue
        if min_importance is not None and float(mu.get("importance", 0.0)) < min_importance:
            continue
        if exclude_noise and float(mu.get("importance", 0.0)) <= 0.2 and not active_only:
            continue
        result.append(mu)
    return sorted(result, key=lambda x: (-float(x.get("importance", 0.0)), day_of(x)))


def select(
    mus: List[Dict[str, Any]],
    predicate: Any,
    *,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    rows = [mu for mu in mus if predicate(mu)]
    rows.sort(key=lambda x: (-float(x.get("importance", 0.0)), day_of(x)))
    if limit is not None:
        return rows[:limit]
    return rows


def ids(mus: Iterable[Dict[str, Any]]) -> List[str]:
    return unique(str(mu.get("id", "")) for mu in mus)


def event_ids(mus: Iterable[Dict[str, Any]]) -> List[str]:
    return unique(event_id_of(mu) for mu in mus)


def old_versions_for(
    current_ids: Iterable[str],
    all_mus: List[Dict[str, Any]],
    current_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    negatives: List[str] = []
    for current_id in current_ids:
        current = current_by_id.get(current_id)
        if not current:
            continue
        current_content = content_of(current)
        linked = [
            mu for mu in all_mus
            if mu.get("linked_current_mu_id") == current_id
            and content_of(mu) != current_content
        ]
        linked.sort(key=day_of)
        negatives.extend(str(mu["id"]) for mu in linked[:-1] or linked)
    return unique(negatives)


def hard_current(
    current_mus: List[Dict[str, Any]],
    gold_ids: Iterable[str],
    keywords: Iterable[str],
    *,
    limit: int = 4,
) -> List[str]:
    gold = set(gold_ids)
    candidates = [
        mu for mu in current_mus
        if str(mu.get("id")) not in gold and contains_any(content_of(mu), keywords)
    ]
    candidates.sort(key=lambda x: (float(x.get("importance", 0.0)), -day_of(x)))
    return ids(candidates[:limit])


def make_query(
    *,
    user_id: str,
    query_day: int,
    case_type: str,
    query: str,
    gold: List[Dict[str, Any]],
    current_mus: List[Dict[str, Any]],
    all_mus: List[Dict[str, Any]],
    current_by_id: Dict[str, Dict[str, Any]],
    hard_keywords: Iterable[str],
    rationale: str,
) -> Optional[Dict[str, Any]]:
    gold_mu_ids = ids(gold)
    if not gold_mu_ids:
        return None
    hard_current_ids = hard_current(current_mus, gold_mu_ids, hard_keywords)
    hard_all_ids = old_versions_for(gold_mu_ids, all_mus, current_by_id)
    return {
        "user_id": user_id,
        "query_day": query_day,
        "case_type": case_type,
        "query": query,
        "gold_mu_ids": gold_mu_ids,
        "gold_event_ids": event_ids(gold),
        "hard_negative_current_mu_ids": hard_current_ids,
        "hard_negative_all_mu_ids": hard_all_ids,
        "candidate_sets": {
            "primary": "current_memory_units",
            "hard_negative_pool": "all_memory_units",
        },
        "rationale": rationale,
    }


def build_queries_for_user(user_id: str, mu_dir: Path) -> List[Dict[str, Any]]:
    current_path = mu_dir / f"{user_id}_memory_units_current.jsonl"
    all_path = mu_dir / f"{user_id}_memory_units_all.jsonl"
    log_path = mu_dir / f"{user_id}_extraction_log.jsonl"

    missing = [p for p in [current_path, all_path, log_path] if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required MU files: " + ", ".join(str(p) for p in missing))

    current_mus = read_jsonl(current_path)
    all_mus = read_jsonl(all_path)
    logs = read_jsonl(log_path)
    current_by_id = {str(mu["id"]): mu for mu in current_mus}
    query_day = max([day_of(mu) for mu in current_mus] + [0]) + 1

    active_todos = [
        mu for mu in current_mus
        if bool(mu.get("istodo", mu.get("is_todo", False)))
    ]
    active_todos.sort(key=lambda x: (ddl_of(x) is None, ddl_of(x) or 10**9, -float(x.get("importance", 0.0))))

    sleep_current = select(
        current_mus,
        lambda mu: contains_any(
            content_of(mu),
            ["睡眠", "夜醒", "小睡", "哄睡", "晚间流程", "喂奶间隔"],
        )
        and (float(mu.get("importance", 0.0)) >= 0.8 or bool(mu.get("istodo", mu.get("is_todo", False)))),
        limit=5,
    )
    supplies_current = select(
        current_mus,
        lambda mu: contains_any(content_of(mu), ["库存", "纸尿裤需要补货", "湿巾", "奶瓶配件"])
        and "临时" not in content_of(mu),
        limit=3,
    )
    preference_current = select(
        current_mus,
        lambda mu: "偏好" in content_of(mu) and contains_any(content_of(mu), ["购物", "比较", "建议", "表格"]),
        limit=2,
    )
    constraint_current = select(
        current_mus,
        lambda mu: "约束" in content_of(mu) and contains_any(content_of(mu), ["搜索", "记录现象", "第二天"]),
        limit=2,
    )
    review_current = select(
        current_mus,
        lambda mu: contains_any(content_of(mu), ["复盘", "跟踪", "下一次"]) and "当前仍需" in content_of(mu),
        limit=2,
    )
    completed_results = select(
        current_mus,
        lambda mu: not bool(mu.get("istodo", mu.get("is_todo", False)))
        and "尚未完成" not in content_of(mu)
        and contains_any(content_of(mu), ["已完成", "结论", "发现", "观察到"]),
        limit=4,
    )

    queries = [
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="active_todo_currentness",
            query="我现在还没完成、接下来需要继续推进的事项有哪些？",
            gold=active_todos,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["已完成", "取消", "不再", "临时", "只是"],
            rationale="Tests whether retrieval favors currently active todos over completed, cancelled, or noisy memories.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="current_sleep_plan_vs_stale_plan",
            query="宝宝睡眠这条线现在应该重点看什么？不要把早期已经替换掉的固定流程当成主方案。",
            gold=sleep_current,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["固定", "替换", "不再", "历史参考", "小睡"],
            rationale="Tests current plan selection under stale-plan and semantically similar sleep memories.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="completed_result_not_active_todo",
            query="之前做完的记录或整理任务里，有哪些结论还能作为现在安排的依据？",
            gold=completed_results,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["需要", "尚未", "延期", "待办", "截止"],
            rationale="Tests whether completed results can be retrieved as evidence without treating their old tasks as still open.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="preference_revision",
            query="如果现在要比较或购买宝宝用品，我当前更偏好的输出方式是什么？",
            gold=preference_current,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["详细表格", "当前阶段", "购物", "比较"],
            rationale="Tests updated preference retrieval and suppression of older preference versions.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="household_supplies_state",
            query="宝宝用品库存和补货这块，现在的有效状态是什么？",
            gold=supplies_current,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["活动价", "临时", "尚未", "推迟", "用品"],
            rationale="Tests current state retrieval where a task moved from active to completed.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="behavior_constraint_vs_noise",
            query="夜里醒来以后，我给自己设过什么限制，避免被焦虑搜索带偏？",
            gold=constraint_current,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["焦虑", "搜索", "临时", "未形成新安排"],
            rationale="Tests retrieval of an active constraint over nearby anxiety/noise memories.",
        ),
        make_query(
            user_id=user_id,
            query_day=query_day,
            case_type="recurring_review_current_focus",
            query="最近一次复盘后，当前还需要跟踪的重点和下一次复盘安排是什么？",
            gold=review_current,
            current_mus=current_mus,
            all_mus=all_mus,
            current_by_id=current_by_id,
            hard_keywords=["复盘", "下一次", "历史参考", "顺延"],
            rationale="Tests recurring-task state updates and latest-instance preference.",
        ),
    ]

    rows = [q for q in queries if q is not None]
    for i, row in enumerate(rows, start=1):
        row["query_id"] = f"{user_id}_q{i:03d}"
        row["source_artifacts"] = {
            "current_memory_units": str(current_path.relative_to(BASE_DIR)),
            "all_memory_units": str(all_path.relative_to(BASE_DIR)),
            "extraction_log": str(log_path.relative_to(BASE_DIR)),
        }

    log_event_types = sorted({str(row.get("event_type")) for row in logs})
    for row in rows:
        row["available_event_types"] = log_event_types

    return rows


def discover_users(mu_dir: Path) -> List[str]:
    users = []
    for path in sorted(mu_dir.glob("*_memory_units_current.jsonl")):
        users.append(path.name.removesuffix("_memory_units_current.jsonl"))
    return users


def main() -> None:
    parser = argparse.ArgumentParser(description="Build retrieval benchmark queries from MU outputs.")
    parser.add_argument("user_ids", nargs="*", help="User ids, for example L01 S01. Default: all users in outputs/mu.")
    parser.add_argument("--mu-dir", type=Path, default=DEFAULT_MU_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    user_ids = args.user_ids or discover_users(args.mu_dir)
    if not user_ids:
        raise ValueError(f"No users found in {args.mu_dir}")

    summary = {
        "mu_dir": str(args.mu_dir),
        "out_dir": str(args.out_dir),
        "users": {},
    }

    all_rows: List[Dict[str, Any]] = []
    for user_id in user_ids:
        rows = build_queries_for_user(user_id, args.mu_dir)
        output_path = args.out_dir / f"{user_id}_queries.jsonl"
        write_jsonl(output_path, rows)
        summary["users"][user_id] = {
            "query_count": len(rows),
            "output": str(output_path),
            "case_types": [row["case_type"] for row in rows],
        }
        all_rows.extend(rows)
        print(f"{user_id}: wrote {len(rows)} queries -> {output_path}")

    if len(user_ids) > 1:
        write_jsonl(args.out_dir / "all_queries.jsonl", all_rows)

    summary_path = args.out_dir / "benchmark_summary.json"
    write_json(summary_path, summary)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
