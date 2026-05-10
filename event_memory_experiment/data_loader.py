import json
from pathlib import Path


def load_synthetic_users(path):
    """Load synthetic users from JSONL or pretty JSON."""
    path = Path(path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    data = json.loads(text)
    if isinstance(data, list):
        return data
    return [data]


def iter_query_cases(users):
    for user in users:
        events_by_id = {event["event_id"]: event for event in user["events"]}
        memories_by_id = {memory["memory_id"]: memory for memory in user["memories"]}

        for query in user["queries"]:
            yield {
                "user_id": user["user_id"],
                "now": query.get("now") or user.get("now"),
                "query": query,
                "events": user["events"],
                "memories": user["memories"],
                "events_by_id": events_by_id,
                "memories_by_id": memories_by_id,
                "gold_memory_ids": [item["memory_id"] for item in query.get("gold", [])],
                "gold_event_ids": query.get("gold_event_ids", []),
                "gold_relevance": {
                    item["memory_id"]: float(item.get("relevance", 0))
                    for item in query.get("gold", [])
                },
            }


def flatten_cases(path):
    users = load_synthetic_users(path)
    return list(iter_query_cases(users))
