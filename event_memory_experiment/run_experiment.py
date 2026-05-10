import argparse
import csv
from pathlib import Path

from data_loader import flatten_cases
from evaluator import evaluate_case
from selectors import rank_events


METHODS = [
    "recency_only",
    "similarity_only",
    "recency_similarity_hybrid",
    "proposed_TMT_decay_event_memory",
]


def parse_top_k_values(value):
    if isinstance(value, (list, tuple)):
        return [int(item) for item in value]
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


def run(input_path, output_csv, top_k_values=(1, 2, 3)):
    cases = flatten_cases(input_path)
    rows = []

    for case in cases:
        for top_k in top_k_values:
            for method in METHODS:
                selected_events = rank_events(case, method, top_k=top_k)
                metrics = evaluate_case(case, selected_events)
                rows.append(
                    {
                        "top_k": top_k,
                        "user_id": case["user_id"],
                        "query_id": case["query"]["query_id"],
                        "query_mode": case["query"].get("query_mode", ""),
                        "query_subtype": case["query"].get("query_subtype", ""),
                        "query": case["query"]["query"],
                        "method": method,
                        "selected_event_ids": "|".join(item["event_id"] for item in selected_events),
                        "selected_event_titles": "|".join(item["title"] for item in selected_events),
                        "selected_event_scores": "|".join(str(item["score"]) for item in selected_events),
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
    parser.add_argument("--top-k-values", default="1,2,3")
    args = parser.parse_args()

    top_k_values = [args.top_k] if args.top_k is not None else parse_top_k_values(args.top_k_values)
    rows = run(args.input, args.output, top_k_values)
    print(f"wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
