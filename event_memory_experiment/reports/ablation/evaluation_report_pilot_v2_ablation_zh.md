# Pilot v2 MU-Level Ablation 实验报告

## 1. 实验目标

本实验在 Pilot v2 的 MU-level retrieval 上验证 QCA 公式内部组件的贡献。消融对象包括 TMT、forgetting decay、intent-memory type compatibility、domain match 和 penalty。主表使用 top_k=5，top_k=10 作为补充。

## 2. Ablation Variants

| ablation | 含义 |
| --- | --- |
| full_qca | 完整 QCA 公式 |
| wo_tmt | todo 的 accessibility 不使用 TMT，改用 accessible_score |
| wo_decay | non-todo 的 accessibility 不使用 forgetting decay，改用 accessible_score |
| wo_compatibility | 移除 intent-memory type compatibility |
| wo_domain | 移除 query 与任务域/实体的 domain match |
| wo_penalty | 移除 completed task、domain mismatch、old preference 等惩罚项 |

## 3. Overall Results: top_k=5

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.598 | 0.610 | 0.615 | 0.526 | 0.565 | 0.000 | 79.845 |
| wo_tmt | 0.628 | 0.644 | 0.710 | 0.629 | 0.555 | 0.020 | 79.875 |
| wo_decay | 0.614 | 0.622 | 0.630 | 0.476 | 0.609 | 0.000 | 77.705 |
| wo_compatibility | 0.430 | 0.420 | 0.390 | 0.287 | 0.475 | 0.035 | 75.345 |
| wo_domain | 0.516 | 0.515 | 0.550 | 0.272 | 0.560 | 0.000 | 78.455 |
| wo_penalty | 0.600 | 0.610 | 0.615 | 0.526 | 0.567 | 0.000 | 79.780 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.807 | 0.689 | 0.615 | 0.897 | 0.656 | 0.000 | 157.675 |
| wo_tmt | 0.799 | 0.713 | 0.710 | 0.890 | 0.637 | 0.075 | 157.400 |
| wo_decay | 0.828 | 0.704 | 0.630 | 0.879 | 0.710 | 0.000 | 154.925 |
| wo_compatibility | 0.643 | 0.506 | 0.390 | 0.508 | 0.720 | 0.080 | 152.350 |
| wo_domain | 0.709 | 0.593 | 0.550 | 0.599 | 0.667 | 0.000 | 156.995 |
| wo_penalty | 0.820 | 0.691 | 0.615 | 0.897 | 0.669 | 0.000 | 156.515 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate |
| --- | --- | --- | --- | --- | --- | --- |
| wo_tmt | +0.030 | +0.034 | +0.095 | +0.104 | -0.009 | +0.020 |
| wo_decay | +0.016 | +0.012 | +0.015 | -0.050 | +0.045 | +0.000 |
| wo_compatibility | -0.167 | -0.190 | -0.225 | -0.238 | -0.090 | +0.035 |
| wo_domain | -0.082 | -0.094 | -0.065 | -0.254 | -0.004 | +0.000 |
| wo_penalty | +0.002 | +0.001 | +0.000 | +0.000 | +0.002 | +0.000 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_qca | 0.670 | 0.718 | 0.729 | 0.000 |
| chat | wo_tmt | 0.699 | 0.730 | 0.729 | 0.020 |
| chat | wo_decay | 0.730 | 0.768 | 0.771 | 0.000 |
| chat | wo_compatibility | 0.556 | 0.601 | 0.586 | 0.035 |
| chat | wo_domain | 0.619 | 0.609 | 0.457 | 0.000 |
| chat | wo_penalty | 0.675 | 0.720 | 0.729 | 0.000 |
| task | full_qca | 0.559 | 0.551 | 0.554 | - |
| task | wo_tmt | 0.590 | 0.598 | 0.700 | - |
| task | wo_decay | 0.551 | 0.544 | 0.554 | - |
| task | wo_compatibility | 0.363 | 0.323 | 0.285 | - |
| task | wo_domain | 0.460 | 0.465 | 0.600 | - |
| task | wo_penalty | 0.559 | 0.551 | 0.554 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_history | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_history | wo_decay | +0.000 | -0.013 | +0.000 |
| chat_history | wo_compatibility | +0.000 | +0.000 | +0.000 |
| chat_history | wo_domain | +0.000 | -0.298 | -0.900 |
| chat_history | wo_penalty | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_decay | +0.000 | +0.090 | +0.150 |
| chat_preference | wo_compatibility | -0.167 | -0.109 | -0.050 |
| chat_preference | wo_domain | +0.000 | -0.019 | -0.100 |
| chat_preference | wo_penalty | +0.017 | +0.006 | +0.000 |
| chat_profile | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_decay | +0.400 | +0.145 | +0.000 |
| chat_profile | wo_compatibility | -0.400 | -0.598 | -0.900 |
| chat_profile | wo_domain | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_penalty | +0.000 | +0.000 | +0.000 |
| mixed | wo_tmt | +0.100 | +0.044 | +0.000 |
| mixed | wo_decay | +0.008 | +0.018 | +0.000 |
| mixed | wo_compatibility | -0.033 | -0.002 | +0.000 |
| mixed | wo_domain | -0.179 | -0.215 | -0.400 |
| mixed | wo_penalty | +0.000 | +0.000 | +0.000 |
| negative | wo_tmt | +0.000 | +0.000 | +0.000 |
| negative | wo_decay | +0.000 | +0.000 | +0.000 |
| negative | wo_compatibility | +0.000 | +0.000 | +0.000 |
| negative | wo_domain | +0.000 | +0.000 | +0.000 |
| negative | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_context | wo_tmt | +0.000 | +0.000 | +0.000 |
| task_context | wo_decay | +0.167 | +0.060 | +0.000 |
| task_context | wo_compatibility | +0.017 | +0.072 | +0.300 |
| task_context | wo_domain | +0.000 | +0.089 | +0.450 |
| task_context | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt | +0.033 | +0.022 | +0.000 |
| task_dependency | wo_decay | -0.067 | -0.034 | +0.000 |
| task_dependency | wo_compatibility | +0.117 | +0.043 | +0.000 |
| task_dependency | wo_domain | -0.100 | -0.104 | -0.050 |
| task_dependency | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_due | wo_tmt | +0.167 | +0.093 | +0.450 |
| task_due | wo_decay | -0.150 | -0.076 | +0.000 |
| task_due | wo_compatibility | -0.500 | -0.515 | -0.550 |
| task_due | wo_domain | +0.000 | +0.106 | +0.450 |
| task_due | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_priority | wo_tmt | +0.000 | +0.146 | +0.333 |
| task_priority | wo_decay | +0.000 | +0.000 | +0.000 |
| task_priority | wo_compatibility | -0.422 | -0.420 | -0.333 |
| task_priority | wo_domain | -0.311 | -0.365 | -0.333 |
| task_priority | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_status | wo_tmt | +0.000 | -0.017 | +0.000 |
| task_status | wo_decay | +0.000 | +0.000 | +0.000 |
| task_status | wo_compatibility | -0.138 | -0.229 | -0.500 |
| task_status | wo_domain | -0.038 | -0.052 | -0.025 |
| task_status | wo_penalty | +0.000 | +0.000 | +0.000 |

