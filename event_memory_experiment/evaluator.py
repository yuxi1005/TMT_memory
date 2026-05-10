import math
from datetime import datetime


def supporting_event_recall(pred_event_ids, gold_event_ids):
    if not gold_event_ids:
        return 1.0
    return len(set(pred_event_ids) & set(gold_event_ids)) / len(set(gold_event_ids))


def top1_accuracy(pred_event_ids, gold_event_ids):
    return 1.0 if pred_event_ids and pred_event_ids[0] in set(gold_event_ids) else 0.0


def top3_recall(pred_event_ids, gold_event_ids):
    return supporting_event_recall(pred_event_ids[:3], gold_event_ids)


def ndcg_at_3(pred_event_ids, case):
    event_gain = {}
    for item in case["query"].get("gold", []):
        memory = case["memories_by_id"].get(item["memory_id"])
        if not memory:
            continue
        event_id = memory["event_id"]
        event_gain[event_id] = max(event_gain.get(event_id, 0.0), float(item.get("relevance", 0)))

    gains = [event_gain.get(event_id, 0.0) for event_id in pred_event_ids[:3]]
    dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
    ideal = sorted(event_gain.values(), reverse=True)[:3]
    idcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(ideal))
    return 1.0 if idcg == 0 else dcg / idcg


def task_status_accuracy(pred_event_ids, case):
    if case["query"].get("query_mode") != "task":
        return None

    selected = set(pred_event_ids)
    gold_todo_events = set()
    for memory_id in case["gold_memory_ids"]:
        memory = case["memories_by_id"].get(memory_id)
        if memory and memory.get("memory_type") == "todo" and memory.get("is_done") is not True:
            gold_todo_events.add(memory["event_id"])

    if not gold_todo_events:
        return 1.0
    return len(selected & gold_todo_events) / len(gold_todo_events)


def token_cost(pred_event_ids, events_by_id, memories_by_id):
    total_chars = 0
    for event_id in pred_event_ids:
        event = events_by_id[event_id]
        total_chars += len(event.get("event_text", ""))
        for memory_id in event.get("memory_ids", []):
            total_chars += len(memories_by_id[memory_id].get("content", ""))
    return math.ceil(total_chars / 4)


def llm_can_answer(pred_event_ids, gold_event_ids):
    return 1.0 if set(gold_event_ids).issubset(set(pred_event_ids)) else 0.0


def evaluate_case(case, selected_events):
    pred_event_ids = [item["event_id"] for item in selected_events]
    gold_event_ids = case["gold_event_ids"]
    return {
        "supporting_event_recall": supporting_event_recall(pred_event_ids, gold_event_ids),
        "task_status_accuracy": task_status_accuracy(pred_event_ids, case),
        "top1_accuracy": top1_accuracy(pred_event_ids, gold_event_ids),
        "top3_recall": top3_recall(pred_event_ids, gold_event_ids),
        "NDCG@3": ndcg_at_3(pred_event_ids, case),
        "token_cost": token_cost(pred_event_ids, case["events_by_id"], case["memories_by_id"]),
        "llm_can_answer": llm_can_answer(pred_event_ids, gold_event_ids),
    }


def memory_recall_at_k(pred_memory_ids, gold_memory_ids):
    if not gold_memory_ids:
        return 1.0
    return len(set(pred_memory_ids) & set(gold_memory_ids)) / len(set(gold_memory_ids))


def memory_ndcg_at_k(pred_memory_ids, case, k):
    relevance = case["gold_relevance"]
    gains = [relevance.get(memory_id, 0.0) for memory_id in pred_memory_ids[:k]]
    dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(ideal))
    return 1.0 if idcg == 0 else dcg / idcg


def typed_memory_recall(pred_memory_ids, case, want_todo):
    gold = []
    for memory_id in case["gold_memory_ids"]:
        memory = case["memories_by_id"].get(memory_id)
        if not memory:
            continue
        is_todo = memory.get("memory_type") == "todo"
        if is_todo == want_todo:
            gold.append(memory_id)
    if not gold:
        return None
    return len(set(pred_memory_ids) & set(gold)) / len(set(gold))


def completed_task_error_rate(selected_memories, query):
    subtype = query.get("query_subtype", "")
    if subtype not in {"task_due", "task_priority"}:
        return None
    selected_todos = [memory for memory in selected_memories if memory.get("memory_type") == "todo"]
    if not selected_todos:
        return 0.0
    completed = [memory for memory in selected_todos if memory.get("is_done") is True]
    return len(completed) / len(selected_todos)


def todo_intrusion_rate(selected_memories, query):
    subtype = query.get("query_subtype", "")
    if subtype not in {"chat_preference", "chat_profile", "chat_history"}:
        return None
    if not selected_memories:
        return 0.0
    todos = [memory for memory in selected_memories if memory.get("memory_type") == "todo"]
    return len(todos) / len(selected_memories)


