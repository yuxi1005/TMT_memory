import math
import re
from datetime import datetime


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


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


def similarity_score(query_text, candidate_text):
    q_tokens = tokenize(query_text)
    c_tokens = tokenize(candidate_text)
    if not q_tokens or not c_tokens:
        return 0.0

    overlap = len(q_tokens & c_tokens)
    union = len(q_tokens | c_tokens)
    return clamp01(overlap / union)


def TMT_score(memory, now, plateau_days=3.0):
    if memory.get("memory_type") != "todo":
        return 0.0
    if memory.get("is_done") is True:
        return 0.05 * float(memory.get("importance", 0.5))

    ddl = parse_time(memory.get("ddl"))
    now_dt = parse_time(now)
    importance = float(memory.get("importance", 0.5))
    if not ddl or not now_dt:
        return clamp01(importance * 0.5)

    hours_to_deadline = (ddl - now_dt).total_seconds() / 3600.0
    if hours_to_deadline >= 0:
        delay_days = max(hours_to_deadline / 24.0, 0.0)
        if delay_days > plateau_days:
            deadline_activation = 0.8
        else:
            urgency = 1.0 - (delay_days / max(plateau_days, 0.01))
            deadline_activation = 0.8 + 0.2 * urgency
    else:
        overdue_days = abs(hours_to_deadline) / 24.0
        deadline_activation = min(1.0, 0.75 + 0.08 * math.log1p(overdue_days))

    return clamp01(importance * deadline_activation)


def forgetting_decay(memory, now, lambda_per_day=0.12):
    if memory.get("memory_type") == "todo":
        return 1.0

    ts = parse_time(memory.get("timestamp"))
    now_dt = parse_time(now)
    if not ts or not now_dt:
        return 0.5

    age_days = max((now_dt - ts).total_seconds() / 86400.0, 0.0)
    return clamp01(math.exp(-lambda_per_day * age_days))


def dependency_score(memory, all_memories):
    content = (memory.get("content") or "").lower()
    if any(word in content for word in ["before", "after", "depends", "requires", "signoff", "review"]):
        return 0.2
    return 0.0
