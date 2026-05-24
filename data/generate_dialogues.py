import argparse
import subprocess
from pathlib import Path


# =========================
# 路径配置
# =========================

CODEX_CMD = Path(r"C:\nvm4w\nodejs\codex.cmd")

BASE_DIR = Path(r"E:\MyDatum\小论文\Codex\data")

# 你的 prompt txt，改成你实际放置的位置
PROMPT_TXT = Path(r"E:\MyDatum\小论文\Codex\data\prompts\dialogue_realization_prompt.txt")

PROFILES_FILE = Path(
    r"E:\MyDatum\小论文\Codex\data\outputs\profiles\long_memory_benchmark_user_profiles_enriched.json"
)

TIMELINES_DIR = Path(
    r"E:\MyDatum\小论文\Codex\data\outputs\timelines"
)

DIALOGUES_DIR = Path(
    r"E:\MyDatum\小论文\Codex\data\outputs\dialogues"
)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到 prompt 文件：{path}")
    return path.read_text(encoding="utf-8-sig")


def find_timeline_file(user_id: str) -> Path:
    candidates = [
        TIMELINES_DIR / f"{user_id}_timeline.json",
        TIMELINES_DIR / f"{user_id}_latent_world_timeline.json",
        TIMELINES_DIR / f"{user_id}.json",
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(f"找不到 {user_id} 的 timeline 文件，目录：{TIMELINES_DIR}")


def build_prompt(user_id: str) -> str:
    base_prompt = read_text(PROMPT_TXT)
    base_prompt = base_prompt.replace("{{USER_ID}}", user_id)

    timeline_file = find_timeline_file(user_id)
    output_file = DIALOGUES_DIR / f"{user_id}_dialogues.json"

    # 这里追加绝对路径，覆盖你 prompt 末尾原来的相对路径说明
    path_override = f"""

====================

请读取用户画像总文件：
{PROFILES_FILE}

请读取当前用户 timeline 文件：
{timeline_file}

只处理 user_id = {user_id}。

请将结果写入：
{output_file}

如果输出目录不存在，请创建：
{DIALOGUES_DIR}

要求：
1. 只生成 {user_id} 的 dialogue JSON。
2. 不要修改 profile 文件。
3. 不要修改 timeline 文件。
4. 输出文件必须是合法 JSON。
5. 完成后只回复：DONE {user_id}
"""

    return base_prompt + path_override


def run_codex_for_user(user_id: str, overwrite: bool = False):
    DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DIALOGUES_DIR / f"{user_id}_dialogues.json"

    if output_file.exists() and not overwrite:
        print(f"[SKIP] {user_id}: 已存在 {output_file}")
        return

    prompt = build_prompt(user_id)

    code_cmd = Path(r"C:\nvm4w\nodejs\codex.cmd")

    if code_cmd.exists():
        cmd = [
            str(code_cmd),
            "exec",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "-"
        ]
    else:
        # fallback：如果系统 PATH 能找到 codex，就走这个
        cmd = [
            "codex",
            "exec",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
            "-"
        ]

    print(f"[CODEX] 开始生成 {user_id} dialogue...")

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        cwd=str(BASE_DIR),
        capture_output=True,
        shell=False
    )

    print("STDOUT:")
    print(result.stdout)

    if result.stderr.strip():
        print("STDERR:")
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"Codex 运行失败：{user_id}")

    if not output_file.exists():
        raise FileNotFoundError(f"Codex 运行结束，但没有生成输出文件：{output_file}")

    print(f"[OK] 已生成：{output_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_id", required=True, help="例如 S04 / P01 / L03")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    run_codex_for_user(args.user_id, overwrite=args.overwrite)


if __name__ == "__main__":
    main()