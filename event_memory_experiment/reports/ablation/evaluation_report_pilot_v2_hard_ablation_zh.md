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
| full_qca | 0.639 | 0.643 | 0.617 | 0.561 | 0.629 | 0.000 | 86.456 |
| wo_tmt | 0.652 | 0.649 | 0.718 | 0.629 | 0.591 | 0.014 | 86.496 |
| wo_decay | 0.640 | 0.633 | 0.581 | 0.518 | 0.635 | 0.000 | 84.399 |
| wo_compatibility | 0.492 | 0.469 | 0.411 | 0.359 | 0.541 | 0.024 | 82.593 |
| wo_domain | 0.549 | 0.541 | 0.565 | 0.327 | 0.595 | 0.000 | 85.306 |
| wo_penalty | 0.641 | 0.644 | 0.617 | 0.561 | 0.631 | 0.041 | 86.274 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.832 | 0.713 | 0.617 | 0.913 | 0.704 | 0.052 | 170.141 |
| wo_tmt | 0.826 | 0.720 | 0.718 | 0.907 | 0.689 | 0.114 | 170.044 |
| wo_decay | 0.862 | 0.710 | 0.581 | 0.898 | 0.764 | 0.031 | 167.359 |
| wo_compatibility | 0.700 | 0.548 | 0.411 | 0.584 | 0.756 | 0.117 | 165.863 |
| wo_domain | 0.753 | 0.621 | 0.565 | 0.661 | 0.713 | 0.062 | 169.714 |
| wo_penalty | 0.843 | 0.715 | 0.617 | 0.913 | 0.714 | 0.062 | 169.282 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate |
| --- | --- | --- | --- | --- | --- | --- |
| wo_tmt | +0.012 | +0.005 | +0.101 | +0.068 | -0.038 | +0.014 |
| wo_decay | +0.001 | -0.010 | -0.036 | -0.042 | +0.006 | +0.000 |
| wo_compatibility | -0.147 | -0.174 | -0.206 | -0.201 | -0.088 | +0.024 |
| wo_domain | -0.090 | -0.102 | -0.052 | -0.234 | -0.034 | +0.000 |
| wo_penalty | +0.001 | +0.000 | +0.000 | +0.000 | +0.002 | +0.041 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_qca | 0.704 | 0.764 | 0.784 | 0.000 |
| chat | wo_tmt | 0.726 | 0.774 | 0.784 | 0.014 |
| chat | wo_decay | 0.751 | 0.777 | 0.750 | 0.000 |
| chat | wo_compatibility | 0.613 | 0.641 | 0.602 | 0.024 |
| chat | wo_domain | 0.663 | 0.677 | 0.568 | 0.000 |
| chat | wo_penalty | 0.707 | 0.765 | 0.784 | 0.041 |
| task | full_qca | 0.604 | 0.577 | 0.525 | - |
| task | wo_tmt | 0.610 | 0.580 | 0.681 | - |
| task | wo_decay | 0.579 | 0.554 | 0.487 | - |
| task | wo_compatibility | 0.426 | 0.375 | 0.306 | - |
| task | wo_domain | 0.486 | 0.467 | 0.562 | - |
| task | wo_penalty | 0.604 | 0.577 | 0.525 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_history | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_history | wo_decay | +0.000 | -0.013 | +0.000 |
| chat_history | wo_compatibility | +0.000 | +0.000 | +0.000 |
| chat_history | wo_domain | +0.000 | -0.298 | -0.900 |
| chat_history | wo_penalty | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_decay | +0.000 | -0.014 | -0.079 |
| chat_preference | wo_compatibility | -0.088 | -0.125 | -0.184 |
| chat_preference | wo_domain | +0.000 | -0.010 | -0.053 |
| chat_preference | wo_penalty | +0.009 | +0.003 | +0.000 |
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
| task_context | wo_decay | +0.128 | -0.014 | -0.231 |
| task_context | wo_compatibility | -0.103 | +0.008 | +0.231 |
| task_context | wo_domain | +0.000 | +0.090 | +0.346 |
| task_context | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt | +0.033 | +0.022 | +0.000 |
| task_dependency | wo_decay | -0.067 | -0.034 | +0.000 |
| task_dependency | wo_compatibility | +0.117 | +0.043 | +0.000 |
| task_dependency | wo_domain | -0.100 | -0.104 | -0.050 |
| task_dependency | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_due | wo_tmt | +0.008 | -0.084 | +0.341 |
| task_due | wo_decay | -0.136 | -0.059 | +0.000 |
| task_due | wo_compatibility | -0.227 | -0.266 | -0.250 |
| task_due | wo_domain | -0.136 | -0.111 | +0.205 |
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

