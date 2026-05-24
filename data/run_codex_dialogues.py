import argparse
import subprocess
import time
from pathlib import Path


BASE_DIR = Path(r"E:\MyDatum\小论文\Codex")

PROMPT_TXT = BASE_DIR / "data" / "generate_dialogues.txt"

PROFILES_FILE = BASE_DIR / "data" / "outputs" / "profiles" / "long_memory_benchmark_user_profiles_enriched.json"
TIMELINES_DIR = BASE_DIR / "data" / "outputs" / "timelines"
DIALOGUES_DIR = BASE_DIR / "data" / "outputs" / "dialogues"

USER_IDS = (
    [f"S{i:02d}" for i in range(1, 11)]
    + [f"P{i:02d}" for i in range(1, 11)]
    + [f"L{i:02d}" for i in range(1, 11)]
)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")
    return path.read_text(encoding="utf-8-sig")


def find_timeline_file(user_id: str) -> Path:
    candidates = [
        TIMELINES_DIR / f"{user_id}_timeline.json",
        TIMELINES_DIR / f"{user_id}_latent_world_timeline.json",
        TIMELINES_DIR / f"{user_id}.json",
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(f"找不到 {user_id} 的 timeline 文件：{TIMELINES_DIR}")


def build_codex_prompt(user_id: str) -> str:
    base_prompt = read_text(PROMPT_TXT).replace("{{USER_ID}}", user_id)

    timeline_file = find_timeline_file(user_id)
    output_file = DIALOGUES_DIR / f"{user_id}_dialogues.json"

    return f"""{base_prompt}

====================
本次实际任务
====================

请读取下面两个文件：

1. 用户画像总文件：
{PROFILES_FILE}

2. 当前用户的 timeline 文件：
{timeline_file}

只处理 user_id = {user_id}。

请根据该用户的 profile 和 timeline 生成 dialogue interactions。

请将最终 JSON 写入：
{output_file}

要求：
1. 只生成 {user_id} 的 dialogue JSON。
2. 如果输出目录不存在，请创建：
{DIALOGUES_DIR}
3. 不要修改 profile 文件。
4. 不要修改 timeline 文件。
5. 不要生成 memory units。
6. 不要生成 query。
7. 不要生成 gold。
8. 输出文件必须是合法 JSON。
9. 完成后只回复一句：DONE {user_id}
"""


def run_codex_for_user(user_id: str, overwrite: bool = False) -> None:
    DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)

    output_file = DIALOGUES_DIR / f"{user_id}_dialogues.json"

    if output_file.exists() and not overwrite:
        print(f"[SKIP] {user_id}: 已存在 {output_file}")
        return

    prompt = build_codex_prompt(user_id)

    print(f"[CODEX] Generating dialogues for {user_id}...")

    cmd = [
        "codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "-",
    ]

    result = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        cwd=str(BASE_DIR),
        capture_output=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] {user_id}: Codex failed.")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        raise RuntimeError(f"Codex failed for {user_id}")

    print(result.stdout.strip())

    if not output_file.exists():
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        raise FileNotFoundError(f"Codex 运行结束，但没有生成输出文件：{output_file}")

    print(f"[OK] {user_id}: {output_file}")


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
        run_codex_for_user(args.user_id, overwrite=args.overwrite)
        return

    for user_id in USER_IDS:
        try:
            run_codex_for_user(user_id, overwrite=args.overwrite)
            time.sleep(args.sleep)
        except Exception as e:
            print(f"[FAILED] {user_id}: {e}")
            continue


if __name__ == "__main__":
    main()