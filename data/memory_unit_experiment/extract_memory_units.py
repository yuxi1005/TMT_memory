from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_INPUT_DIR = Path("outputs/dialogues")
DEFAULT_MU_OUTPUT = Path("memory_unit_experiment/small_memory_units.jsonl")
DEFAULT_EVENT_OUTPUT = Path("memory_unit_experiment/small_events.jsonl")
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"


TODO_ROLES = {
    "active_todo",
    "important_not_urgent_task",
    "urgent_low_value_task",
    "postponed_task",
    "recurring_task",
    "completed_todo",
    "cancelled_task",
}

EVENT_TO_STATUS = {
    "complete_task": "completed",
    "complete_recurring_task_instance": "completed",
    "cancel_task": "cancelled",
    "postpone_task": "postponed",
    "create_task": "open",
    "create_recurring_task": "open",
    "update_priority": "open",
    "revise_deadline": "open",
}


@dataclass
class MemoryUnit:
    id: str
    event_id: str
    role: str
    user_id: str
    content: str
    embedding: list[float] | None
    timestamp: int
    is_todo: bool
    ddl: int | None
    status: str | None
    retrieval_role: str
    importance: float


@dataclass
class Event:
    id: str
    muids: list[str]
    title: str
    abstract: str


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def dialogue_lines(dialogue: list[dict[str, str]]) -> list[str]:
    lines = []
    for turn in dialogue:
        speaker = turn.get("speaker", "unknown")
        text = normalize_text(turn.get("text", ""))
        if text:
            lines.append(f"{speaker}: {text}")
    return lines


def raw_dialogue_text(interaction: dict[str, Any]) -> str:
    return "\n".join(dialogue_lines(interaction.get("dialogue", [])))


def is_todo_memory(retrieval_role: str, event_type: str) -> bool:
    return retrieval_role in TODO_ROLES or "task" in event_type


def infer_status(event_type: str, retrieval_role: str) -> str | None:
    if retrieval_role == "completed_todo":
        return "completed"
    if retrieval_role == "cancelled_task":
        return "cancelled"
    if retrieval_role == "postponed_task":
        return "postponed"
    return EVENT_TO_STATUS.get(event_type)


def infer_importance(retrieval_role: str, event_type: str) -> float:
    if retrieval_role in {"active_todo", "important_not_urgent_task", "completed_todo"}:
        return 0.8
    if retrieval_role in {"stable_preference", "updated_preference", "current_constraint"}:
        return 0.7
    if retrieval_role in {"urgent_low_value_task", "noise", "outdated_status", "stale_plan"}:
        return 0.3
    if event_type in {"create_plan", "replace_plan", "revise_plan"}:
        return 0.6
    return 0.5


def infer_ddl(interaction: dict[str, Any]) -> int | None:
    text = " ".join(
        [
            interaction.get("dialogue_style", ""),
            raw_dialogue_text(interaction),
        ]
    )
    patterns = [
        r"截止(?:先)?(?:大概|时间)?(?:放到|为|到|是)?第\s*(\d+)\s*天",
        r"第\s*(\d+)\s*天(?:前|左右|之前)?(?:完成|交|截止|看看)",
        r"做到第\s*(\d+)\s*天",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def fallback_content(interaction: dict[str, Any]) -> str:
    lines = dialogue_lines(interaction.get("dialogue", []))
    user_lines = [line.removeprefix("user: ") for line in lines if line.startswith("user: ")]
    assistant_lines = [line.removeprefix("assistant: ") for line in lines if line.startswith("assistant: ")]
    parts = []
    if user_lines:
        parts.append("用户：" + " ".join(user_lines))
    if assistant_lines:
        parts.append("助手记录：" + assistant_lines[-1])
    return normalize_text(" ".join(parts))


def extract_content_with_deepseek(
    interaction: dict[str, Any],
    api_key: str,
    model: str,
    timeout: int,
    max_retries: int,
) -> str:
    prompt = {
        "interaction_id": interaction.get("interaction_id"),
        "event_type": interaction.get("event_type"),
        "target_id": interaction.get("target_id"),
        "retrieval_role": interaction.get("retrieval_role"),
        "dialogue": interaction.get("dialogue", []),
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个长期记忆抽取器。请从单次 interaction 的 dialogue 中抽取一个极简 memory unit content。"
                "只输出 JSON，格式为 {\"content\":\"...\"}。"
                "content 应该是中文短句，保留用户明确表达的任务、偏好、计划、状态或事实；"
                "不要编造 dialogue 中没有的信息；不要输出 id、ddl、status 等结构字段。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(prompt, ensure_ascii=False),
        },
    ]
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        DEEPSEEK_CHAT_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            content = normalize_text(parsed.get("content", ""))
            if content:
                return content
            raise ValueError("DeepSeek returned empty content")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
            if attempt >= max_retries:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("unreachable")


