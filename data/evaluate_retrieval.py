# evaluate_retrieval.py
# -*- coding: utf-8 -*-

"""
Evaluate retrieval baselines on benchmark queries.

Default:
  py evaluate_retrieval.py L01

Inputs:
  outputs/mu/{user_id}_memory_units_current.jsonl
  outputs/benchmark/{user_id}_queries.jsonl

Outputs:
  outputs/eval/{user_id}_retrieval_runs.jsonl
  outputs/eval/{user_id}_retrieval_metrics.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MU_DIR = BASE_DIR / "outputs" / "mu"
DEFAULT_BENCHMARK_DIR = BASE_DIR / "outputs" / "benchmark"
DEFAULT_OUT_DIR = BASE_DIR / "outputs" / "eval"
DEFAULT_K_VALUES = [1, 3, 5]


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


def content_of(mu: Dict[str, Any]) -> str:
    return str(mu.get("content") or "")


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def char_ngrams(text: str, n: int = 2) -> set[str]:
    text = normalize(text)
    if not text:
        return set()
    if len(text) <= n:
        return {text}
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def lexical_score(query: str, content: str) -> float:
    q = char_ngrams(query)
    c = char_ngrams(content)
    if not q or not c:
        return 0.0
    return len(q & c) / math.sqrt(len(q) * len(c))


def recency_score(query_day: int, mu: Dict[str, Any]) -> float:
    delta = max(0, query_day - day_of(mu))
    return 1.0 / (1.0 + delta / 30.0)


def importance_score(mu: Dict[str, Any]) -> float:
    return max(0.0, min(1.0, float(mu.get("importance", 0.0))))


def ddl_score(query_day: int, mu: Dict[str, Any]) -> float:
    ddl = ddl_of(mu)
    if ddl is None:
        return 0.0
    distance = abs(ddl - query_day)
    return 1.0 / (1.0 + distance / 14.0)


def todo_score(mu: Dict[str, Any]) -> float:
    return 1.0 if bool(mu.get("istodo", mu.get("is_todo", False))) else 0.0


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def state_heuristic_score(query: Dict[str, Any], mu: Dict[str, Any]) -> float:
    q = str(query["query"])
    c = content_of(mu)
    score = 0.45 * lexical_score(q, c)
    score += 0.15 * recency_score(int(query["query_day"]), mu)
    score += 0.10 * importance_score(mu)

    if contains_any(q, ["还没完成", "继续推进", "待办", "接下来"]):
        score += 0.35 * todo_score(mu)
        if contains_any(c, ["已完成", "取消", "已取消", "不再", "临时", "只是"]):
            score -= 0.25

    if contains_any(q, ["当前", "有效", "现在"]) and contains_any(q, ["计划", "方案"]):
        if contains_any(c, ["当前", "现在", "仍", "阶段目标"]):
            score += 0.25
        if contains_any(c, ["不再", "替换", "降级", "历史参考", "旧计划"]):
            score -= 0.35

    if contains_any(q, ["已经完成", "完成的任务", "结果", "结论", "参考"]):
        if contains_any(c, ["已完成", "发现", "结论", "观察到", "标出"]):
            score += 0.30
        if todo_score(mu):
            score -= 0.20

    if contains_any(q, ["偏好"]):
        if "偏好" in c:
            score += 0.30
        if contains_any(c, ["旧偏好", "不作为默认", "临时"]):
            score -= 0.20

    if contains_any(q, ["约束", "限制"]):
        if contains_any(c, ["约束", "限制", "不要", "只记录"]):
            score += 0.35
        if contains_any(c, ["临时", "焦虑", "只是"]):
            score -= 0.20

    if contains_any(q, ["复盘", "周期"]):
        if contains_any(c, ["复盘", "下一次", "当前仍需", "最近"]):
            score += 0.35
        if contains_any(c, ["历史参考", "过期", "不再"]):
            score -= 0.20

    return score


def score_mu(query: Dict[str, Any], mu: Dict[str, Any], baseline: str) -> float:
    q = str(query["query"])
    q_day = int(query["query_day"])
    lex = lexical_score(q, content_of(mu))

    if baseline == "lexical":
        return lex
    if baseline == "recency":
        return recency_score(q_day, mu)
    if baseline == "importance":
        return importance_score(mu)
    if baseline == "ddl":
        return ddl_score(q_day, mu)
    if baseline == "lexical_recency":
        return 0.75 * lex + 0.25 * recency_score(q_day, mu)
    if baseline == "combined":
        return (
            0.55 * lex
            + 0.15 * recency_score(q_day, mu)
            + 0.15 * importance_score(mu)
            + 0.10 * ddl_score(q_day, mu)
            + 0.05 * todo_score(mu)
        )
    if baseline == "state_heuristic":
        return state_heuristic_score(query, mu)
    raise ValueError(f"Unknown baseline: {baseline}")


def rank(query: Dict[str, Any], mus: List[Dict[str, Any]], baseline: str) -> List[Dict[str, Any]]:
    scored = []
    for mu in mus:
        scored.append(
            {
                "mu_id": str(mu["id"]),
                "score": round(score_mu(query, mu, baseline), 6),
                "event_id": str(mu.get("event_id") or mu.get("eventid") or ""),
                "is_todo": bool(mu.get("istodo", mu.get("is_todo", False))),
                "ddl": ddl_of(mu),
                "importance": importance_score(mu),
                "day": day_of(mu),
            }
        )
    scored.sort(key=lambda x: (-x["score"], -x["importance"], -x["day"], x["mu_id"]))
    return scored


def recall_at_k(ranked_ids: List[str], gold: set[str], k: int) -> float:
    if not gold:
        return 0.0
    return len(set(ranked_ids[:k]) & gold) / len(gold)


def precision_at_k(ranked_ids: List[str], gold: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    return len(set(ranked_ids[:k]) & gold) / k


def mrr_at_k(ranked_ids: List[str], gold: set[str], k: int) -> float:
    for idx, mu_id in enumerate(ranked_ids[:k], start=1):
        if mu_id in gold:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(ranked_ids: List[str], gold: set[str], k: int) -> float:
    dcg = 0.0
    for idx, mu_id in enumerate(ranked_ids[:k], start=1):
        rel = 1.0 if mu_id in gold else 0.0
        dcg += rel / math.log2(idx + 1)
    ideal_hits = min(len(gold), k)
    if ideal_hits == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(idx + 1) for idx in range(1, ideal_hits + 1))
    return dcg / idcg


def hard_negative_hits(ranked_ids: List[str], hard: set[str], k: int) -> int:
    return len(set(ranked_ids[:k]) & hard)


def evaluate(
    user_id: str,
    *,
    mu_dir: Path,
    benchmark_dir: Path,
    out_dir: Path,
    query_file: Optional[Path] = None,
    output_tag: Optional[str] = None,
    baselines: List[str],
    k_values: List[int],
) -> Dict[str, Any]:
    mu_path = mu_dir / f"{user_id}_memory_units_current.jsonl"
    query_path = query_file or (benchmark_dir / f"{user_id}_queries.jsonl")
    if not mu_path.exists():
        raise FileNotFoundError(mu_path)
    if not query_path.exists():
        raise FileNotFoundError(query_path)

    mus = read_jsonl(mu_path)
    queries = read_jsonl(query_path)
    run_rows: List[Dict[str, Any]] = []

    metric_acc: Dict[str, Dict[str, List[float]]] = {
        baseline: {} for baseline in baselines
    }

    for baseline in baselines:
        for query in queries:
            ranked = rank(query, mus, baseline)
            ranked_ids = [row["mu_id"] for row in ranked]
            gold = set(query.get("gold_mu_ids", []))
            hard = set(query.get("hard_negative_current_mu_ids", []))

            per_query_metrics: Dict[str, float] = {}
            for k in k_values:
                per_query_metrics[f"recall@{k}"] = recall_at_k(ranked_ids, gold, k)
                per_query_metrics[f"precision@{k}"] = precision_at_k(ranked_ids, gold, k)
                per_query_metrics[f"mrr@{k}"] = mrr_at_k(ranked_ids, gold, k)
                per_query_metrics[f"ndcg@{k}"] = ndcg_at_k(ranked_ids, gold, k)
                per_query_metrics[f"hard_negative_hits@{k}"] = float(hard_negative_hits(ranked_ids, hard, k))

            for name, value in per_query_metrics.items():
                metric_acc[baseline].setdefault(name, []).append(value)

            run_rows.append(
                {
                    "user_id": user_id,
                    "query_id": query["query_id"],
                    "case_type": query["case_type"],
                    "baseline": baseline,
                    "gold_mu_ids": query.get("gold_mu_ids", []),
                    "hard_negative_current_mu_ids": query.get("hard_negative_current_mu_ids", []),
                    "ranked_mu_ids": ranked_ids,
                    "top_scores": ranked[:10],
                    "metrics": {k: round(v, 6) for k, v in per_query_metrics.items()},
                }
            )

    metrics = {
        "user_id": user_id,
        "mu_file": str(mu_path),
        "query_file": str(query_path),
        "query_count": len(queries),
        "candidate_count": len(mus),
        "baselines": {},
    }
    for baseline, values_by_metric in metric_acc.items():
        metrics["baselines"][baseline] = {
            name: round(sum(values) / len(values), 6) if values else 0.0
            for name, values in sorted(values_by_metric.items())
        }

    suffix = f"_{output_tag}" if output_tag else ""
    write_jsonl(out_dir / f"{user_id}{suffix}_retrieval_runs.jsonl", run_rows)
    write_json(out_dir / f"{user_id}{suffix}_retrieval_metrics.json", metrics)
    return metrics


def parse_k_values(value: str) -> List[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval baselines.")
    parser.add_argument("user_id", help="User id, for example L01.")
    parser.add_argument("--mu-dir", type=Path, default=DEFAULT_MU_DIR)
    parser.add_argument("--benchmark-dir", type=Path, default=DEFAULT_BENCHMARK_DIR)
    parser.add_argument("--query-file", type=Path, help="Explicit query JSONL file. Overrides --benchmark-dir.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--output-tag", help="Optional suffix for output files, for example state.")
    parser.add_argument(
        "--baselines",
        default="lexical,recency,importance,ddl,lexical_recency,combined,state_heuristic",
        help="Comma-separated baselines.",
    )
    parser.add_argument("--k", default="1,3,5", help="Comma-separated K values.")
    args = parser.parse_args()

    baselines = [x.strip() for x in args.baselines.split(",") if x.strip()]
    metrics = evaluate(
        args.user_id,
        mu_dir=args.mu_dir,
        benchmark_dir=args.benchmark_dir,
        out_dir=args.out_dir,
        query_file=args.query_file,
        output_tag=args.output_tag,
        baselines=baselines,
        k_values=parse_k_values(args.k),
    )
    print(f"{args.user_id}: evaluated {metrics['query_count']} queries over {metrics['candidate_count']} candidates")
    suffix = f"_{args.output_tag}" if args.output_tag else ""
    print(f"Metrics: {args.out_dir / f'{args.user_id}{suffix}_retrieval_metrics.json'}")
    print(f"Runs: {args.out_dir / f'{args.user_id}{suffix}_retrieval_runs.jsonl'}")


if __name__ == "__main__":
    main()
