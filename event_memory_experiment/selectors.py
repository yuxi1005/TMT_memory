from scorers import (
    TMT_score,
    dependency_score,
    forgetting_decay,
    parse_time,
    recency_score,
    similarity_score,
    tokenize,
)

QUERY_GATES = {
    "task_due": {"semantic": 0.28, "access": 0.36, "compat": 0.18, "domain": 0.10, "base": 0.08},
    "task_priority": {"semantic": 0.28, "access": 0.26, "compat": 0.22, "domain": 0.14, "base": 0.10},
    "task_status": {"semantic": 0.32, "access": 0.16, "compat": 0.28, "domain": 0.14, "base": 0.10},
    "task_context": {"semantic": 0.40, "access": 0.10, "compat": 0.24, "domain": 0.18, "base": 0.08},
    "task_dependency": {"semantic": 0.34, "access": 0.14, "compat": 0.30, "domain": 0.14, "base": 0.08},
    "chat_preference": {"semantic": 0.34, "access": 0.20, "compat": 0.30, "domain": 0.08, "base": 0.08},
    "chat_profile": {"semantic": 0.34, "access": 0.18, "compat": 0.32, "domain": 0.08, "base": 0.08},
    "chat_history": {"semantic": 0.42, "access": 0.16, "compat": 0.20, "domain": 0.14, "base": 0.08},
    "mixed": {"semantic": 0.30, "access": 0.26, "compat": 0.24, "domain": 0.12, "base": 0.08},
    "negative": {"semantic": 0.45, "access": 0.05, "compat": 0.20, "domain": 0.20, "base": 0.10},
}

TYPE_COMPATIBILITY = {
    "task_due": {"todo": 1.0, "status_update": 0.65, "dependency": 0.55, "constraint": 0.45, "fact": 0.25},
    "task_priority": {"todo": 0.95, "status_update": 0.55, "dependency": 0.45, "constraint": 0.45, "fact": 0.25},
    "task_status": {"status_update": 1.0, "todo": 0.85, "fact": 0.45, "constraint": 0.35, "dependency": 0.35},
    "task_context": {"fact": 0.9, "dependency": 0.85, "constraint": 0.75, "status_update": 0.65, "todo": 0.45, "preference": 0.35},
    "task_dependency": {"dependency": 1.0, "constraint": 0.85, "todo": 0.55, "status_update": 0.5, "fact": 0.4},
    "chat_preference": {"preference": 1.0, "habit": 0.85, "profile": 0.45, "fact": 0.35, "status_update": 0.35},
    "chat_profile": {"profile": 1.0, "fact": 0.65, "habit": 0.55, "preference": 0.35},
    "chat_history": {"fact": 0.75, "preference": 0.65, "habit": 0.6, "profile": 0.55, "status_update": 0.55, "todo": 0.35},
    "mixed": {"todo": 0.8, "preference": 0.85, "habit": 0.75, "dependency": 0.75, "constraint": 0.7, "status_update": 0.7, "fact": 0.6, "profile": 0.55},
    "negative": {"todo": 0.0, "preference": 0.0, "profile": 0.0, "fact": 0.0, "habit": 0.0, "dependency": 0.0, "constraint": 0.0, "status_update": 0.0},
}


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
    return tau * __import__("math").log(sum(__import__("math").exp((v - m) / tau) for v in values)) + m


def rank_events(case, method, top_k=3):
    if method == "recency_only":
        return recency_only(case, top_k)
    if method == "similarity_only":
        return similarity_only(case, top_k)
    if method == "recency_similarity_hybrid":
        return recency_similarity_hybrid(case, top_k)
    if method == "proposed_TMT_decay_event_memory":
        return proposed_TMT_decay_event_memory(case, top_k)
    raise ValueError(f"Unknown selector method: {method}")


def rank_memories(case, method, top_k=10):
    if method == "recency_only":
        rows = recency_memory_rows(case)
    elif method == "similarity_only":
        rows = similarity_memory_rows(case)
    elif method == "recency_similarity_hybrid":
        rows = recency_similarity_memory_rows(case)
    elif method == "proposed_TMT_decay_event_memory":
        rows = proposed_memory_rows(case)
    else:
        raise ValueError(f"Unknown selector method: {method}")
    return _format_memory_rows(rows, top_k)


def recency_only(case, top_k=3):
    now = case["now"]
    rows = []
    for event in case["events"]:
        score = recency_score(event.get("time_range"), now)
        rows.append((event, score))
    return _format_rows(rows, top_k)


def similarity_only(case, top_k=3):
    query_text = case["query"]["query"]
    memories_by_id = case["memories_by_id"]
    rows = []
    for event in case["events"]:
        score = similarity_score(query_text, event_text(event, memories_by_id))
        rows.append((event, score))
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