## 8. Component Contribution Analysis

- `wo_tmt`: top_k=5 下 todo_recall 变化为 +0.104；task_due recall 变化为 +0.167，task_priority recall 变化为 +0.000。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 +0.045；chat_history recall 变化为 +0.000，chat_preference recall 变化为 +0.000。
- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 -0.190，todo_intrusion_rate 变化为 +0.035。
- `wo_domain`: top_k=5 下 task_context recall 变化为 +0.000，task_dependency recall 变化为 -0.100，mixed recall 变化为 -0.179。
- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 +0.000，todo_intrusion_rate 变化为 +0.000。

## 9. 结论

本轮消融最清楚的结论是：`compatibility` 和 `domain match` 是当前 QCA 在 Pilot v2 上最关键的两个约束。移除 compatibility 后，top_k=5 的 memory_recall、memory_NDCG、top1 accuracy 和 todo_recall 都明显下降；移除 domain 后，todo_recall 与部分 task/mixed subtype 也显著受损。

TMT 和 decay 的结果更复杂。`wo_tmt` 在当前数据上没有导致预期下降，反而提升了若干总体指标，并带来少量 todo_intrusion；`wo_decay` 也没有整体下降。这不应解释为 TMT/decay 无效，而应作为后续诊断信号：当前 synthetic Pilot v2 可能让 accessible_score 与 TMT/decay 功能重叠，或 TMT/decay 的权重与函数形状还没有充分校准。`wo_penalty` 几乎没有影响，说明当前数据中的 completed/old-preference 错误样本覆盖不足，或 penalty 触发条件过少。

下一步建议：补充更强的 deadline-ordering、completed-task 和 old-preference hard cases；单独校准 TMT/decay；然后将 lexical overlap similarity 替换为 embedding similarity 后复跑同一套 ablation。