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
    "completed_todo_retro_recall",
    "active_todo_precision",
    "wrong_domain_urgent_intrusion_rate",
    "stale_preference_intrusion_rate",
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
    "active_todo_precision",
    "wrong_domain_urgent_intrusion_rate",
    "stale_preference_intrusion_rate",
    "memory_token_cost",
]

ABLATION_ORDER = [
    "full_core_v2",
    "wo_embedding",
    "wo_decay",
    "wo_role_matrix",
    "wo_domain_gate",
    "wo_tmt_condition",
    "wo_eisenhower",
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
    full = overall[(str(top_k), "full_core_v2")]
    available = {key[1] for key in overall if key[0] == str(top_k) and key[1] != "full_core_v2"}
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
        full = subtype_agg.get((str(top_k), subtype, "full_core_v2"))
        if not full:
            continue
        for ablation in ordered_ablations(
            {key[2] for key in subtype_agg if key[0] == str(top_k) and key[1] == subtype and key[2] != "full_core_v2"}
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
    full = overall[("5", "full_core_v2")]

    def delta(ablation, metric):
        item = overall.get(("5", ablation))
        if not item:
            return None
        if item.get(metric) is None or full.get(metric) is None:
            return None
        return item[metric] - full[metric]

    def subtype_delta(subtype, ablation, metric):
        base = subtype_agg.get(("5", subtype, "full_core_v2"))
        item = subtype_agg.get(("5", subtype, ablation))
        if not base or not item or base.get(metric) is None or item.get(metric) is None:
            return None
        return item[metric] - base[metric]

    lines = [
        "- `wo_embedding`: top_k=5 下 memory_recall 变化为 "
        f"{signed(delta('wo_embedding', 'memory_recall'))}，memory_NDCG 变化为 "
        f"{signed(delta('wo_embedding', 'memory_NDCG'))}。",
        "- `wo_decay`: top_k=5 下 non_todo_recall 变化为 "
        f"{signed(delta('wo_decay', 'non_todo_recall'))}；chat_history recall 变化为 "
        f"{signed(subtype_delta('chat_history', 'wo_decay', 'memory_recall'))}，chat_preference recall 变化为 "
        f"{signed(subtype_delta('chat_preference', 'wo_decay', 'memory_recall'))}。",
        "- `wo_role_matrix`: top_k=5 下 todo_intrusion_rate 变化为 "
        f"{signed(delta('wo_role_matrix', 'todo_intrusion_rate'))}，active_todo_precision 变化为 "
        f"{signed(delta('wo_role_matrix', 'active_todo_precision'))}。",
        "- `wo_domain_gate`: top_k=5 下 wrong_domain_urgent_intrusion_rate 变化为 "
        f"{signed(delta('wo_domain_gate', 'wrong_domain_urgent_intrusion_rate'))}。",
        "- `wo_tmt_condition`: top_k=5 下 task_context recall 变化为 "
        f"{signed(subtype_delta('task_context', 'wo_tmt_condition', 'memory_recall'))}。",
        "- `wo_eisenhower`: top_k=5 下 deadline_ranking_accuracy 变化为 "
        f"{signed(delta('wo_eisenhower', 'deadline_ranking_accuracy'))}，far_deadline_before_near_rate 变化为 "
        f"{signed(delta('wo_eisenhower', 'far_deadline_before_near_rate'))}。",
    ]
    return "\n".join(lines)


def build_report(rows):
    overall = aggregate(rows, ["top_k", "ablation"], METRICS)
    mode_agg = aggregate(rows, ["top_k", "query_mode", "ablation"], METRICS)
    subtype_agg = aggregate(rows, ["top_k", "query_subtype", "ablation"], METRICS)
    hard_agg = aggregate(rows, ["top_k", "hard_case_tag", "ablation"], METRICS)

    return "\n\n".join(
        [
            "# MU-Level Theory-Core v2 Ablation 实验报告",
            "## 1. 实验目标\n\n本实验在 MU-level retrieval 上验证 Theory-Core v2 连乘公式的组件贡献：bounded similarity、role-level intent matrix、soft-hard domain gate、conditional TMT/Eisenhower accessibility 与 retrospective decay。主表使用 top_k=5，top_k=10 作为补充。",
            "## 2. Ablation Variants\n\n"
            + markdown_table(
                ["ablation", "含义"],
                [
                    ["full_core_v2", "完整 v2 连乘公式：Sim × IntentGate × DomainGate × Accessibility"],
                    ["wo_embedding", "Sim 强制回退为纯 Token 匹配"],
                    ["wo_decay", "non-todo 的 accessibility 不使用 forgetting decay，改用 accessible_score"],
                    ["wo_role_matrix", "IntentGate 强制设为 1"],
                    ["wo_domain_gate", "DomainGate 强制设为 1"],
                    ["wo_tmt_condition", "TMT 在所有 query_subtype 下均生效"],
                    ["wo_eisenhower", "移除四象限调制，退化为纯 Deadline TMT"],
                ],
            ),
            "## 3. Overall Results: top_k=5\n\n" + table_by_ablation(overall, 5, CORE_METRICS),
            "## 4. Overall Results: top_k=10\n\n" + table_by_ablation(overall, 10, CORE_METRICS),
            "## 5. Component Delta: top_k=5\n\n下表为各消融相对 `full_core_v2` 的变化，负值表示移除该组件后指标下降。\n\n"
            + delta_table(overall, 5, ["memory_recall", "memory_NDCG", "memory_top1_accuracy", "todo_recall", "non_todo_recall", "todo_intrusion_rate", "active_todo_precision"]),
            "## 6. By Query Mode: top_k=5\n\n" + mode_table(mode_agg, 5),
            "## 7. By Query Subtype Delta: top_k=5\n\n" + subtype_delta_table(subtype_agg, 5),
            "## 8. Hard Case Results: top_k=5\n\n" + hard_case_table(hard_agg, 5),
            "## 9. Component Contribution Analysis\n\n" + component_notes(overall, subtype_agg),
            "## 10. 结论\n\n本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 bounded similarity、role matrix、domain gate、conditional TMT 和 Eisenhower 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。\n\n当前版本已将主方法改为 `Sim × IntentGate × DomainGate × Accessibility`。其中 Sim 有 embedding/floor 兜底，IntentGate 是角色级矩阵，DomainGate 负责软硬结合的跨域隔离，TMT 只在任务调度型 query 下生效。"
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
