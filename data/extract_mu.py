# extract_mu.py
# -*- coding: utf-8 -*-

"""
Extract current memory units from dialogue data using update-in-place.

Input:
  - outputs/dialogues/{user_id}_dialogues.json
  - prompts/提取mu和event.txt

Output:
  - outputs/mu/{user_id}_events.jsonl
  - outputs/mu/{user_id}_memory_units_current.jsonl
  - outputs/mu/{user_id}_extraction_log.jsonl

DeepSeek API key:
  export DEEPSEEK_API_KEY="your_api_key"

Example:
  py extract_mu.py L01
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =========================
# Config
# =========================

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DIALOGUES_DIR = BASE_DIR / "outputs" / "dialogues"
DEFAULT_PROMPT_PATH = BASE_DIR / "prompts" / "提取mu和event.txt"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs" / "mu"

IMPORTANCE_MAP = {
    1: 0.2,
    2: 0.4,
    3: 0.6,
    4: 0.8,
    5: 1.0,
}

TODO_CREATE_TYPES = {
    "create_task",
}

TODO_UPDATE_ACTIVE_TYPES = {
    "postpone_task",
}

NON_TODO_TYPES = {
    "complete_task",
    "cancel_task",
    "create_plan",
    "revise_plan",
    "replace_plan",
    "add_preference",
    "revise_preference",
    "add_constraint",
    "create_recurring_task",
    "complete_recurring_task_instance",
    "add_status_update",
    "introduce_noise",
    "unexpected_event",
    "revise_deadline",
    "update_priority",
}


# =========================
# Utility
# =========================

def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: str | Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_jsonl(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def safe_int(x: Any, default: Optional[int] = None) -> Optional[int]:
    try:
        if x is None:
            return default
        return int(x)
    except Exception:
        return default


def clamp_importance_level(level: Any) -> int:
    level_int = safe_int(level, 3)
    if level_int is None:
        return 3
    return max(1, min(5, level_int))


def lower_importance(importance: float, step: float = 0.2) -> float:
    return max(0.2, round(importance - step, 2))


def normalize_importance(level: Any) -> float:
    level_int = clamp_importance_level(level)
    return IMPORTANCE_MAP[level_int]


def dialogue_to_text(dialogue: List[Dict[str, str]]) -> str:
    parts = []
    for turn in dialogue:
        speaker = turn.get("speaker", "")
        text = turn.get("text", "")
        parts.append(f"{speaker}: {text}")
    return "\n".join(parts)


def strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text.strip()).strip()
    return text


def parse_model_json(text: str) -> Dict[str, Any]:
    raw = strip_json_fence(text)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract the first JSON object.
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


# =========================
# DDL extraction
# =========================

DAY_PATTERNS = [
    r"第\s*(\d+)\s*天前",
    r"第\s*(\d+)\s*天左右",
    r"第\s*(\d+)\s*天",
    r"截止(?:日)?(?:先)?(?:设到|放到|推到|延期到|顺延到)?\s*第?\s*(\d+)\s*天",
    r"推到\s*第?\s*(\d+)\s*天",
    r"延期到\s*第?\s*(\d+)\s*天",
    r"顺延到\s*第?\s*(\d+)\s*天",
    r"执行到\s*第?\s*(\d+)\s*天",
    r"阶段(?:目标|观察点|复盘日)?(?:先)?(?:看到|到|放到|顺延到)?\s*第?\s*(\d+)\s*天",
    r"下一次(?:复盘)?(?:先)?(?:排到|安排在|按|是)?\s*第?\s*(\d+)\s*天",
]


def extract_all_day_mentions(text: str) -> List[int]:
    days: List[int] = []
    for pat in DAY_PATTERNS:
        for m in re.finditer(pat, text):
            d = safe_int(m.group(1))
            if d is not None:
                days.append(d)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for d in days:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def choose_ddl_from_text(
    text: str,
    event_type: str,
    current_day: int,
    previous_ddl: Optional[int],
) -> Optional[int]:
    """
    Deterministic ddl choice.

    Principle:
    - For create/postpone/revise deadline, use explicit future day if possible.
    - For complete_task, inherit previous ddl.
    - For cancel_task and noise, use null.
    - For recurring completion, prefer future day after current_day.
    """
    days = extract_all_day_mentions(text)

    if event_type in {"introduce_noise"}:
        return None

    if event_type == "cancel_task":
        return None

    if event_type == "complete_task":
        return previous_ddl

    if not days:
        if event_type in {"postpone_task", "revise_deadline", "revise_plan"}:
            return previous_ddl
        return None

    future_days = [d for d in days if d >= current_day]

    if event_type in {
        "postpone_task",
        "revise_deadline",
        "revise_plan",
        "create_task",
        "create_plan",
        "add_constraint",
        "create_recurring_task",
        "complete_recurring_task_instance",
    }:
        if future_days:
            # Often the new deadline or next review is the largest future explicit day.
            return max(future_days)
        return max(days)

    # Fallback: prefer future day, otherwise latest mentioned day.
    if future_days:
        return max(future_days)
    return max(days)


# =========================
# DeepSeek call
# =========================

def call_deepseek(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system_prompt: str,
    user_payload: Dict[str, Any],
    temperature: float = 0.0,
    max_retries: int = 3,
    timeout: int = 60,
) -> Dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            },
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(
                url=url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return parse_model_json(content)
        except urllib.error.HTTPError as e:
            last_error = RuntimeError(
                f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            )
        except Exception as e:
            last_error = e

        if attempt < max_retries:
            time.sleep(1.5 * attempt)
        else:
            break

    raise RuntimeError(f"DeepSeek API failed after {max_retries} retries: {last_error}")


# =========================
# MU update rules
# =========================

def make_mu_id(user_id: str, index: int) -> str:
    return f"{user_id}_mu_{index:03d}"


def should_create_new_mu(event_type: str, target_id: Optional[str], target_to_mu: Dict[str, str]) -> bool:
    if not target_id:
        return True
    return target_id not in target_to_mu


def initial_istodo(event_type: str) -> bool:
    if event_type in TODO_CREATE_TYPES:
        return True
    if event_type in TODO_UPDATE_ACTIVE_TYPES:
        return True
    return False


def update_istodo(event_type: str, previous: Optional[Dict[str, Any]]) -> bool:
    if event_type in {"create_task", "postpone_task"}:
        return True
    if event_type in {"complete_task", "cancel_task"}:
        return False
    if previous is not None:
        # For plans/preferences/noise, usually keep false.
        # For revise_deadline/update_priority on a previous todo, preserve the todo state.
        if event_type in {"revise_deadline", "update_priority"}:
            return bool(previous.get("istodo", False))
    return False


def compute_importance(
    *,
    event_type: str,
    ai_importance_level: int,
    previous_mu: Optional[Dict[str, Any]],
) -> float:
    """
    Importance = intrinsic value.
    Do not update importance merely because ddl is near.

    Rules:
    - New MU: use AI score.
    - Postpone: inherit previous importance.
    - Complete: inherit previous importance.
    - Cancel: lower previous importance.
    - Replace old plan: lower previous importance.
    - Revise/update priority: use max(previous, AI) if AI signals higher value.
    """
    ai_value = IMPORTANCE_MAP[ai_importance_level]

    if previous_mu is None:
        return ai_value

    prev_value = float(previous_mu.get("importance", ai_value))

    if event_type in {"postpone_task", "complete_task"}:
        return prev_value

    if event_type in {"cancel_task", "replace_plan"}:
        return lower_importance(prev_value)

    if event_type in {"update_priority"}:
        return max(prev_value, ai_value)

    if event_type in {"revise_plan", "revise_preference", "revise_deadline", "add_status_update"}:
        # Allow upward adjustment only when AI clearly sees higher intrinsic value.
        return max(prev_value, ai_value)

    return prev_value


def build_event_title(event_type: str, content: str) -> str:
    type_title = {
        "create_task": "创建任务",
        "postpone_task": "任务延期",
        "complete_task": "完成任务",
        "cancel_task": "取消任务",
        "create_plan": "创建计划",
        "revise_plan": "修订计划",
        "replace_plan": "替换计划",
        "add_preference": "新增偏好",
        "revise_preference": "修订偏好",
        "add_constraint": "新增约束",
        "create_recurring_task": "创建重复事项",
        "complete_recurring_task_instance": "完成周期复盘",
        "add_status_update": "更新状态",
        "introduce_noise": "记录临时事项",
        "unexpected_event": "记录意外事件",
        "revise_deadline": "调整截止时间",
        "update_priority": "更新优先级",
    }.get(event_type, "记录事件")

    short = content.strip()
    if len(short) > 24:
        short = short[:24] + "..."
    return f"{type_title}：{short}"


def validate_ai_output(ai_out: Dict[str, Any]) -> Tuple[str, int, str, Optional[int]]:
    content = str(ai_out.get("content", "")).strip()
    if not content:
        content = "该交互包含一条需要记录的用户记忆，但模型未能生成有效内容。"

    level = clamp_importance_level(ai_out.get("importance_level", 3))

    reason = str(ai_out.get("importance_reason", "")).strip()
    if not reason:
        reason = "模型未提供重要性说明。"

    ddl_candidate = ai_out.get("ddl_candidate", None)
    ddl_candidate_int = safe_int(ddl_candidate, None)

    return content, level, reason, ddl_candidate_int


# =========================
# Main extraction
# =========================

def process_dialogues(
    *,
    input_path: str | Path,
    prompt_path: str | Path,
    outdir: str | Path,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    dry_run: bool = False,
) -> None:
    data = read_json(input_path)
    system_prompt = read_text(prompt_path)

    user_id = data["user_id"]
    interactions = data.get("interactions", [])

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    memory_store: Dict[str, Dict[str, Any]] = {}
    target_to_mu: Dict[str, str] = {}
    events: List[Dict[str, Any]] = []
    memory_units_all: List[Dict[str, Any]] = []
    extraction_log: List[Dict[str, Any]] = []

    mu_counter = 0

    for idx, interaction in enumerate(interactions, start=1):
        interaction_id = interaction.get("interaction_id")
        event_id = interaction.get("source_event_id") or f"e{idx:03d}"
        day = safe_int(interaction.get("day"), 0) or 0
        event_type = interaction.get("event_type", "other")
        target_id = interaction.get("target_id")
        dialogue = interaction.get("dialogue", [])
        dialogue_text = dialogue_to_text(dialogue)

        previous_mu: Optional[Dict[str, Any]] = None
        previous_mu_id: Optional[str] = None

        if target_id and target_id in target_to_mu:
            previous_mu_id = target_to_mu[target_id]
            previous_mu = memory_store[previous_mu_id]

        user_payload = {
            "user_id": user_id,
            "interaction": interaction,
            "previous_mu": previous_mu,
        }

        if dry_run:
            # For debugging pipeline without API call.
            ai_out = {
                "content": f"[DRY RUN] {dialogue_text[:80]}",
                "importance_level": 3,
                "importance_reason": "dry run",
                "ddl_candidate": None,
            }
        else:
            ai_out = call_deepseek(
                api_key=api_key,
                base_url=base_url,
                model=model,
                system_prompt=system_prompt,
                user_payload=user_payload,
            )

        content, importance_level, importance_reason, ai_ddl = validate_ai_output(ai_out)

        regex_ddl = choose_ddl_from_text(
            text=dialogue_text,
            event_type=event_type,
            current_day=day,
            previous_ddl=previous_mu.get("ddl") if previous_mu else None,
        )

        # Deterministic ddl priority:
        # regex explicit day > AI ddl candidate > previous / null according to event rule.
        ddl_warning = None
        if regex_ddl is not None:
            final_ddl = regex_ddl
            if ai_ddl is not None and ai_ddl != regex_ddl:
                ddl_warning = {
                    "type": "ddl_mismatch",
                    "ai_ddl": ai_ddl,
                    "regex_ddl": regex_ddl,
                    "decision": "use_regex_ddl",
                }
        else:
            final_ddl = ai_ddl

        # For complete/cancel rules, enforce final ddl behavior after fallback.
        if event_type == "complete_task" and previous_mu is not None:
            final_ddl = previous_mu.get("ddl")
        elif event_type == "cancel_task":
            final_ddl = None
        elif event_type == "introduce_noise":
            final_ddl = None

        create_new = should_create_new_mu(event_type, target_id, target_to_mu)

        if create_new:
            mu_counter += 1
            mu_id = make_mu_id(user_id, mu_counter)

            istodo = initial_istodo(event_type)
            importance = normalize_importance(importance_level)

            mu = {
                "id": mu_id,
                "eventid": event_id,
                "roleuserid": user_id,
                "content": content,
                "embedding": None,
                "timestamp": {"day": day},
                "istodo": istodo,
                "ddl": final_ddl,
                "importance": importance,
            }

            memory_store[mu_id] = mu
            if target_id:
                target_to_mu[target_id] = mu_id

            affected_mu_ids = [mu_id]

        else:
            assert previous_mu_id is not None
            assert previous_mu is not None

            mu_id = previous_mu_id

            istodo = update_istodo(event_type, previous_mu)
            importance = compute_importance(
                event_type=event_type,
                ai_importance_level=importance_level,
                previous_mu=previous_mu,
            )

            previous_mu.update(
                {
                    "eventid": event_id,
                    "content": content,
                    "timestamp": {"day": day},
                    "istodo": istodo,
                    "ddl": final_ddl,
                    "importance": importance,
                }
            )

            memory_store[mu_id] = previous_mu
            affected_mu_ids = [mu_id]

        event = {
            "id": event_id,
            "muids": affected_mu_ids,
            "title": build_event_title(event_type, content),
            "abstract": content,
        }
        events.append(event)
        
        all_mu = {
            "id": f"{user_id}_allmu_{idx:03d}",
            "eventid": event_id,
            "roleuserid": user_id,
            "content": content,
            "embedding": None,
            "timestamp": {"day": day},
            "istodo": istodo,
            "ddl": final_ddl,
            "importance": importance,
            "linked_current_mu_id": affected_mu_ids[0],
        }

        memory_units_all.append(all_mu)

        extraction_log.append(
            {
                "interaction_id": interaction_id,
                "event_id": event_id,
                "day": day,
                "event_type": event_type,
                "target_id": target_id,
                "previous_mu_id": previous_mu_id,
                "affected_mu_ids": affected_mu_ids,
                "ai_output": ai_out,
                "parsed": {
                    "content": content,
                    "importance_level": importance_level,
                    "importance": IMPORTANCE_MAP[importance_level],
                    "importance_reason": importance_reason,
                    "ai_ddl_candidate": ai_ddl,
                    "regex_ddl": regex_ddl,
                    "final_ddl": final_ddl,
                    "ddl_warning": ddl_warning,
                },
            }
        )

        print(
            f"[{idx:03d}/{len(interactions):03d}] "
            f"{interaction_id} {event_type} target={target_id} -> {affected_mu_ids}"
        )

    # Stable order by mu id number
    memory_units = sorted(memory_store.values(), key=lambda x: x["id"])

    events_path = outdir / f"{user_id}_events.jsonl"
    all_mus_path = outdir / f"{user_id}_memory_units_all.jsonl"
    mus_path = outdir / f"{user_id}_memory_units_current.jsonl"
    log_path = outdir / f"{user_id}_extraction_log.jsonl"

    write_jsonl(events_path, events)
    write_jsonl(all_mus_path, memory_units_all)
    write_jsonl(mus_path, memory_units)
    write_jsonl(log_path, extraction_log)

    print("\nDone.")
    print(f"Events: {events_path}")
    print(f"Current memory units: {mus_path}")
    print(f"Extraction log: {log_path}")
    print(f"Final MU count: {len(memory_units)}")
    print(f"Event count: {len(events)}")


def infer_user_id_from_input(input_path: str | Path) -> str:
    stem = Path(input_path).stem
    suffix = "_dialogues"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def build_default_input_path(user_id: str) -> Path:
    return DEFAULT_DIALOGUES_DIR / f"{user_id}_dialogues.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "user_id",
        nargs="?",
        help="User id, for example L01. Defaults input to outputs/dialogues/{user_id}_dialogues.json.",
    )
    parser.add_argument("--input", help="Path to dialogue JSON file. Overrides user_id default.")
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH), help="Path to prompt txt.")
    parser.add_argument("--outdir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory.")
    parser.add_argument("--api-key", default=os.getenv("DEEPSEEK_API_KEY"))
    parser.add_argument("--base-url", default=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL))
    parser.add_argument("--dry-run", action="store_true", help="Run without API calls.")
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
        user_id = args.user_id or infer_user_id_from_input(input_path)
    elif args.user_id:
        user_id = args.user_id
        input_path = build_default_input_path(user_id)
    else:
        parser.error("Provide user_id, for example: py extract_mu.py L01")

    prompt_path = Path(args.prompt)
    outdir = Path(args.outdir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input dialogue file not found: {input_path}")
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    if not args.dry_run and not args.api_key:
        raise ValueError(
            "Missing API key. Set DEEPSEEK_API_KEY or pass --api-key."
        )

    print(f"User: {user_id}")
    print(f"Input: {input_path}")
    print(f"Prompt: {prompt_path}")
    print(f"Output dir: {outdir}")

    process_dialogues(
        input_path=input_path,
        prompt_path=prompt_path,
        outdir=outdir,
        api_key=args.api_key or "",
        base_url=args.base_url,
        model=args.model,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