def build_memory_unit(
    user_id: str,
    interaction: dict[str, Any],
    use_ai: bool,
    api_key: str | None,
    model: str,
    timeout: int,
    max_retries: int,
) -> MemoryUnit:
    interaction_id = interaction["interaction_id"]
    event_id = interaction.get("source_event_id", interaction_id)
    event_type = interaction.get("event_type", "")
    retrieval_role = interaction.get("retrieval_role", "")
    todo = is_todo_memory(retrieval_role, event_type)

    if use_ai:
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is required when --use-ai is set")
        content = extract_content_with_deepseek(interaction, api_key, model, timeout, max_retries)
    else:
        content = fallback_content(interaction)

    return MemoryUnit(
        id=f"{user_id}_{interaction_id}_mu001",
        event_id=event_id,
        role=retrieval_role,
        user_id=user_id,
        content=content,
        embedding=None,
        timestamp=int(interaction.get("day", 0)),
        is_todo=todo,
        ddl=infer_ddl(interaction) if todo else None,
        status=infer_status(event_type, retrieval_role) if todo else None,
        retrieval_role=retrieval_role,
        importance=infer_importance(retrieval_role, event_type),
    )


def build_event(interaction: dict[str, Any], mu: MemoryUnit) -> Event:
    event_id = interaction.get("source_event_id", interaction["interaction_id"])
    title = normalize_text(interaction.get("dialogue_style", "")) or interaction.get("target_id", event_id)
    return Event(
        id=event_id,
        muids=[mu.id],
        title=title,
        abstract=mu.content,
    )


def extract_from_file(
    path: Path,
    max_interactions: int | None,
    use_ai: bool,
    api_key: str | None,
    model: str,
    timeout: int,
    max_retries: int,
) -> tuple[list[MemoryUnit], list[Event]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    user_id = data["user_id"]
    interactions = data.get("interactions", [])
    if max_interactions is not None:
        interactions = interactions[:max_interactions]

    memory_units: list[MemoryUnit] = []
    events: list[Event] = []
    for interaction in interactions:
        mu = build_memory_unit(user_id, interaction, use_ai, api_key, model, timeout, max_retries)
        memory_units.append(mu)
        events.append(build_event(interaction, mu))
    return memory_units, events


def run(
    input_dir: Path,
    mu_output: Path,
    event_output: Path,
    max_users: int,
    max_interactions: int | None,
    use_ai: bool,
    model: str,
    timeout: int,
    max_retries: int,
) -> tuple[int, int]:
    files = sorted(input_dir.glob("*_dialogues.json"))[:max_users]
    api_key = os.getenv("DEEPSEEK_API_KEY")
    mu_output.parent.mkdir(parents=True, exist_ok=True)
    event_output.parent.mkdir(parents=True, exist_ok=True)

    mu_count = 0
    event_count = 0
    with mu_output.open("w", encoding="utf-8") as mu_file, event_output.open("w", encoding="utf-8") as event_file:
        for path in files:
            memory_units, events = extract_from_file(
                path=path,
                max_interactions=max_interactions,
                use_ai=use_ai,
                api_key=api_key,
                model=model,
                timeout=timeout,
                max_retries=max_retries,
            )
            for mu in memory_units:
                mu_file.write(json.dumps(asdict(mu), ensure_ascii=False) + "\n")
                mu_count += 1
            for event in events:
                event_file.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
                event_count += 1
    return mu_count, event_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract small-sample Memory Units and Events from dialogue JSON files.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--mu-output", type=Path, default=DEFAULT_MU_OUTPUT)
    parser.add_argument("--event-output", type=Path, default=DEFAULT_EVENT_OUTPUT)
    parser.add_argument("--max-users", type=int, default=2)
    parser.add_argument("--max-interactions", type=int, default=8)
    parser.add_argument("--use-ai", action="store_true", help="Use DeepSeek to extract MU content from dialogue.")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()

    mu_count, event_count = run(
        input_dir=args.input_dir,
        mu_output=args.mu_output,
        event_output=args.event_output,
        max_users=args.max_users,
        max_interactions=args.max_interactions,
        use_ai=args.use_ai,
        model=args.model,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )
    print(f"wrote {mu_count} memory units to {args.mu_output}")
    print(f"wrote {event_count} events to {args.event_output}")


if __name__ == "__main__":
    main()
