import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI


# =========================
# 1. 配置区：你主要改这里
# =========================

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("KMSOFT_API_KEY")
MODEL = "gpt-5.5"  # 如果你的 API 项目里模型名不同，改这一行

BASE_DIR = Path(r"E:\MyDatum\小论文\Codex")

PROFILES_DIR = Path(r"E:\MyDatum\小论文\Codex\data\outputs\profiles")
TIMELINES_DIR = Path(r"E:\MyDatum\小论文\Codex\data\outputs\timelines")
DIALOGUES_DIR = Path(r"E:\MyDatum\小论文\Codex\data\outputs\dialogues")
PROMPT_TXT = Path(r"E:\MyDatum\小论文\Codex\data\generate_dialogues.txt")

USER_IDS = (
    [f"S{i:02d}" for i in range(1, 11)]
    + [f"P{i:02d}" for i in range(1, 11)]
    + [f"L{i:02d}" for i in range(1, 11)]
)


# =========================
# 2. 文件读取工具
# =========================

def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_profile_file(user_id: str) -> Optional[Path]:
    """
    兼容几种常见命名：
    S04.json
    S04_profile.json
    S04_enriched_profile.json
    user_profiles_enriched.json
    """
    candidates = [
        PROFILES_DIR / f"{user_id}.json",
        PROFILES_DIR / f"{user_id}_profile.json",
        PROFILES_DIR / f"{user_id}_enriched_profile.json",
        PROFILES_DIR / "user_profiles_enriched.json",
        PROFILES_DIR / "profiles_enriched.json",
    ]

    for p in candidates:
        if p.exists():
            return p

    return None


def load_profile(user_id: str) -> Dict[str, Any]:
    profile_file = find_profile_file(user_id)
    if profile_file is None:
        raise FileNotFoundError(f"找不到 {user_id} 的 profile 文件，请检查 {PROFILES_DIR}")

    data = read_json(profile_file)

    # 情况 1：单个用户 profile
    if isinstance(data, dict) and data.get("user_id") == user_id:
        return data

    # 情况 2：profile 文件是一个 list
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("user_id") == user_id:
                return item

    # 情况 3：profile 文件是 {"profiles": [...]}
    if isinstance(data, dict) and isinstance(data.get("profiles"), list):
        for item in data["profiles"]:
            if isinstance(item, dict) and item.get("user_id") == user_id:
                return item

    raise ValueError(f"在 {profile_file} 中找不到 user_id={user_id}")


