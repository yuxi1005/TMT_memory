import argparse
import csv
from pathlib import Path

from data_loader import flatten_cases
from evaluator import evaluate_memory_case
from run_experiment import parse_top_k_values
from scorers import memory_role
from selectors import proposed_memory_rows


ABLATIONS = [
    "full_core_v2",
    "wo_embedding",
    "wo_decay",
    "wo_role_matrix",
    "wo_domain_gate",
    "wo_tmt_condition",
    "wo_eisenhower",
]

FIELDNAMES = [
    "top_k",
    "ablation",
    "user_id",
    "query_id",
    "query_mode",
    "query_subtype",
    "hard_case_tag",
    "query",
    "selected_memory_ids",
    "selected_event_ids",
    "selected_memory_types",
    "selected_memory_roles",
    "selected_memory_scores",
    "gold_memory_ids",
    "gold_event_ids",
    "memory_recall",
    "memory_NDCG",
    "memory_top1_accuracy",
    "todo_recall",
    "non_todo_recall",
    "completed_task_error_rate",
    "todo_intrusion_rate",
    "wrong_domain_intrusion_rate",
    "stale_memory_intrusion_rate",
    "completed_task_intrusion_rate",
    "completed_todo_retro_recall",
    "active_todo_precision",
    "wrong_domain_urgent_intrusion_rate",
    "stale_preference_intrusion_rate",
    "far_deadline_before_near_rate",
    "deadline_ranking_accuracy",
    "memory_token_cost",
]


def rank_memories_ablation(case, ablation, top_k):
    rows = proposed_memory_rows(case, ablation=ablation)
    ranked = sorted(rows, key=lambda item: item[1], reverse=True)
    return [
        {
            "memory_id": memory["memory_id"],
            "event_id": memory["event_id"],
            "score": round(float(score), 6),
            "memory_type": memory.get("memory_type", ""),
            "memory_role": memory_role(memory),
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
                        "selected_memory_roles": "|".join(item["memory_role"] for item in selected_memories),
                        "selected_memory_scores": "|".join(str(item["score"]) for item in selected_memories),
                        "gold_memory_ids": "|".join(case["gold_memory_ids"]),
                        "gold_event_ids": "|".join(case["gold_event_ids"]),
                        **metrics,
                    }
                )

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
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
