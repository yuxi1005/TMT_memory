import argparse
import json
from copy import deepcopy
from pathlib import Path


def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, users):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for user in users:
            handle.write(json.dumps(user, ensure_ascii=False) + "\n")


def next_index(items, key):
    values = []
    for item in items:
        raw = str(item.get(key, ""))
        if raw and raw[-4:].isdigit():
            values.append(int(raw[-4:]))
    return max(values or [0]) + 1


def append_completed_todo_adversary(user):
    user = deepcopy(user)
    now = user.get("now") or "2026-05-06T09:00:00+08:00"
    event_index = next_index(user.get("events", []), "event_id")
    memory_index = next_index(user.get("memories", []), "memory_id")
    query_index = next_index(user.get("queries", []), "query_id")

    prefix = user["user_id"]
    event_id = f"{prefix}_e{event_index:04d}"
    active_id = f"{prefix}_m{memory_index:04d}"
    completed_id = f"{prefix}_m{memory_index + 1:04d}"
    context_id = f"{prefix}_m{memory_index + 2:04d}"
    query_id = f"{prefix}_q{query_index:04d}"
    domain = "adversarial_completed_todo_v2"

    event = {
        "event_id": event_id,
        "title": "adversarial completed todo role transition",
        "time_range": {
            "start": "2026-05-06T08:30:00+08:00",
            "end": "2026-05-06T08:30:00+08:00",
        },
        "event_text": "Adversarial completed todo pair with identical keywords but different done state.",
        "event_embedding": None,
        "memory_ids": [active_id, completed_id, context_id],
    }

    active_memory = {
        "memory_id": active_id,
        "content": "Active todo for adversarial_completed_todo_v2: submit evidence_table next.",
        "timestamp": "2026-05-05T09:00:00+08:00",
        "embedding": None,
        "event_id": event_id,
        "memory_type": "todo",
        "ddl": "2026-05-07T18:00:00+08:00",
        "importance": 0.90,
        "accessible_score": 0.80,
        "is_done": False,
        "domain": domain,
        "distractor_role": "active_target",
        "temporal_bucket": "recent",
    }
    completed_memory = {
        "memory_id": completed_id,
        "content": "Completed todo for adversarial_completed_todo_v2: submit evidence_table next.",
        "timestamp": "2026-05-06T08:00:00+08:00",
        "embedding": None,
        "event_id": event_id,
        "memory_type": "todo",
        "ddl": "2026-05-07T18:00:00+08:00",
        "importance": 0.95,
        "accessible_score": 0.95,
        "is_done": True,
        "domain": domain,
        "distractor_role": "completed_task",
        "temporal_bucket": "recent",
    }
    context_memory = {
        "memory_id": context_id,
        "content": "The completed adversarial_completed_todo_v2 evidence_table item should not count as the next action.",
        "timestamp": "2026-05-06T08:05:00+08:00",
        "embedding": None,
        "event_id": event_id,
        "memory_type": "constraint",
        "ddl": None,
        "importance": 0.70,
        "accessible_score": 0.70,
        "is_done": None,
        "domain": domain,
        "distractor_role": "",
        "temporal_bucket": "recent",
    }

    query = {
        "query_id": query_id,
        "query": "What should I do next for adversarial_completed_todo_v2 evidence_table?",
        "query_mode": "task",
        "query_subtype": "task_due",
        "now": now,
        "hard_case_tag": "adversarial_completed_todo_v2",
        "constraints": {
            "hard_case_tag": "adversarial_completed_todo_v2",
            "entities": [domain],
            "keywords": [
                "what",
                "should",
                "I",
                "do",
                "next",
                "adversarial_completed_todo_v2",
                "evidence_table",
            ],
        },
        "gold": [
            {"memory_id": active_id, "relevance": 3, "reason": "Active task with identical keywords."},
            {"memory_id": context_id, "relevance": 1, "reason": "Explains completed item should be ignored."},
        ],
        "gold_event_ids": [event_id],
        "answer_type": "ranked_tasks",
    }

    user.setdefault("events", []).append(event)
    user.setdefault("memories", []).extend([active_memory, completed_memory, context_memory])
    user.setdefault("queries", []).append(query)
    return user


def build(input_path, output_path):
    users = load_jsonl(input_path)
    users = [append_completed_todo_adversary(user) for user in users]
    write_jsonl(output_path, users)
    return len(users)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    count = build(args.input, args.output)
    print(f"wrote {count} users to {args.output}")


if __name__ == "__main__":
    main()
