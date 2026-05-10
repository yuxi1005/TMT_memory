import argparse
import csv
from collections import defaultdict
from pathlib import Path


METRICS = [
    "memory_recall",
    "memory_NDCG",
    "memory_top1_accuracy",
    "todo_recall",
    "non_todo_recall",
    "completed_task_error_rate",
    "todo_intrusion_rate",
    "wrong_domain_intrusion_rate",
    "stale_memory_intrusion_rate",
    "completed_task_intrusion_rate",
    "far_deadline_before_near_rate",
    "deadline_ranking_accuracy",
    "memory_token_cost",
]

CORE_METRICS = [
    "memory_recall",
    "memory_NDCG",
    "memory_top1_accuracy",
    "todo_recall",
    "non_todo_recall",
    "todo_intrusion_rate",
    "wrong_domain_intrusion_rate",
    "stale_memory_intrusion_rate",
    "memory_token_cost",
]

ABLATION_ORDER = [
    "full_qca",
    "wo_tmt",
    "wo_decay",
    "wo_compatibility",
    "wo_domain",
    "wo_penalty",
]


def load_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def mean_metric(rows, metric):
    values = []
    for row in rows:
        value = row.get(metric)
        if value in ("", "None", None):
            continue
        values.append(float(value))
    if not values:
        return None
    return sum(values) / len(values)


def aggregate(rows, keys, metrics):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(key, "") for key in keys)].append(row)

    result = {}
    for key, group_rows in groups.items():
        result[key] = {metric: mean_metric(group_rows, metric) for metric in metrics}
        result[key]["n"] = len(group_rows)
    return result


def fmt(value):
    if value is None:
        return "-"
    return f"{value:.3f}"


def signed(value):
    if value is None:
        return "-"
    return f"{value:+.3f}"


def markdown_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def ordered_ablations(available):
    known = [item for item in ABLATION_ORDER if item in available]
    extra = sorted(set(available) - set(known))
    return known + extra


def table_by_ablation(overall, top_k, metrics):
    available = {key[1] for key in overall if key[0] == str(top_k)}
    rows = []
    for ablation in ordered_ablations(available):
        item = overall.get((str(top_k), ablation), {})
        rows.append([ablation] + [fmt(item.get(metric)) for metric in metrics])
    return markdown_table(["ablation"] + metrics, rows)


def delta_table(overall, top_k, metrics):
    full = overall[(str(top_k), "full_qca")]
    available = {key[1] for key in overall if key[0] == str(top_k) and key[1] != "full_qca"}
    rows = []
    for ablation in ordered_ablations(available):
        item = overall[(str(top_k), ablation)]
        rows.append(
            [ablation]
            + [
                signed(None if item.get(metric) is None or full.get(metric) is None else item[metric] - full[metric])
                for metric in metrics
            ]
        )
    return markdown_table(["ablation"] + [f"delta_{metric}" for metric in metrics], rows)


def mode_table(mode_agg, top_k):
    rows = []
    for mode in sorted({key[1] for key in mode_agg if key[0] == str(top_k)}):
        for ablation in ordered_ablations({key[2] for key in mode_agg if key[0] == str(top_k) and key[1] == mode}):
            item = mode_agg[(str(top_k), mode, ablation)]
            rows.append(
                [
                    mode,
                    ablation,
                    fmt(item.get("memory_recall")),
                    fmt(item.get("memory_NDCG")),
                    fmt(item.get("memory_top1_accuracy")),
                    fmt(item.get("todo_intrusion_rate")),
                ]
            )
    return markdown_table(
        ["query_mode", "ablation", "memory_recall", "memory_NDCG", "top1_acc", "todo_intrusion"],
        rows,
    )


def subtype_delta_table(subtype_agg, top_k):
    rows = []
    metrics = ["memory_recall", "memory_NDCG", "memory_top1_accuracy"]
    subtypes = sorted({key[1] for key in subtype_agg if key[0] == str(top_k)})
    for subtype in subtypes:
        full = subtype_agg.get((str(top_k), subtype, "full_qca"))
        if not full:
            continue
        for ablation in ordered_ablations(
            {key[2] for key in subtype_agg if key[0] == str(top_k) and key[1] == subtype and key[2] != "full_qca"}
        ):
            item = subtype_agg[(str(top_k), subtype, ablation)]
            rows.append(
                [subtype, ablation]
                + [
                    signed(None if item.get(metric) is None or full.get(metric) is None else item[metric] - full[metric])
                    for metric in metrics
                ]
            )
    return markdown_table(["query_subtype", "ablation"] + [f"delta_{metric}" for metric in metrics], rows)


def hard_case_table(hard_agg, top_k):
    rows = []
    tags = sorted({key[1] for key in hard_agg if key[0] == str(top_k) and key[1]})
    for tag in tags:
        for ablation in ordered_ablations({key[2] for key in hard_agg if key[0] == str(top_k) and key[1] == tag}):
            item = hard_agg[(str(top_k), tag, ablation)]
            rows.append(
                [
                    tag,
                    ablation,
                    fmt(item.get("memory_recall")),
                    fmt(item.get("memory_NDCG")),
                    fmt(item.get("memory_top1_accuracy")),
                    fmt(item.get("todo_recall")),
                    fmt(item.get("non_todo_recall")),
                    fmt(item.get("completed_task_error_rate")),
                    fmt(item.get("todo_intrusion_rate")),
                    fmt(item.get("wrong_domain_intrusion_rate")),
                    fmt(item.get("stale_memory_intrusion_rate")),
                    fmt(item.get("far_deadline_before_near_rate")),
                ]
            )
    if not rows:
        return "No hard_case_tag rows found."
    return markdown_table(
        [
            "hard_case_tag",
            "ablation",
            "memory_recall",
            "memory_NDCG",
            "top1_acc",
            "todo_recall",
            "non_todo_recall",
            "completed_error",
            "todo_intrusion",
            "wrong_domain_intrusion",
            "stale_intrusion",
            "far_before_near",
        ],
        rows,
    )


