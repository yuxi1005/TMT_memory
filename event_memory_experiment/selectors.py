import math

from scorers import (
    accessibility,
    bounded_similarity_score,
    clamp01,
    dependency_score,
    forgetting_decay,
    memory_role,
    recency_score,
    similarity_score,
    tmt_q,
    tokenize,
)


ROLE_INTENT_MATRIX = {
    "task_due": {
        "active_todo": 1.0,
        "completed_todo": 0.1,
        "fact_context": 0.2,
        "preference": 0.1,
    },
    "task_priority": {
        "active_todo": 1.0,
        "completed_todo": 0.1,
        "fact_context": 0.3,
        "preference": 0.1,
    },
    "task_status": {
        "active_todo": 0.8,
        "completed_todo": 0.8,
        "fact_context": 0.8,
        "preference": 0.2,
    },
    "task_context": {
        "active_todo": 0.4,
        "completed_todo": 0.8,
        "fact_context": 1.0,
        "preference": 0.3,
    },
    "task_dependency": {
        "active_todo": 0.8,
        "completed_todo": 0.6,
        "fact_context": 1.0,
        "preference": 0.2,
    },
    "chat_preference": {
        "active_todo": 0.1,
        "completed_todo": 0.4,
        "fact_context": 0.5,
        "preference": 1.0,
    },
    "chat_profile": {
        "active_todo": 0.1,
        "completed_todo": 0.5,
        "fact_context": 0.7,
        "preference": 1.0,
    },
    "chat_history": {
        "active_todo": 0.8,
        "completed_todo": 0.9,
        "fact_context": 1.0,
        "preference": 1.0,
    },
    "mixed": {
        "active_todo": 0.8,
        "completed_todo": 0.8,
        "fact_context": 0.9,
        "preference": 0.9,
    },
    "negative": {
        "active_todo": 0.0,
        "completed_todo": 0.0,
        "fact_context": 0.0,
        "preference": 0.0,
    },
}

TMT_QUERY_SUBTYPES = {"task_due", "task_priority", "task_status"}


def query_subtype(query):
    return query.get("query_subtype") or query.get("query_mode", "chat")


def event_text(event, memories_by_id=None):
    parts = [event.get("title", ""), event.get("event_text", "")]
    if memories_by_id:
        for memory_id in event.get("memory_ids", []):
            memory = memories_by_id.get(memory_id)
            if memory:
                parts.append(memory.get("content", ""))
    return " ".join(parts)


def smooth_max(values, tau=0.15):
    if not values:
        return 0.0
    m = max(values)
    if tau <= 0:
        return m
    mean_exp = sum(math.exp((value - m) / tau) for value in values) / len(values)
    return m + tau * math.log(mean_exp)


def intent_gate(query, memory, disabled=False):
    if disabled:
        return 1.0
    matrix = ROLE_INTENT_MATRIX.get(query_subtype(query), ROLE_INTENT_MATRIX["chat_history"])
    return matrix.get(memory_role(memory), 0.4)


def domain_gate(query, memory, event, disabled=False):
    if disabled:
        return 1.0

    explicit_domain = memory.get("domain")
    query_entities = query.get("constraints", {}).get("entities", [])
    subtype = query_subtype(query)
    if explicit_domain and query_entities:
        if explicit_domain in query_entities:
            return 1.2
        if explicit_domain == "profile" and subtype in {"chat_preference", "chat_profile", "chat_history", "mixed"}:
            return 1.2
        return 0.05

    query_tokens = tokenize(query.get("query", ""))
    if not query_tokens:
        return 1.0
    text = " ".join([memory.get("content", ""), event.get("title", ""), event.get("event_text", "")])
    text_tokens = tokenize(text)
    if not text_tokens:
        return 1.0
    overlap = query_tokens & text_tokens
    return 1.2 if any("_" in token or len(token) >= 6 for token in overlap) else 1.0


def memory_accessibility(
    memory,
    query,
    now,
    ablation="full_core",
    disable_role_transition=False,
):
    role = memory_role(memory)

    if disable_role_transition and memory.get("memory_type") == "todo":
        role = "active_todo"

    if role == "active_todo":
        if ablation != "wo_tmt_condition" and query_subtype(query) not in TMT_QUERY_SUBTYPES:
            return forgetting_decay(memory, now)
        if ablation == "wo_tmt":
            return clamp01(memory.get("accessible_score", 0.5))
        tmt_memory = {**memory, "is_done": False} if disable_role_transition else memory
        return tmt_q(tmt_memory, now, use_eisenhower=ablation != "wo_eisenhower")

    if ablation == "wo_decay":
        return clamp01(memory.get("accessible_score", 0.5))
    return accessibility(memory, now)


def score_memory_core(memory, query, event, now, ablation="full_core"):
    semantic = bounded_similarity_score(query, memory, use_embedding=ablation != "wo_embedding")
    gate = intent_gate(query, memory, disabled=ablation == "wo_role_matrix")
    domain = domain_gate(query, memory, event, disabled=ablation == "wo_domain_gate")
    disable_role_transition = ablation == "wo_role_transition"
    access = memory_accessibility(
        memory,
        query,
        now,
        ablation=ablation,
        disable_role_transition=disable_role_transition,
    )
    score = semantic * gate * domain * access

    return clamp01(score)


def rank_events(case, method, top_k=3):
    if method == "recency_only":
        return recency_only(case, top_k)
    if method == "similarity_only":
        return similarity_only(case, top_k)
    if method == "recency_similarity_hybrid":
        return recency_similarity_hybrid(case, top_k)
    if method in {"proposed_TMT_decay_event_memory", "proposed_theory_core"}:
        return proposed_TMT_decay_event_memory(case, top_k)
    raise ValueError(f"Unknown selector method: {method}")