## 8. Hard Case Results: top_k=5

| hard_case_tag | ablation | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | completed_error | todo_intrusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compatibility_chat_intrusion | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_decay | 1.000 | 0.920 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_compatibility | 1.000 | 0.877 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_plan | full_qca | 1.000 | 0.906 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_tmt | 1.000 | 0.906 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_decay | 1.000 | 0.646 | 0.000 | - | 1.000 | - | - |
| decay_current_plan | wo_compatibility | 0.500 | 0.704 | 1.000 | - | 0.500 | - | - |
| decay_current_plan | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_penalty | 1.000 | 0.906 | 1.000 | - | 1.000 | - | - |
| decay_current_preference | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_decay | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_compatibility | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 |
| domain_wrong_urgent | full_qca | 0.500 | 0.521 | 0.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_tmt | 0.500 | 0.275 | 1.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_decay | 0.500 | 0.521 | 0.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_compatibility | 0.500 | 0.413 | 0.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_domain | 0.000 | 0.000 | 0.000 | 0.000 | - | 0.000 | - |
| domain_wrong_urgent | wo_penalty | 0.500 | 0.521 | 0.000 | 0.500 | - | 0.000 | - |
| penalty_completed_task | full_qca | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_tmt | 0.500 | 0.235 | 0.000 | 0.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_decay | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_compatibility | 1.000 | 0.648 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_domain | 1.000 | 0.742 | 1.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_penalty | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_old_preference | full_qca | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_tmt | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_decay | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_compatibility | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_domain | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_penalty | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 |
| tmt_deadline_order | full_qca | 1.000 | 0.626 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| tmt_deadline_order | wo_tmt | 0.500 | 0.272 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_decay | 0.500 | 0.444 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_compatibility | 1.000 | 0.534 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| tmt_deadline_order | wo_domain | 0.500 | 0.272 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_penalty | 1.000 | 0.626 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| tmt_far_distractor | full_qca | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_tmt | 1.000 | 0.821 | 1.000 | 1.000 | - | 0.250 | - |
| tmt_far_distractor | wo_decay | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_compatibility | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_domain | 0.500 | 0.352 | 0.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_penalty | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - |

## 9. Component Contribution Analysis

- `wo_tmt`: top_k=5 下 todo_recall 变化为 +0.068；task_due recall 变化为 +0.008，task_priority recall 变化为 +0.000。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 +0.006；chat_history recall 变化为 +0.000，chat_preference recall 变化为 +0.000。
- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 -0.174，todo_intrusion_rate 变化为 +0.024。
- `wo_domain`: top_k=5 下 task_context recall 变化为 +0.000，task_dependency recall 变化为 -0.100，mixed recall 变化为 -0.179。
- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 +0.000，todo_intrusion_rate 变化为 +0.041。

## 10. 结论

本轮消融最清楚的结论是：`compatibility` 和 `domain match` 是当前 QCA 在 Pilot v2 上最关键的两个约束。移除 compatibility 后，top_k=5 的 memory_recall、memory_NDCG、top1 accuracy 和 todo_recall 都明显下降；移除 domain 后，todo_recall 与部分 task/mixed subtype 也显著受损。

TMT 和 decay 的结果更复杂。`wo_tmt` 在当前数据上没有导致预期下降，反而提升了若干总体指标，并带来少量 todo_intrusion；`wo_decay` 也没有整体下降。这不应解释为 TMT/decay 无效，而应作为后续诊断信号：当前 synthetic Pilot v2 可能让 accessible_score 与 TMT/decay 功能重叠，或 TMT/decay 的权重与函数形状还没有充分校准。`wo_penalty` 几乎没有影响，说明当前数据中的 completed/old-preference 错误样本覆盖不足，或 penalty 触发条件过少。

如果本报告使用 hard ablation 扩展数据集，请优先查看 hard_case_tag 分组结果。它比 overall 更适合判断 TMT、decay 和 penalty 是否在对应困难场景中产生独立贡献。