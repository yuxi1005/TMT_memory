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
| full_qca | 0.545 | 0.569 | 0.610 | 0.495 | 0.506 | 0.000 | 85.055 |
| wo_tmt | 0.579 | 0.576 | 0.550 | 0.569 | 0.509 | 0.000 | 84.075 |
| wo_decay | 0.635 | 0.651 | 0.725 | 0.560 | 0.603 | 0.000 | 78.355 |
| wo_compatibility | 0.351 | 0.342 | 0.335 | 0.237 | 0.315 | 0.045 | 87.795 |
| wo_domain | 0.379 | 0.411 | 0.445 | 0.182 | 0.471 | 0.000 | 81.100 |
| wo_penalty | 0.564 | 0.576 | 0.610 | 0.518 | 0.510 | 0.000 | 84.845 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.711 | 0.631 | 0.610 | 0.695 | 0.639 | 0.000 | 167.805 |
| wo_tmt | 0.791 | 0.659 | 0.550 | 0.855 | 0.639 | 0.000 | 166.125 |
| wo_decay | 0.797 | 0.716 | 0.725 | 0.813 | 0.717 | 0.035 | 155.200 |
| wo_compatibility | 0.560 | 0.429 | 0.335 | 0.456 | 0.624 | 0.040 | 174.465 |
| wo_domain | 0.503 | 0.455 | 0.445 | 0.290 | 0.583 | 0.000 | 168.720 |
| wo_penalty | 0.736 | 0.642 | 0.610 | 0.705 | 0.661 | 0.000 | 168.285 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate |
| --- | --- | --- | --- | --- | --- | --- |
| wo_tmt | +0.033 | +0.007 | -0.060 | +0.074 | +0.003 | +0.000 |
| wo_decay | +0.089 | +0.082 | +0.115 | +0.065 | +0.097 | +0.000 |
| wo_compatibility | -0.194 | -0.227 | -0.275 | -0.258 | -0.192 | +0.045 |
| wo_domain | -0.166 | -0.158 | -0.165 | -0.313 | -0.035 | +0.000 |
| wo_penalty | +0.018 | +0.006 | +0.000 | +0.023 | +0.004 | +0.000 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_qca | 0.596 | 0.634 | 0.600 | 0.000 |
| chat | wo_tmt | 0.601 | 0.638 | 0.600 | 0.000 |
| chat | wo_decay | 0.770 | 0.777 | 0.771 | 0.000 |
| chat | wo_compatibility | 0.418 | 0.482 | 0.529 | 0.045 |
| chat | wo_domain | 0.471 | 0.546 | 0.571 | 0.000 |
| chat | wo_penalty | 0.606 | 0.633 | 0.600 | 0.000 |
| task | full_qca | 0.518 | 0.535 | 0.615 | - |
| task | wo_tmt | 0.567 | 0.543 | 0.523 | - |
| task | wo_decay | 0.562 | 0.583 | 0.700 | - |
| task | wo_compatibility | 0.315 | 0.268 | 0.231 | - |
| task | wo_domain | 0.329 | 0.339 | 0.377 | - |
| task | wo_penalty | 0.541 | 0.545 | 0.615 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_history | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_history | wo_decay | +0.000 | +0.167 | +0.900 |
| chat_history | wo_compatibility | +0.000 | +0.181 | +0.900 |
| chat_history | wo_domain | -0.667 | -0.461 | +0.000 |
| chat_history | wo_penalty | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_decay | +0.167 | +0.197 | +0.150 |
| chat_preference | wo_compatibility | -0.117 | -0.099 | -0.100 |
| chat_preference | wo_domain | +0.000 | -0.037 | -0.100 |
| chat_preference | wo_penalty | +0.033 | -0.003 | +0.000 |
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
| task_context | wo_decay | +0.283 | +0.147 | +0.050 |
| task_context | wo_compatibility | +0.083 | +0.046 | +0.000 |
| task_context | wo_domain | -0.033 | +0.042 | +0.000 |
| task_context | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_decay | +0.000 | +0.014 | +0.000 |
| task_dependency | wo_compatibility | -0.017 | -0.093 | +0.000 |
| task_dependency | wo_domain | -0.133 | -0.124 | -0.050 |
| task_dependency | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_due | wo_tmt | +0.150 | +0.087 | +0.550 |
| task_due | wo_decay | +0.000 | +0.061 | +0.050 |
| task_due | wo_compatibility | -0.400 | -0.444 | -0.450 |
| task_due | wo_domain | -0.667 | -0.626 | -0.450 |
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

No hard_case_tag rows found.

## 9. Component Contribution Analysis

- `wo_tmt`: top_k=5 下 todo_recall 变化为 +0.074；task_due recall 变化为 +0.150，task_priority recall 变化为 +0.111。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 +0.097；chat_history recall 变化为 +0.000，chat_preference recall 变化为 +0.167。
- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 -0.227，todo_intrusion_rate 变化为 +0.045。
- `wo_domain`: top_k=5 下 task_context recall 变化为 -0.033，task_dependency recall 变化为 -0.133，mixed recall 变化为 -0.104。
- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 +0.000，todo_intrusion_rate 变化为 +0.000。

## 10. 结论

本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 TMT、decay、compatibility、domain 和 penalty 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。

修复后的消融已经阻断 `wo_tmt` 中的隐式 TMT penalty 调用，并将 `access` 与 `base` 解耦：`base` 只表示静态 importance/accessibility，non-todo `access` 只表示时间衰减系数。因此，`wo_tmt` 和 `wo_decay` 的结果比旧报告更接近纯粹消融。

如果 hard_case_tag 表中某个组件对应的困难样本显著下降，即使 overall 变化不大，也可以解释为该组件在目标场景中有效；如果 hard case 仍不下降，再考虑继续调权重、改函数形状或补更强的诊断样本。