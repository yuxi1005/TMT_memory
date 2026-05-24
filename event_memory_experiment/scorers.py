import math
import re
from datetime import datetime


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")
PREFERENCE_TYPES = {"preference", "habit", "profile"}
FACT_CONTEXT_TYPES = {"fact", "dependency", "constraint", "status_update"}

LAMBDA_BY_ROLE = {
    "profile": 0.005,
    "preference": 0.015,
    "habit": 0.025,
    "dependency": 0.030,
    "constraint": 0.035,
    "status_update": 0.035,
    "completed_todo": 0.035,
    "fact": 0.050,
}

QUADRANT_FACTORS = {
    "Q1": {"vf": 1.00, "if": 0.15},
    "Q2": {"vf": 0.90, "if": 0.03},
    "Q3": {"vf": 0.45, "if": 0.25},
    "Q4": {"vf": 0.25, "if": 0.05},
}


def parse_time(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def clamp01(value):
    return max(0.0, min(1.0, float(value)))


def tokenize(text):
    return set(token.lower() for token in TOKEN_RE.findall(text or ""))


def recency_score(timestamp_or_range, now):
    now_dt = parse_time(now)
    if isinstance(timestamp_or_range, dict):
        timestamp = timestamp_or_range.get("end") or timestamp_or_range.get("start")
    else:
        timestamp = timestamp_or_range
    ts = parse_time(timestamp)
    if not ts or not now_dt:
        return 0.0

    age_hours = max((now_dt - ts).total_seconds() / 3600.0, 0.0)
    return clamp01(math.exp(-age_hours / (24.0 * 10.0)))


def token_similarity_score(query_text, candidate_text):
    q_tokens = tokenize(query_text)
    c_tokens = tokenize(candidate_text)
    if not q_tokens or not c_tokens:
        return 0.0

    overlap = len(q_tokens & c_tokens)
    union = len(q_tokens | c_tokens)
    return clamp01(overlap / union)


def cosine_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return None
    dot = sum(float(a) * float(b) for a, b in zip(left, right))
    left_norm = math.sqrt(sum(float(a) * float(a) for a in left))
    right_norm = math.sqrt(sum(float(b) * float(b) for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return clamp01((dot / (left_norm * right_norm) + 1.0) / 2.0)


def token_boost(query_text, candidate_text, max_boost=0.18):
    q_tokens = tokenize(query_text)
    c_tokens = tokenize(candidate_text)
    if not q_tokens or not c_tokens:
        return 0.0

    overlap = q_tokens & c_tokens
    if not overlap:
        return 0.0
    long_overlap = [token for token in overlap if len(token) >= 4 or "_" in token]
    if long_overlap:
        return max_boost
    return min(0.08, max_boost)


def embedding_similarity_score(query=None, memory=None, query_text="", candidate_text=""):
    query_embedding = None
    if query:
        query_embedding = query.get("embedding") or query.get("query_embedding")
    memory_embedding = memory.get("embedding") if memory else None
    score = cosine_similarity(query_embedding, memory_embedding)
    if score is not None:
        return score
    return None


def bounded_similarity_score(query, memory, candidate_text=None, use_embedding=True):
    query_text = query.get("query", "") if isinstance(query, dict) else str(query or "")
    candidate_text = candidate_text if candidate_text is not None else memory.get("content", "")
    token_sim = token_similarity_score(query_text, candidate_text)
    boosted_token = token_sim + token_boost(query_text, candidate_text)
    if not use_embedding:
        return clamp01(boosted_token)
    embed_sim = embedding_similarity_score(query=query, memory=memory, query_text=query_text, candidate_text=candidate_text)
    if embed_sim is None:
        query_entities = []
        if isinstance(query, dict):
            query_entities = query.get("constraints", {}).get("entities", [])
        explicit_domain = memory.get("domain")
        entity_hit = bool(explicit_domain and explicit_domain in query_entities)
        profile_hit = explicit_domain == "profile" and "profile" in query_entities
        text_hit = any(entity and entity in candidate_text for entity in query_entities)
        if entity_hit or profile_hit or text_hit:
            embed_sim = 0.62
        elif token_sim > 0.0:
            embed_sim = 0.42
        else:
            embed_sim = 0.20
    return clamp01(max(boosted_token, embed_sim))


def similarity_score(query_text, candidate_text):
    return token_similarity_score(query_text, candidate_text)


def memory_role(memory):
    if memory.get("memory_type") == "todo" and memory.get("is_done") is False:
        return "active_todo"
    if memory.get("memory_type") == "todo" and memory.get("is_done") is True:
        return "completed_todo"
    memory_type = memory.get("memory_type") or "fact"
    if memory_type in PREFERENCE_TYPES:
        return "preference"
    if memory_type in FACT_CONTEXT_TYPES:
        return "fact_context"
    return memory_type


def age_days(memory, now):
    ts = parse_time(memory.get("timestamp"))
    now_dt = parse_time(now)
    if not ts or not now_dt:
        return None
    return max((now_dt - ts).total_seconds() / 86400.0, 0.0)


def delay_days(memory, now):
    ddl = parse_time(memory.get("ddl"))
    now_dt = parse_time(now)
    if not ddl or not now_dt:
        return None
    return (ddl - now_dt).total_seconds() / 86400.0


def eisenhower_quadrant(memory, now, importance_threshold=0.7, urgency_days=3.0):
    importance = float(memory.get("importance", 0.5))
    delay = delay_days(memory, now)
    urgent = delay is not None and delay <= urgency_days
    important = importance >= importance_threshold

    if important and urgent:
        return "Q1"
    if important and not urgent:
        return "Q2"
    if not important and urgent:
        return "Q3"
    return "Q4"


def tmt_q(
    memory,
    now,
    importance_threshold=0.7,
    urgency_days=3.0,
    overdue_alpha=0.10,
    use_eisenhower=True,
):
    if memory_role(memory) != "active_todo":
        return 0.0

    importance = float(memory.get("importance", 0.5))
    delay = delay_days(memory, now)
    if delay is None:
        return clamp01(importance * 0.5)

    delay_for_formula = max(delay, 0.0)
    quadrant = (
        eisenhower_quadrant(memory, now, importance_threshold, urgency_days)
        if use_eisenhower
        else "Q1"
    )
    factors = QUADRANT_FACTORS[quadrant]
    score = importance * factors["vf"] / (1.0 + factors["if"] * delay_for_formula)

    if delay < 0:
        score *= 1.0 + overdue_alpha * math.log1p(abs(delay))
    return clamp01(score)


def retrospective_decay(memory, now, role=None, lambda_by_role=None):
    role = role or memory_role(memory)
    lambda_by_role = lambda_by_role or LAMBDA_BY_ROLE
    importance = float(memory.get("importance", 0.5))
    age = age_days(memory, now)
    if age is None:
        return clamp01(importance * 0.5)

    lambda_role = role
    if role in {"fact_context", "preference"}:
        lambda_role = memory.get("memory_type") or role
    lambda_per_day = lambda_by_role.get(lambda_role, lambda_by_role["fact"])
    return clamp01(importance * math.exp(-lambda_per_day * age))


def accessibility(memory, now, **kwargs):
    role = memory_role(memory)
    if role == "active_todo":
        return tmt_q(memory, now, **kwargs)
    return retrospective_decay(memory, now, role=role)


def TMT_score(memory, now, **kwargs):
    return tmt_q(memory, now, **kwargs)


def forgetting_decay(memory, now, lambda_per_day=None):
    if lambda_per_day is not None:
        role = memory_role(memory)
        old = LAMBDA_BY_ROLE.get(role, LAMBDA_BY_ROLE["fact"])
        return retrospective_decay(memory, now, role=role, lambda_by_role={role: lambda_per_day, "fact": old})
    return retrospective_decay(memory, now)


def dependency_score(memory, all_memories):
    content = (memory.get("content") or "").lower()
    if any(word in content for word in ["before", "after", "depends", "requires", "signoff", "review", "blocks"]):
        return 0.2
    return 0.0
