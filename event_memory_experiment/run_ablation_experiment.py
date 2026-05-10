import argparse
import csv
from pathlib import Path

from data_loader import flatten_cases
from evaluator import evaluate_memory_case
from run_experiment import parse_top_k_values
from selectors import (
    QUERY_GATES,
    domain_match_score,
    estimate_decay_lambda,
    intent_penalty,
    memory_accessibility,
    type_compatibility,
)
from scorers import similarity_score


ABLATIONS = [
    "full_qca",
    "wo_tmt",
    "wo_decay",
    "wo_compatibility",
    "wo_domain",
    "wo_penalty",
]


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def score_memory_ablation(memory, query, event, now, ablation, decay_lambda=None):
    subtype = query.get("query_subtype") or query.get("query_mode", "chat")
    gate = QUERY_GATES.get(subtype, QUERY_GATES.get(query.get("query_mode", "chat"), QUERY_GATES["chat_history"]))

    semantic = similarity_score(query["query"], memory.get("content", ""))
    importance = float(memory.get("importance", 0.5))
    accessible = float(memory.get("accessible_score", 0.5))

    if ablation == "wo_tmt" and memory.get("memory_type") == "todo":
        access = accessible
    elif ablation == "wo_decay" and memory.get("memory_type") != "todo":
        access = accessible
    else:
        access = memory_accessibility(memory, query, now, decay_lambda=decay_lambda)

    compat = 0.0 if ablation == "wo_compatibility" else type_compatibility(memory, subtype)
    domain = 0.0 if ablation == "wo_domain" else domain_match_score(query, memory, event)
    base = 0.5 * importance + 0.5 * accessible
    penalty = 0.0 if ablation == "wo_penalty" else intent_penalty(query, memory, domain, ablation=ablation)

    return clamp01(
        gate["semantic"] * semantic
        + gate["access"] * access
        + gate["compat"] * compat
        + gate["domain"] * domain
        + gate["base"] * base
        - penalty
    )


def rank_memories_ablation(case, ablation, top_k):
    rows = []
    decay_lambda = estimate_decay_lambda(case["memories"], case["now"])
    for memory in case["memories"]:
        event = case["events_by_id"][memory["event_id"]]
        score = score_memory_ablation(memory, case["query"], event, case["now"], ablation, decay_lambda=decay_lambda)
        rows.append((memory, score))

    ranked = sorted(rows, key=lambda item: item[1], reverse=True)
    return [
        {
            "memory_id": memory["memory_id"],
            "event_id": memory["event_id"],
            "score": round(float(score), 6),
            "memory_type": memory.get("memory_type", ""),
            "is_done": memory.get("is_done"),
            "ddl": memory.get("ddl"),
            "content": memory.get("content", ""),
        }
        for memory, score in ranked[:top_k]
    ]


def run(input_path, output_csv, top_k_values=(5, 10), ablations=ABLATIONS):
    cases = flatten_cases(input_path)
    rows = []

    for case in cases:
        for top_k in top_k_values:
            for ablation in ablations:
                selected_memories = rank_memories_ablation(case, ablation, top_k=top_k)
                metrics = evaluate_memory_case(case, selected_memories)
                rows.append(
                    {
                        "top_k": top_k,
                        "ablation": ablation,
                        "user_id": case["user_id"],
                        "query_id": case["query"]["query_id"],
                        "query_mode": case["query"].get("query_mode", ""),
                        "query_subtype": case["query"].get("query_subtype", ""),
                        "hard_case_tag": case["query"].get("hard_case_tag", "")
                        or case["query"].get("constraints", {}).get("hard_case_tag", ""),
                        "query": case["query"]["query"],
                        "selected_memory_ids": "|".join(item["memory_id"] for item in selected_memories),
                        "selected_event_ids": "|".join(item["event_id"] for item in selected_memories),
                        "selected_memory_types": "|".join(item["memory_type"] for item in selected_memories),
                        "selected_memory_scores": "|".join(str(item["score"]) for item in selected_memories),
                        "gold_memory_ids": "|".join(case["gold_memory_ids"]),
                        "gold_event_ids": "|".join(case["gold_event_ids"]),
                        **metrics,
                    }
                )

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--top-k-values", default="5,10")
    parser.add_argument("--ablations", default=",".join(ABLATIONS))
    args = parser.parse_args()

    top_k_values = [args.top_k] if args.top_k is not None else parse_top_k_values(args.top_k_values)
    ablations = [item.strip() for item in args.ablations.split(",") if item.strip()]
    unknown = sorted(set(ablations) - set(ABLATIONS))
    if unknown:
        raise ValueError(f"Unknown ablations: {', '.join(unknown)}")

    rows = run(args.input, args.output, top_k_values=top_k_values, ablations=ablations)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
