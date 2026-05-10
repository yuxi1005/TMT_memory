import argparse
import csv
from pathlib import Path

from data_loader import flatten_cases
from evaluator import evaluate_memory_case
from run_experiment import METHODS, parse_top_k_values
from selectors import rank_memories


def run(input_path, output_csv, top_k_values=(1, 3, 5, 10)):
    cases = flatten_cases(input_path)
    rows = []

    for case in cases:
        for top_k in top_k_values:
            for method in METHODS:
                selected_memories = rank_memories(case, method, top_k=top_k)
                metrics = evaluate_memory_case(case, selected_memories)
                rows.append(
                    {
                        "top_k": top_k,
                        "user_id": case["user_id"],
                        "query_id": case["query"]["query_id"],
                        "query_mode": case["query"].get("query_mode", ""),
                        "query_subtype": case["query"].get("query_subtype", ""),
                        "query": case["query"]["query"],
                        "method": method,
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
    parser.add_argument("--top-k-values", default="1,3,5,10")
    args = parser.parse_args()

    top_k_values = [args.top_k] if args.top_k is not None else parse_top_k_values(args.top_k_values)
    rows = run(args.input, args.output, top_k_values)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