def find_timeline_file(user_id: str) -> Path:
    candidates = [
        TIMELINES_DIR / f"{user_id}_timeline.json",
        TIMELINES_DIR / f"{user_id}_latent_world_timeline.json",
        TIMELINES_DIR / f"{user_id}.json",
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(f"找不到 {user_id} 的 timeline 文件，请检查 {TIMELINES_DIR}")


def load_timeline(user_id: str) -> Dict[str, Any]:
    path = find_timeline_file(user_id)
    data = read_json(path)

    if not isinstance(data, dict):
        raise ValueError(f"{path} 不是 JSON object")

    if data.get("user_id") != user_id:
        raise ValueError(f"{path} 的 user_id 不是 {user_id}，实际是 {data.get('user_id')}")

    return data


# =========================
# 3. Prompt 拼接
# =========================

def build_prompt(user_id: str, profile: Dict[str, Any], timeline: Dict[str, Any]) -> str:
    base_prompt = read_text(PROMPT_TXT)

    # 支持你的 txt 里使用 {{USER_ID}} 占位符
    base_prompt = base_prompt.replace("{{USER_ID}}", user_id)

    payload = {
        "user_profile": profile,
        "timeline": timeline,
    }

    return f"""{base_prompt}

====================
实际输入数据
====================

下面是当前要处理的 user profile 和 timeline。

请只处理 user_id = {user_id}。

请严格输出合法 JSON，不要输出解释。

INPUT_JSON:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


# =========================
# 4. API 调用与 JSON 清洗
# =========================

def extract_json_object(text: str) -> Dict[str, Any]:
    """
    尽量从模型输出中提取 JSON object。
    如果模型严格只输出 JSON，这一步会直接成功。
    """
    text = text.strip()

    # 去掉可能的 ```json 包裹
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 兜底：截取第一个 { 到最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型输出中找不到 JSON object")

    candidate = text[start:end + 1]
    return json.loads(candidate)


def call_openai(prompt: str) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Missing API key. Set OPENAI_API_KEY or KMSOFT_API_KEY.")

    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.kmsoft.top/"
    )

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        temperature=0.4,
    )

    text = getattr(response, "output_text", None)

    if not text:
        chunks = []
        for item in getattr(response, "output", []):
            for content in getattr(item, "content", []):
                if getattr(content, "type", None) == "output_text":
                    chunks.append(content.text)
        text = "\n".join(chunks)

    if not text:
        raise RuntimeError("API 返回为空，无法解析")

    return extract_json_object(text)

# =========================
# 5. 简单校验
# =========================

def validate_dialogue_json(user_id: str, timeline: Dict[str, Any], dialogue_data: Dict[str, Any]) -> None:
    if dialogue_data.get("user_id") != user_id:
        raise ValueError(f"输出 user_id 不匹配：期望 {user_id}，实际 {dialogue_data.get('user_id')}")

    interactions = dialogue_data.get("interactions")
    if not isinstance(interactions, list):
        raise ValueError("输出缺少 interactions list")

    event_count = len(timeline.get("events", []))
    interaction_count = len(interactions)

    if interaction_count != event_count:
        raise ValueError(f"interaction 数量不匹配：timeline 有 {event_count} 个 events，输出有 {interaction_count} 个 interactions")

    event_ids = [e.get("event_id") for e in timeline.get("events", [])]
    interaction_event_ids = [i.get("source_event_id") for i in interactions]

    missing = set(event_ids) - set(interaction_event_ids)
    extra = set(interaction_event_ids) - set(event_ids)

    if missing:
        raise ValueError(f"缺少这些 event 的 interaction：{sorted(missing)}")

    if extra:
        raise ValueError(f"出现 timeline 中不存在的 source_event_id：{sorted(extra)}")

    for idx, interaction in enumerate(interactions, start=1):
        dialogue = interaction.get("dialogue")
        if not isinstance(dialogue, list) or not dialogue:
            raise ValueError(f"第 {idx} 个 interaction 缺少 dialogue")

        for turn in dialogue:
            if turn.get("speaker") not in {"user", "assistant"}:
                raise ValueError(f"第 {idx} 个 interaction 有非法 speaker：{turn.get('speaker')}")
            if not isinstance(turn.get("text"), str) or not turn["text"].strip():
                raise ValueError(f"第 {idx} 个 interaction 有空文本")


# =========================
# 6. 单用户生成
# =========================

def generate_one_user(user_id: str, overwrite: bool = False) -> Path:
    DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)

    output_path = DIALOGUES_DIR / f"{user_id}_dialogues.json"

    if output_path.exists() and not overwrite:
        print(f"[SKIP] {user_id}: 已存在 {output_path}")
        return output_path

    print(f"[LOAD] {user_id}: profile + timeline")
    profile = load_profile(user_id)
    timeline = load_timeline(user_id)

    print(f"[PROMPT] {user_id}: build prompt")
    prompt = build_prompt(user_id, profile, timeline)

    print(f"[API] {user_id}: generating dialogues")
    dialogue_data = call_openai(prompt)

    print(f"[VALIDATE] {user_id}")
    validate_dialogue_json(user_id, timeline, dialogue_data)

    print(f"[SAVE] {user_id}: {output_path}")
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(dialogue_data, f, ensure_ascii=False, indent=2)

    return output_path


# =========================
# 7. CLI 入口
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", type=str, help="只生成一个用户，例如 S04")
    parser.add_argument("--all", action="store_true", help="循环生成 S01-S10, P01-P10, L01-L10")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 dialogue 文件")
    parser.add_argument("--sleep", type=float, default=1.0, help="批量生成时每个用户之间暂停秒数")
    args = parser.parse_args()

    if not args.user_id and not args.all:
        raise ValueError("请指定 --user_id S04 或 --all")

    if args.user_id:
        generate_one_user(args.user_id, overwrite=args.overwrite)
        return

    if args.all:
        for user_id in USER_IDS:
            try:
                generate_one_user(user_id, overwrite=args.overwrite)
                time.sleep(args.sleep)
            except Exception as e:
                print(f"[ERROR] {user_id}: {e}")
                # 不中断全部任务，继续下一个
                continue


if __name__ == "__main__":
    main()
