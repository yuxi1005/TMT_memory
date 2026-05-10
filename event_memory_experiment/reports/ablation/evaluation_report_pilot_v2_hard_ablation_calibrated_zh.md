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
| full_qca | 0.609 | 0.615 | 0.613 | 0.574 | 0.551 | 0.000 | 90.754 |
| wo_tmt | 0.600 | 0.577 | 0.565 | 0.519 | 0.584 | 0.000 | 89.802 |
| wo_decay | 0.681 | 0.673 | 0.681 | 0.629 | 0.630 | 0.000 | 84.798 |
| wo_compatibility | 0.441 | 0.414 | 0.391 | 0.337 | 0.395 | 0.031 | 92.790 |
| wo_domain | 0.427 | 0.437 | 0.456 | 0.173 | 0.553 | 0.000 | 87.754 |
| wo_penalty | 0.624 | 0.620 | 0.613 | 0.593 | 0.554 | 0.021 | 90.423 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.755 | 0.669 | 0.613 | 0.742 | 0.690 | 0.062 | 178.395 |
| wo_tmt | 0.820 | 0.667 | 0.565 | 0.878 | 0.690 | 0.062 | 177.194 |
| wo_decay | 0.836 | 0.731 | 0.681 | 0.842 | 0.769 | 0.055 | 167.581 |
| wo_compatibility | 0.633 | 0.490 | 0.391 | 0.541 | 0.678 | 0.110 | 183.621 |
| wo_domain | 0.587 | 0.497 | 0.456 | 0.400 | 0.645 | 0.062 | 179.226 |
| wo_penalty | 0.775 | 0.677 | 0.613 | 0.751 | 0.708 | 0.093 | 178.839 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate |
| --- | --- | --- | --- | --- | --- | --- |
| wo_tmt | -0.009 | -0.038 | -0.048 | -0.054 | +0.033 | +0.000 |
| wo_decay | +0.072 | +0.058 | +0.069 | +0.055 | +0.079 | +0.000 |
| wo_compatibility | -0.169 | -0.201 | -0.222 | -0.237 | -0.156 | +0.031 |
| wo_domain | -0.182 | -0.178 | -0.157 | -0.400 | +0.002 | +0.000 |
| wo_penalty | +0.015 | +0.005 | +0.000 | +0.019 | +0.003 | +0.021 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_qca | 0.645 | 0.670 | 0.614 | 0.000 |
| chat | wo_tmt | 0.649 | 0.673 | 0.614 | 0.000 |
| chat | wo_decay | 0.783 | 0.785 | 0.750 | 0.000 |
| chat | wo_compatibility | 0.503 | 0.542 | 0.557 | 0.031 |
| chat | wo_domain | 0.545 | 0.600 | 0.591 | 0.000 |
| chat | wo_penalty | 0.652 | 0.669 | 0.614 | 0.021 |
| task | full_qca | 0.590 | 0.585 | 0.613 | - |
| task | wo_tmt | 0.573 | 0.524 | 0.537 | - |
| task | wo_decay | 0.625 | 0.611 | 0.644 | - |
| task | wo_compatibility | 0.406 | 0.344 | 0.300 | - |
| task | wo_domain | 0.361 | 0.348 | 0.381 | - |
| task | wo_penalty | 0.608 | 0.593 | 0.613 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_history | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_history | wo_decay | +0.000 | +0.167 | +0.900 |
| chat_history | wo_compatibility | +0.000 | +0.181 | +0.900 |
| chat_history | wo_domain | -0.667 | -0.461 | +0.000 |
| chat_history | wo_penalty | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_decay | +0.088 | +0.105 | +0.079 |
| chat_preference | wo_compatibility | -0.061 | -0.069 | -0.053 |
| chat_preference | wo_domain | +0.000 | -0.020 | -0.053 |
| chat_preference | wo_penalty | +0.018 | -0.001 | +0.000 |
| chat_profile | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_decay | +0.400 | +0.145 | +0.000 |
| chat_profile | wo_compatibility | -0.450 | -0.660 | -1.000 |
| chat_profile | wo_domain | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_penalty | +0.000 | +0.000 | +0.000 |
| mixed | wo_tmt | +0.017 | +0.014 | +0.000 |
| mixed | wo_decay | +0.242 | +0.150 | +0.000 |
| mixed | wo_compatibility | -0.283 | -0.193 | -0.100 |
| mixed | wo_domain | -0.104 | -0.039 | +0.000 |
| mixed | wo_penalty | +0.000 | +0.000 | +0.000 |
| negative | wo_tmt | +0.000 | +0.000 | +0.000 |
| negative | wo_decay | +0.000 | +0.000 | +0.000 |
| negative | wo_compatibility | +0.000 | +0.000 | +0.000 |
| negative | wo_domain | +0.000 | +0.000 | +0.000 |
| negative | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_context | wo_tmt | +0.000 | +0.000 | +0.000 |
| task_context | wo_decay | +0.218 | +0.031 | -0.192 |
| task_context | wo_compatibility | +0.064 | +0.014 | +0.000 |
| task_context | wo_domain | -0.026 | +0.012 | +0.000 |
| task_context | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_decay | +0.000 | +0.014 | +0.000 |
| task_dependency | wo_compatibility | -0.017 | -0.093 | +0.000 |
| task_dependency | wo_domain | -0.133 | -0.124 | -0.050 |
| task_dependency | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_due | wo_tmt | -0.136 | -0.204 | +0.250 |
| task_due | wo_decay | +0.000 | +0.030 | +0.023 |
| task_due | wo_compatibility | -0.250 | -0.274 | -0.205 |
| task_due | wo_domain | -0.576 | -0.557 | -0.341 |
| task_due | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_priority | wo_tmt | +0.111 | +0.080 | -0.300 |
| task_priority | wo_decay | +0.000 | +0.000 | +0.000 |
| task_priority | wo_compatibility | -0.211 | -0.331 | -0.667 |
| task_priority | wo_domain | +0.033 | +0.017 | +0.000 |
| task_priority | wo_penalty | +0.100 | +0.044 | +0.000 |
| task_status | wo_tmt | +0.000 | -0.076 | -0.350 |
| task_status | wo_decay | +0.000 | +0.047 | +0.225 |
| task_status | wo_compatibility | -0.333 | -0.374 | -0.525 |
| task_status | wo_domain | -0.221 | -0.293 | -0.525 |
| task_status | wo_penalty | +0.000 | +0.000 | +0.000 |

