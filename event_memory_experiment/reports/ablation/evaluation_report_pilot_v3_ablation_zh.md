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

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | wrong_domain_intrusion_rate | stale_memory_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.811 | 0.719 | 0.667 | 0.857 | 0.743 | 0.000 | 0.017 | 0.100 | 117.533 |
| wo_tmt | 0.593 | 0.470 | 0.389 | 0.167 | 0.679 | 0.000 | 0.167 | 0.100 | 115.711 |
| wo_decay | 0.491 | 0.477 | 0.489 | 0.857 | 0.250 | 0.000 | 0.000 | 0.500 | 111.350 |
| wo_compatibility | 0.750 | 0.596 | 0.444 | 0.524 | 0.821 | 0.000 | 0.017 | 0.050 | 116.522 |
| wo_domain | 0.593 | 0.476 | 0.278 | 0.333 | 0.643 | 0.000 | 0.300 | 0.050 | 116.272 |
| wo_penalty | 0.756 | 0.695 | 0.667 | 0.786 | 0.707 | 0.000 | 0.100 | 0.125 | 117.339 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | wrong_domain_intrusion_rate | stale_memory_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_qca | 0.913 | 0.762 | 0.667 | 0.857 | 0.921 | 0.000 | 0.050 | 0.350 | 234.878 |
| wo_tmt | 0.783 | 0.556 | 0.389 | 0.286 | 0.921 | 0.000 | 0.117 | 0.350 | 233.961 |
| wo_decay | 0.574 | 0.505 | 0.489 | 0.857 | 0.357 | 0.000 | 0.017 | 0.588 | 222.267 |
| wo_compatibility | 0.898 | 0.659 | 0.444 | 0.857 | 0.893 | 0.000 | 0.025 | 0.075 | 230.239 |
| wo_domain | 0.722 | 0.526 | 0.278 | 0.333 | 0.821 | 0.000 | 0.277 | 0.300 | 231.006 |
| wo_penalty | 0.913 | 0.757 | 0.667 | 0.857 | 0.921 | 0.000 | 0.108 | 0.350 | 234.883 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_qca` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate |
| --- | --- | --- | --- | --- | --- | --- |
| wo_tmt | -0.219 | -0.248 | -0.278 | -0.690 | -0.064 | +0.000 |
| wo_decay | -0.320 | -0.242 | -0.178 | +0.000 | -0.493 | +0.000 |
| wo_compatibility | -0.061 | -0.122 | -0.222 | -0.333 | +0.079 | +0.000 |
| wo_domain | -0.219 | -0.243 | -0.389 | -0.524 | -0.100 | +0.000 |
| wo_penalty | -0.056 | -0.024 | +0.000 | -0.071 | -0.036 | +0.000 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_qca | 0.800 | 0.753 | 0.571 | 0.000 |
| chat | wo_tmt | 0.714 | 0.682 | 0.429 | 0.000 |
| chat | wo_decay | 0.333 | 0.335 | 0.143 | 0.000 |
| chat | wo_compatibility | 0.905 | 0.694 | 0.286 | 0.000 |
| chat | wo_domain | 0.690 | 0.668 | 0.429 | 0.000 |
| chat | wo_penalty | 0.729 | 0.727 | 0.571 | 0.000 |
| task | full_qca | 0.818 | 0.697 | 0.727 | - |
| task | wo_tmt | 0.515 | 0.335 | 0.364 | - |
| task | wo_decay | 0.591 | 0.567 | 0.709 | - |
| task | wo_compatibility | 0.652 | 0.534 | 0.545 | - |
| task | wo_domain | 0.530 | 0.353 | 0.182 | - |
| task | wo_penalty | 0.773 | 0.674 | 0.727 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_preference | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_decay | -0.625 | -0.582 | -0.500 |
| chat_preference | wo_compatibility | +0.250 | +0.058 | +0.000 |
| chat_preference | wo_domain | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_penalty | -0.125 | -0.045 | +0.000 |
| chat_profile | wo_tmt | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_decay | -0.500 | -0.296 | +0.000 |
| chat_profile | wo_compatibility | +0.000 | -0.401 | -1.000 |
| chat_profile | wo_domain | -0.500 | -0.296 | +0.000 |
| chat_profile | wo_penalty | +0.000 | +0.000 | +0.000 |
| mixed | wo_tmt | -0.600 | -0.497 | -1.000 |
| mixed | wo_decay | -0.267 | -0.299 | -1.000 |
| mixed | wo_compatibility | -0.267 | -0.242 | -1.000 |
| mixed | wo_domain | -0.267 | -0.296 | -1.000 |
| mixed | wo_penalty | +0.000 | +0.000 | +0.000 |
| negative | wo_tmt | +0.000 | +0.000 | +0.000 |
| negative | wo_decay | +0.000 | +0.000 | +0.000 |
| negative | wo_compatibility | +0.000 | +0.000 | +0.000 |
| negative | wo_domain | +0.000 | +0.000 | +0.000 |
| negative | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_context | wo_tmt | +0.000 | +0.000 | +0.000 |
| task_context | wo_decay | -0.167 | -0.011 | +0.333 |
| task_context | wo_compatibility | +0.333 | +0.258 | +0.000 |
| task_context | wo_domain | -0.167 | -0.036 | +0.000 |
| task_context | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt | +0.000 | -0.080 | +0.000 |
| task_dependency | wo_decay | +0.000 | -0.139 | -0.200 |
| task_dependency | wo_compatibility | +0.000 | -0.123 | +0.000 |
| task_dependency | wo_domain | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_penalty | +0.000 | +0.000 | +0.000 |
| task_due | wo_tmt | -0.567 | -0.718 | -0.800 |
| task_due | wo_decay | -0.200 | -0.096 | +0.000 |
| task_due | wo_compatibility | -0.467 | -0.427 | -0.400 |
| task_due | wo_domain | -0.533 | -0.694 | -1.000 |
| task_due | wo_penalty | -0.100 | -0.050 | +0.000 |
| task_status | wo_tmt | -0.250 | -0.152 | +0.000 |
| task_status | wo_decay | -0.500 | -0.386 | -0.500 |
| task_status | wo_compatibility | -0.250 | -0.152 | +0.000 |
| task_status | wo_domain | +0.000 | -0.102 | -0.500 |
| task_status | wo_penalty | +0.000 | +0.000 | +0.000 |

## 8. Hard Case Results: top_k=5

| hard_case_tag | ablation | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | completed_error | todo_intrusion | wrong_domain_intrusion | stale_intrusion | far_before_near |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compatibility_chat_intrusion | full_qca | 1.000 | 0.885 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_tmt | 1.000 | 0.885 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_decay | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.400 | - |
| compatibility_chat_intrusion | wo_compatibility | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_domain | 1.000 | 0.885 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_penalty | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.200 | - |
| completed_intrusion_check | full_qca | 1.000 | 0.906 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_tmt | 0.500 | 0.182 | 0.000 | 0.500 | - | 0.000 | - | 0.400 | - | 1.000 |
| completed_intrusion_check | wo_decay | 1.000 | 0.906 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_compatibility | 0.000 | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_domain | 0.500 | 0.202 | 0.000 | 0.500 | - | 0.000 | - | 0.400 | - | 0.000 |
| completed_intrusion_check | wo_penalty | 1.000 | 0.885 | 1.000 | 1.000 | - | 0.000 | - | 0.200 | - | 0.000 |
| decay_current_plan | full_qca | 0.500 | 0.202 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| decay_current_plan | wo_tmt | 0.500 | 0.202 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| decay_current_plan | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | 0.600 | - |
| decay_current_plan | wo_compatibility | 0.500 | 0.272 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| decay_current_plan | wo_domain | 0.500 | 0.202 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| decay_current_plan | wo_penalty | 0.500 | 0.202 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| decay_current_preference | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| decay_current_preference | wo_compatibility | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| domain_wrong_urgent | full_qca | 1.000 | 0.885 | 1.000 | 1.000 | - | 0.000 | - | 0.200 | - | 0.000 |
| domain_wrong_urgent | wo_tmt | 0.000 | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.600 | - | 1.000 |
| domain_wrong_urgent | wo_decay | 1.000 | 0.906 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_compatibility | 0.000 | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.200 | - | 0.000 |
| domain_wrong_urgent | wo_domain | 0.500 | 0.202 | 0.000 | 0.500 | - | 0.000 | - | 0.400 | - | 0.000 |
| domain_wrong_urgent | wo_penalty | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - | 0.400 | - | 0.000 |
| mixed_plan_preference | full_qca | 0.600 | 0.497 | 1.000 | 1.000 | 0.400 | - | - | - | - | - |
| mixed_plan_preference | wo_tmt | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | - |
| mixed_plan_preference | wo_decay | 0.333 | 0.198 | 0.000 | 1.000 | 0.000 | - | - | - | - | - |
| mixed_plan_preference | wo_compatibility | 0.333 | 0.255 | 0.000 | 0.000 | 0.500 | - | - | - | - | - |
| mixed_plan_preference | wo_domain | 0.333 | 0.201 | 0.000 | 1.000 | 0.000 | - | - | - | - | - |
| mixed_plan_preference | wo_penalty | 0.600 | 0.497 | 1.000 | 1.000 | 0.400 | - | - | - | - | - |
| negative_unknown_domain | full_qca | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_tmt | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_decay | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_compatibility | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_domain | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.600 | - | - |
| negative_unknown_domain | wo_penalty | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| noise_resilience | full_qca | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.400 | - |
| noise_resilience | wo_tmt | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.400 | - |
| noise_resilience | wo_decay | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.400 | - |
| noise_resilience | wo_compatibility | 0.500 | 0.352 | 0.000 | 1.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| noise_resilience | wo_domain | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.200 | 0.200 | - |
| noise_resilience | wo_penalty | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.400 | - |
| old_preference_intrusion_check | full_qca | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_tmt | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| old_preference_intrusion_check | wo_compatibility | 1.000 | 0.554 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_domain | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_penalty | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_completed_task | full_qca | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_tmt | 0.500 | 0.296 | 0.000 | 0.000 | 1.000 | 0.000 | - | 0.200 | - | 1.000 |
| penalty_completed_task | wo_decay | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_compatibility | 1.000 | 0.772 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_domain | 0.500 | 0.296 | 0.000 | 0.000 | 1.000 | 0.000 | - | 0.400 | - | 0.000 |
| penalty_completed_task | wo_penalty | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.200 | - | 0.000 |
| penalty_old_preference | full_qca | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_tmt | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| penalty_old_preference | wo_compatibility | 1.000 | 0.538 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_domain | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_penalty | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_tmt | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_decay | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.800 | - |
| profile_stable_old | wo_compatibility | 1.000 | 0.599 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_domain | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| stale_memory_filter | full_qca | 0.500 | 0.107 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| stale_memory_filter | wo_tmt | 0.500 | 0.107 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| stale_memory_filter | wo_decay | 0.500 | 0.275 | 1.000 | - | 0.500 | - | - | 0.000 | 0.600 | - |
| stale_memory_filter | wo_compatibility | 1.000 | 0.457 | 0.000 | - | 1.000 | - | - | 0.000 | 0.200 | - |
| stale_memory_filter | wo_domain | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.200 | 0.000 | - |
| stale_memory_filter | wo_penalty | 0.500 | 0.107 | 0.000 | - | 0.500 | - | - | 0.000 | 0.200 | - |
| task_dependency_current | full_qca | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_tmt | 1.000 | 0.920 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_decay | 1.000 | 0.861 | 0.800 | - | 1.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_compatibility | 1.000 | 0.877 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_domain | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - | 0.200 | - | - |
| task_dependency_current | wo_penalty | 1.000 | 1.000 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | full_qca | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_tmt | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_decay | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_compatibility | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_domain | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.200 | - | - |
| task_status_completed_contrast | wo_penalty | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| tmt_deadline_order | full_qca | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_tmt | 0.500 | 0.182 | 0.000 | 0.000 | 1.000 | 0.000 | - | 0.400 | - | 1.000 |
| tmt_deadline_order | wo_decay | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_compatibility | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_domain | 0.500 | 0.235 | 0.000 | 0.000 | 1.000 | 0.000 | - | 0.400 | - | 0.000 |
| tmt_deadline_order | wo_penalty | 1.000 | 0.885 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.200 | - | 0.000 |
| tmt_far_distractor | full_qca | 1.000 | 0.973 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_tmt | 0.667 | 0.420 | 1.000 | 0.667 | - | 0.000 | - | 0.400 | - | 1.000 |
| tmt_far_distractor | wo_decay | 1.000 | 0.973 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_compatibility | 0.667 | 0.763 | 1.000 | 0.667 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_domain | 0.333 | 0.265 | 0.000 | 0.333 | - | 0.000 | - | 0.400 | - | 0.000 |
| tmt_far_distractor | wo_penalty | 1.000 | 0.943 | 1.000 | 1.000 | - | 0.000 | - | 0.200 | - | 0.000 |
| wrong_domain_status | full_qca | 1.000 | 0.772 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_tmt | 0.500 | 0.469 | 1.000 | - | 0.500 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_compatibility | 0.500 | 0.469 | 1.000 | - | 0.500 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_domain | 1.000 | 0.568 | 0.000 | - | 1.000 | - | - | 0.200 | - | - |
| wrong_domain_status | wo_penalty | 1.000 | 0.772 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |

## 9. Component Contribution Analysis

- `wo_tmt`: top_k=5 下 todo_recall 变化为 -0.690；task_due recall 变化为 -0.567，task_priority recall 变化为 -。这说明当前 Pilot v2 中 TMT 的贡献没有按预期显现，可能是 accessible_score 已经覆盖了部分 deadline/task salience，或当前 TMT 权重/函数仍需校准。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 -0.493；chat_history recall 变化为 -，chat_preference recall 变化为 -0.625。
- `wo_compatibility`: top_k=5 下 memory_NDCG 变化为 -0.122，todo_intrusion_rate 变化为 +0.000。
- `wo_domain`: top_k=5 下 task_context recall 变化为 -0.167，task_dependency recall 变化为 +0.000，mixed recall 变化为 -0.267。
- `wo_penalty`: top_k=5 下 completed_task_error_rate 变化为 +0.000，todo_intrusion_rate 变化为 +0.000。

## 10. 结论

本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 TMT、decay、compatibility、domain 和 penalty 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。

修复后的消融已经阻断 `wo_tmt` 中的隐式 TMT penalty 调用，并将 `access` 与 `base` 解耦：`base` 只表示静态 importance/accessibility，non-todo `access` 只表示时间衰减系数。因此，`wo_tmt` 和 `wo_decay` 的结果比旧报告更接近纯粹消融。

如果 hard_case_tag 表中某个组件对应的困难样本显著下降，即使 overall 变化不大，也可以解释为该组件在目标场景中有效；如果 hard case 仍不下降，再考虑继续调权重、改函数形状或补更强的诊断样本。