def proposed_TMT_decay_event_memory(case, top_k=3):
    query = case["query"]
    query_text = query["query"]
    subtype = query.get("query_subtype") or query.get("query_mode", "chat")
    gate = QUERY_GATES.get(subtype, QUERY_GATES.get(query.get("query_mode", "chat"), QUERY_GATES["chat_history"]))
    now = case["now"]
    memories_by_id = case["memories_by_id"]
    decay_lambda = estimate_decay_lambda(case["memories"], now)
    rows = []

    for event in case["events"]:
        mu_scores = []
        for memory_id in event.get("memory_ids", []):
            memory = memories_by_id[memory_id]
            score = score_memory_qca(memory, query, event, now, gate, subtype, decay_lambda=decay_lambda)

            mu_scores.append(max(0.0, min(1.0, score)))

        rows.append((event, max(0.0, min(1.0, smooth_max(mu_scores)))))

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


def proposed_memory_rows(case):
    query = case["query"]
    subtype = query.get("query_subtype") or query.get("query_mode", "chat")
    gate = QUERY_GATES.get(subtype, QUERY_GATES.get(query.get("query_mode", "chat"), QUERY_GATES["chat_history"]))
    now = case["now"]
    decay_lambda = estimate_decay_lambda(case["memories"], now)
    rows = []
    for memory in case["memories"]:
        event = case["events_by_id"][memory["event_id"]]
        rows.append((memory, score_memory_qca(memory, query, event, now, gate, subtype, decay_lambda=decay_lambda)))
    return rows


def score_memory_qca(memory, query, event, now, gate, subtype, ablation="full_qca", decay_lambda=None):
    query_text = query["query"]
    semantic = similarity_score(query_text, memory.get("content", ""))
    importance = float(memory.get("importance", 0.5))
    accessible = float(memory.get("accessible_score", 0.5))
    access = memory_accessibility(memory, query, now, decay_lambda=decay_lambda)
    compat = type_compatibility(memory, subtype)
    domain = domain_match_score(query, memory, event)
    base = 0.5 * importance + 0.5 * accessible
    penalty = intent_penalty(query, memory, domain, ablation=ablation)

    return max(
        0.0,
        min(
            1.0,
            gate["semantic"] * semantic
            + gate["access"] * access
            + gate["compat"] * compat
            + gate["domain"] * domain
            + gate["base"] * base
            - penalty,
        ),
    )


def estimate_decay_lambda(memories, now, min_lambda=0.12, max_lambda=0.5):
    now_dt = parse_time(now)
    if not now_dt:
        return min_lambda

    ages = []
    for memory in memories:
        if memory.get("memory_type") == "todo":
            continue
        ts = parse_time(memory.get("timestamp"))
        if ts:
            ages.append(max((now_dt - ts).total_seconds() / 86400.0, 0.0))
    if not ages:
        return min_lambda

    span_days = max(max(ages), 1.0)
    half_life_days = max(span_days / 3.0, 1.0)
    decay_lambda = __import__("math").log(2.0) / half_life_days
    return max(min_lambda, min(max_lambda, decay_lambda))


def memory_accessibility(memory, query, now, decay_lambda=None):
    subtype = query.get("query_subtype", "")
    memory_type = memory.get("memory_type")
    if memory_type == "todo":
        return TMT_score(memory, now)
    return forgetting_decay(memory, now, lambda_per_day=decay_lambda or 0.12)


def type_compatibility(memory, subtype):
    table = TYPE_COMPATIBILITY.get(subtype, {})
    compat = table.get(memory.get("memory_type"), 0.15)
    content = (memory.get("content") or "").lower()

    if subtype == "chat_preference" and any(term in content for term in ["newer", "updated", "now", "recently", "新", "更新", "现在", "覆盖"]):
        compat = min(1.0, compat + 0.12)
    if subtype in {"task_dependency", "mixed"}:
        compat = min(1.0, compat + dependency_score(memory, []))
    return compat


def domain_match_score(query, memory, event):
    explicit_domain = memory.get("domain")
    query_entities = query.get("constraints", {}).get("entities", [])
    subtype = query.get("query_subtype", "")
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


def intent_penalty(query, memory, domain, ablation="full_qca"):
    subtype = query.get("query_subtype", "")
    penalty = 0.0

    if subtype in {"task_due", "task_priority"} and memory.get("is_done") is True:
        penalty += 0.22
    if subtype in {"task_due", "task_priority", "task_status", "task_context", "task_dependency"}:
        if (
            ablation != "wo_tmt"
            and memory.get("memory_type") == "todo"
            and TMT_score(memory, query.get("now")) > 0.7
            and domain < 0.05
        ):
            penalty += 0.18
    if subtype in {"chat_preference", "chat_profile"} and memory.get("memory_type") == "todo":
        penalty += 0.20

    content = (memory.get("content") or "").lower()
    if subtype == "chat_preference" and any(term in content for term in ["old preference", "older preference", "旧偏好", "过去"]):
        penalty += 0.12

    return penalty


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
            "is_done": memory.get("is_done"),
            "ddl": memory.get("ddl"),
            "content": memory.get("content", ""),
        }
        for memory, score in ranked[:top_k]
    ]