## 8. Hard Case Results: top_k=5

| hard_case_tag | ablation | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | completed_error | todo_intrusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compatibility_chat_intrusion | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_decay | 1.000 | 0.920 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_compatibility | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| compatibility_chat_intrusion | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_plan | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_decay | 1.000 | 0.646 | 0.000 | - | 1.000 | - | - |
| decay_current_plan | wo_compatibility | 1.000 | 0.906 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_domain | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - |
| decay_current_plan | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - |
| decay_current_preference | full_qca | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_tmt | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_decay | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_compatibility | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_domain | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 |
| decay_current_preference | wo_penalty | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 |
| domain_wrong_urgent | full_qca | 1.000 | 0.945 | 1.000 | 1.000 | - | 0.000 | - |
| domain_wrong_urgent | wo_tmt | 0.500 | 0.275 | 1.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_decay | 1.000 | 0.964 | 1.000 | 1.000 | - | 0.000 | - |
| domain_wrong_urgent | wo_compatibility | 0.500 | 0.413 | 0.000 | 0.500 | - | 0.000 | - |
| domain_wrong_urgent | wo_domain | 0.000 | 0.000 | 0.000 | 0.000 | - | 0.000 | - |
| domain_wrong_urgent | wo_penalty | 1.000 | 0.945 | 1.000 | 1.000 | - | 0.000 | - |
| penalty_completed_task | full_qca | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_tmt | 0.500 | 0.296 | 0.000 | 0.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_decay | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_compatibility | 1.000 | 0.821 | 1.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_domain | 0.500 | 0.469 | 1.000 | 0.000 | 1.000 | 0.000 | - |
| penalty_completed_task | wo_penalty | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.000 | - |
| penalty_old_preference | full_qca | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_tmt | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_decay | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_compatibility | 0.500 | 0.413 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_domain | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.000 |
| penalty_old_preference | wo_penalty | 0.500 | 0.521 | 0.000 | - | 0.500 | - | 0.200 |
| tmt_deadline_order | full_qca | 0.500 | 0.444 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_tmt | 0.500 | 0.182 | 0.000 | 0.000 | 1.000 | 0.000 | - |
| tmt_deadline_order | wo_decay | 0.500 | 0.444 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_compatibility | 0.500 | 0.303 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_deadline_order | wo_domain | 0.500 | 0.235 | 0.000 | 0.000 | 1.000 | 0.000 | - |
| tmt_deadline_order | wo_penalty | 0.500 | 0.444 | 0.000 | 1.000 | 0.000 | 0.000 | - |
| tmt_far_distractor | full_qca | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - |
| tmt_far_distractor | wo_tmt | 0.500 | 0.469 | 1.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_decay | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - |
| tmt_far_distractor | wo_compatibility | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - |
| tmt_far_distractor | wo_domain | 0.500 | 0.303 | 0.000 | 0.500 | - | 0.000 | - |
| tmt_far_distractor | wo_penalty | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - |

## 9. Component Contribution Analysis

- `wo_tmt`: top_k=5 下 todo_recall 变化为 -0.054；task_due recall 变化为 -0.136，task_priority recall 变化为 +0.111。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 +0.079；chat_history recall 变化为 +0.000，chat_preference recall 变化为 +0.088。
- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 -0.201，todo_intrusion_rate 变化为 +0.031。
- `wo_domain`: top_k=5 下 task_context recall 变化为 -0.026，task_dependency recall 变化为 -0.133，mixed recall 变化为 -0.104。
- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 +0.000，todo_intrusion_rate 变化为 +0.021。

## 10. 结论

本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 TMT、decay、compatibility、domain 和 penalty 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。

修复后的消融已经阻断 `wo_tmt` 中的隐式 TMT penalty 调用，并将 `access` 与 `base` 解耦：`base` 只表示静态 importance/accessibility，non-todo `access` 只表示时间衰减系数。因此，`wo_tmt` 和 `wo_decay` 的结果比旧报告更接近纯粹消融。

如果 hard_case_tag 表中某个组件对应的困难样本显著下降，即使 overall 变化不大，也可以解释为该组件在目标场景中有效；如果 hard case 仍不下降，再考虑继续调权重、改函数形状或补更强的诊断样本。