def wrong_domain_intrusion_rate(selected_memories, query):
    tag = query.get("hard_case_tag") or query.get("constraints", {}).get("hard_case_tag", "")
    if tag and "domain" not in tag and query.get("query_mode") != "task":
        return None
    if not selected_memories:
        return 0.0
    wrong = [memory for memory in selected_memories if memory.get("distractor_role") == "wrong_domain"]
    return len(wrong) / len(selected_memories)


def stale_memory_intrusion_rate(selected_memories, query):
    subtype = query.get("query_subtype", "")
    tag = query.get("hard_case_tag") or query.get("constraints", {}).get("hard_case_tag", "")
    if subtype not in {"chat_preference", "chat_profile", "chat_history", "task_context"} and "decay" not in tag:
        return None
    if not selected_memories:
        return 0.0
    stale_roles = {"old_preference", "old_plan", "stale_memory"}
    stale = [memory for memory in selected_memories if memory.get("distractor_role") in stale_roles]
    return len(stale) / len(selected_memories)


def completed_task_intrusion_rate(selected_memories, query):
    if query.get("query_mode") != "task":
        return None
    if not selected_memories:
        return 0.0
    completed = [
        memory
        for memory in selected_memories
        if memory.get("memory_type") == "todo" and memory.get("is_done") is True
    ]
    return len(completed) / len(selected_memories)


def parse_time(value):
    if value is None:
        return None
    return datetime.fromisoformat(str(value))


def deadline_ranking_accuracy(selected_memories, case):
    subtype = case["query"].get("query_subtype", "")
    if subtype not in {"task_due", "task_priority"}:
        return None

    gold_todos = []
    for memory_id in case["gold_memory_ids"]:
        memory = case["memories_by_id"].get(memory_id)
        if memory and memory.get("memory_type") == "todo" and memory.get("is_done") is not True and memory.get("ddl"):
            gold_todos.append(memory)
    if not gold_todos:
        return None

    earliest_gold = min(gold_todos, key=lambda memory: parse_time(memory.get("ddl")))["memory_id"]
    selected_todos = [memory for memory in selected_memories if memory.get("memory_type") == "todo"]
    if not selected_todos:
        return 0.0
    return 1.0 if selected_todos[0]["memory_id"] == earliest_gold else 0.0


def far_deadline_before_near_rate(selected_memories, case):
    subtype = case["query"].get("query_subtype", "")
    if subtype not in {"task_due", "task_priority"}:
        return None

    seen_near_gold = False
    gold_ids = set(case["gold_memory_ids"])
    for memory in selected_memories:
        if memory.get("memory_type") != "todo":
            continue
        if memory.get("memory_id") in gold_ids and memory.get("distractor_role") in {"near_deadline", None, ""}:
            seen_near_gold = True
        if not seen_near_gold and memory.get("distractor_role") == "far_deadline":
            return 1.0
    return 0.0


def memory_token_cost(selected_memories):
    total_chars = sum(len(memory.get("content", "")) for memory in selected_memories)
    return math.ceil(total_chars / 4)


def evaluate_memory_case(case, selected_memories):
    pred_memory_ids = [item["memory_id"] for item in selected_memories]
    full_memories = [case["memories_by_id"][memory_id] for memory_id in pred_memory_ids]
    k = len(pred_memory_ids)
    return {
        "memory_recall": memory_recall_at_k(pred_memory_ids, case["gold_memory_ids"]),
        "memory_NDCG": memory_ndcg_at_k(pred_memory_ids, case, k),
        "memory_top1_accuracy": 1.0 if pred_memory_ids and pred_memory_ids[0] in set(case["gold_memory_ids"]) else 0.0,
        "todo_recall": typed_memory_recall(pred_memory_ids, case, True),
        "non_todo_recall": typed_memory_recall(pred_memory_ids, case, False),
        "completed_task_error_rate": completed_task_error_rate(full_memories, case["query"]),
        "todo_intrusion_rate": todo_intrusion_rate(full_memories, case["query"]),
        "wrong_domain_intrusion_rate": wrong_domain_intrusion_rate(full_memories, case["query"]),
        "stale_memory_intrusion_rate": stale_memory_intrusion_rate(full_memories, case["query"]),
        "completed_task_intrusion_rate": completed_task_intrusion_rate(full_memories, case["query"]),
        "far_deadline_before_near_rate": far_deadline_before_near_rate(full_memories, case),
        "deadline_ranking_accuracy": deadline_ranking_accuracy(full_memories, case),
        "memory_token_cost": memory_token_cost(full_memories),
    }