def rank_memories(case, method, top_k=10):
    if method == "recency_only":
        rows = recency_memory_rows(case)
    elif method == "similarity_only":
        rows = similarity_memory_rows(case)
    elif method == "recency_similarity_hybrid":
        rows = recency_similarity_memory_rows(case)
    elif method in {"proposed_TMT_decay_event_memory", "proposed_theory_core"}:
        rows = proposed_memory_rows(case)
    else:
        raise ValueError(f"Unknown selector method: {method}")
    return _format_memory_rows(rows, top_k)


def recency_only(case, top_k=3):
    now = case["now"]
    return _format_rows([(event, recency_score(event.get("time_range"), now)) for event in case["events"]], top_k)


def similarity_only(case, top_k=3):
    query_text = case["query"]["query"]
    memories_by_id = case["memories_by_id"]
    rows = []
    for event in case["events"]:
        rows.append((event, similarity_score(query_text, event_text(event, memories_by_id))))
    return _format_rows(rows, top_k)


def recency_similarity_hybrid(case, top_k=3):
    query_text = case["query"]["query"]
    now = case["now"]
    memories_by_id = case["memories_by_id"]
    rows = []
    for event in case["events"]:
        sim = similarity_score(query_text, event_text(event, memories_by_id))
        rec = recency_score(event.get("time_range"), now)
        rows.append((event, 0.55 * sim + 0.45 * rec))
    return _format_rows(rows, top_k)


def proposed_TMT_decay_event_memory(case, top_k=3, ablation="full_core"):
    query = case["query"]
    now = case["now"]
    memories_by_id = case["memories_by_id"]
    rows = []

    for event in case["events"]:
        mu_scores = []
        for memory_id in event.get("memory_ids", []):
            memory = memories_by_id.get(memory_id)
            if not memory:
                continue
            score = score_memory_core(memory, query, event, now, ablation=ablation)
            mu_scores.append(score)

        aggregate = max(mu_scores) if ablation == "wo_smoothmax" else smooth_max(mu_scores)
        rows.append((event, clamp01(aggregate)))

    return _format_rows(rows, top_k)


def recency_memory_rows(case):
    now = case["now"]
    return [(memory, recency_score(memory.get("timestamp"), now)) for memory in case["memories"]]


def similarity_memory_rows(case):
    query_text = case["query"]["query"]
    return [(memory, similarity_score(query_text, memory.get("content", ""))) for memory in case["memories"]]


def recency_similarity_memory_rows(case):
    query_text = case["query"]["query"]
    now = case["now"]
    rows = []
    for memory in case["memories"]:
        sim = similarity_score(query_text, memory.get("content", ""))
        rec = recency_score(memory.get("timestamp"), now)
        rows.append((memory, 0.55 * sim + 0.45 * rec))
    return rows


def proposed_memory_rows(case, ablation="full_core"):
    query = case["query"]
    now = case["now"]
    rows = []
    for memory in case["memories"]:
        event = case["events_by_id"].get(memory.get("event_id"), {})
        rows.append((memory, score_memory_core(memory, query, event, now, ablation=ablation)))
    return rows


def type_compatibility(memory, subtype):
    role = memory_role(memory)
    if subtype in {"task_due", "task_priority"}:
        return 1.0 if role == "active_todo" else 0.2
    if subtype in {"chat_preference", "chat_profile", "chat_history"}:
        return 0.1 if role == "active_todo" else 1.0
    if subtype == "task_dependency":
        return 1.0 if role == "dependency" or dependency_score(memory, []) else 0.5
    if subtype == "negative":
        return 0.0
    return 0.8


def domain_match_score(query, memory, event):
    explicit_domain = memory.get("domain")
    query_entities = query.get("constraints", {}).get("entities", [])
    subtype = query_subtype(query)
    if explicit_domain and query_entities:
        if explicit_domain in query_entities:
            return 1.0
        if explicit_domain == "profile" and subtype in {"chat_preference", "chat_profile", "chat_history", "mixed"}:
            return 1.0
        return 0.0

    query_tokens = tokenize(query.get("query", ""))
    if not query_tokens:
        return 0.0

    text = " ".join([memory.get("content", ""), event.get("title", ""), event.get("event_text", "")])
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0

    overlap = query_tokens & text_tokens
    if not overlap:
        return 0.0
    return min(1.0, len(overlap) / max(1.0, min(len(query_tokens), 6)))


def intent_penalty(query, memory, domain, ablation="full_core"):
    subtype = query_subtype(query)
    penalty = 0.0
    if subtype in {"task_due", "task_priority"} and memory_role(memory) == "completed_todo":
        penalty += 0.22
    if subtype in {"chat_preference", "chat_profile"} and memory_role(memory) == "active_todo":
        penalty += 0.20

    content = (memory.get("content") or "").lower()
    if subtype == "chat_preference" and any(term in content for term in ["old preference", "older preference"]):
        penalty += 0.12
    return penalty


def score_memory_qca(memory, query, event, now, gate=None, subtype=None, ablation="full_core", decay_lambda=None):
    return score_memory_core(memory, query, event, now, ablation=ablation)


def _format_rows(rows, top_k):
    ranked = sorted(rows, key=lambda item: item[1], reverse=True)
    return [
        {
            "event_id": event["event_id"],
            "score": round(float(score), 6),
            "title": event.get("title", ""),
        }
        for event, score in ranked[:top_k]
    ]


def _format_memory_rows(rows, top_k):
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