def component_notes(overall, subtype_agg):
    full = overall[("5", "full_qca")]

    def delta(ablation, metric):
        item = overall[("5", ablation)]
        if item.get(metric) is None or full.get(metric) is None:
            return None
        return item[metric] - full[metric]

    def subtype_delta(subtype, ablation, metric):
        base = subtype_agg.get(("5", subtype, "full_qca"))
        item = subtype_agg.get(("5", subtype, ablation))
        if not base or not item or base.get(metric) is None or item.get(metric) is None:
            return None
        return item[metric] - base[metric]

    lines = [
        "- `wo_tmt`: top_k=5 下 todo_recall 变化为 "
        f"{signed(delta('wo_tmt', 'todo_recall'))}；task_due recall 变化为 "
        f"{signed(subtype_delta('task_due', 'wo_tmt', 'memory_recall'))}，task_priority recall 变化为 "
        f"{signed(subtype_delta('task_priority', 'wo_tmt', 'memory_recall'))}。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。",
        "- `wo_decay`: top_k=5 下 non_todo_recall 变化为 "
        f"{signed(delta('wo_decay', 'non_todo_recall'))}；chat_history recall 变化为 "
        f"{signed(subtype_delta('chat_history', 'wo_decay', 'memory_recall'))}，chat_preference recall 变化为 "
        f"{signed(subtype_delta('chat_preference', 'wo_decay', 'memory_recall'))}。",
        "- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 "
        f"{signed(delta('wo_compatibility', 'memory_NDCG'))}，todo_intrusion_rate 变化为 "
        f"{signed(delta('wo_compatibility', 'todo_intrusion_rate'))}。",
        "- `wo_domain`: top_k=5 下 task_context recall 变化为 "
        f"{signed(subtype_delta('task_context', 'wo_domain', 'memory_recall'))}，task_dependency recall 变化为 "
        f"{signed(subtype_delta('task_dependency', 'wo_domain', 'memory_recall'))}，mixed recall 变化为 "
        f"{signed(subtype_delta('mixed', 'wo_domain', 'memory_recall'))}。",
        "- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 "
        f"{signed(delta('wo_penalty', 'completed_task_error_rate'))}，todo_intrusion_rate 变化为 "
        f"{signed(delta('wo_penalty', 'todo_intrusion_rate'))}。",
    ]
    return "\n".join(lines)


def build_report(rows):
    overall = aggregate(rows, ["top_k", "ablation"], METRICS)
    mode_agg = aggregate(rows, ["top_k", "query_mode", "ablation"], METRICS)
    subtype_agg = aggregate(rows, ["top_k", "query_subtype", "ablation"], METRICS)
    hard_agg = aggregate(rows, ["top_k", "hard_case_tag", "ablation"], METRICS)

    return "\n\n".join(
        [
            "# Pilot v2 MU-Level Ablation 实验报告",
            "## 1. 实验目标\n\n本实验在 Pilot v2 的 MU-level retrieval 上验证 QCA 公式内部组件的贡献。消融对象包括 TMT、forgetting decay、intent-memory type compatibility、domain match 和 penalty。主表使用 top_k=5，top_k=10 作为补充。",
            "## 2. Ablation Variants\n\n"
            + markdown_table(
                ["ablation", "含义"],
                [
                    ["full_qca", "完整 QCA 公式"],
                    ["wo_tmt", "todo 的 accessibility 不使用 TMT，改用 accessible_score"],
                    ["wo_decay", "non-todo 的 accessibility 不使用 forgetting decay，改用 accessible_score"],
                    ["wo_compatibility", "移除 intent-memory type compatibility"],
                    ["wo_domain", "移除 query 与任务域/实体的 domain match"],
                    ["wo_penalty", "移除 completed task、domain mismatch、old preference 等惩罚项"],
                ],
            ),
            "## 3. Overall Results: top_k=5\n\n" + table_by_ablation(overall, 5, CORE_METRICS),
            "## 4. Overall Results: top_k=10\n\n" + table_by_ablation(overall, 10, CORE_METRICS),
            "## 5. Component Delta: top_k=5\n\n下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。\n\n"
            + delta_table(overall, 5, ["memory_recall", "memory_NDCG", "memory_top1_accuracy", "todo_recall", "non_todo_recall", "todo_intrusion_rate"]),
            "## 6. By Query Mode: top_k=5\n\n" + mode_table(mode_agg, 5),
            "## 7. By Query Subtype Delta: top_k=5\n\n" + subtype_delta_table(subtype_agg, 5),
            "## 8. Hard Case Results: top_k=5\n\n" + hard_case_table(hard_agg, 5),
            "## 9. Component Contribution Analysis\n\n" + component_notes(overall, subtype_agg),
            "## 10. 结论\n\n本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 TMT、decay、compatibility、domain 和 penalty 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。\n\n修复后的消融已经阻断 `wo_tmt` 中的隐式 TMT penalty 调用，并将 `access` 与 `base` 解耦：`base` 只表示静态 importance/accessibility，non-todo `access` 只表示时间衰减系数。因此，`wo_tmt` 和 `wo_decay` 的结果比旧报告更接近纯粹消融。\n\n如果 hard_case_tag 表中某个组件对应的困难样本显著下降，即使 overall 变化不大，也可以解释为该组件在目标场景中有效；如果 hard case 仍不下降，再考虑继续调权重、改函数形状或补更强的诊断样本。"
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = load_rows(args.input)
    report = build_report(rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"wrote report to {output}")


if __name__ == "__main__":
    main()
