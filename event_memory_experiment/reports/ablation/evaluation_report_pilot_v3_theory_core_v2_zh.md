# MU-Level Theory-Core v2 Ablation 实验报告

## 1. 实验目标

本实验在 MU-level retrieval 上验证 Theory-Core v2 连乘公式的组件贡献：bounded similarity、role-level intent matrix、soft-hard domain gate、conditional TMT/Eisenhower accessibility 与 retrospective decay。主表使用 top_k=5，top_k=10 作为补充。

## 2. Ablation Variants

| ablation | 含义 |
| --- | --- |
| full_core_v2 | 完整 v2 连乘公式：Sim × IntentGate × DomainGate × Accessibility |
| wo_embedding | Sim 强制回退为纯 Token 匹配 |
| wo_decay | non-todo 的 accessibility 不使用 forgetting decay，改用 accessible_score |
| wo_role_matrix | IntentGate 强制设为 1 |
| wo_domain_gate | DomainGate 强制设为 1 |
| wo_tmt_condition | TMT 在所有 query_subtype 下均生效 |
| wo_eisenhower | 移除四象限调制，退化为纯 Deadline TMT |

## 3. Overall Results: top_k=5

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | wrong_domain_intrusion_rate | stale_memory_intrusion_rate | active_todo_precision | wrong_domain_urgent_intrusion_rate | stale_preference_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core_v2 | 0.750 | 0.701 | 0.556 | 0.857 | 0.643 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 122.372 |
| wo_embedding | 0.815 | 0.719 | 0.500 | 0.714 | 0.786 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 119.844 |
| wo_decay | 0.306 | 0.308 | 0.278 | 0.714 | 0.036 | 0.000 | 0.000 | 0.550 | 1.000 | 0.000 | 0.400 | 110.239 |
| wo_role_matrix | 0.694 | 0.548 | 0.333 | 0.762 | 0.643 | 0.000 | 0.000 | 0.000 | 0.333 | 0.000 | 0.000 | 118.589 |
| wo_domain_gate | 0.676 | 0.640 | 0.556 | 0.857 | 0.500 | 0.000 | 0.267 | 0.000 | 1.000 | 0.167 | 0.000 | 117.272 |
| wo_tmt_condition | 0.731 | 0.690 | 0.556 | 0.714 | 0.643 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 123.061 |
| wo_eisenhower | 0.731 | 0.697 | 0.556 | 0.810 | 0.643 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 123.206 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | wrong_domain_intrusion_rate | stale_memory_intrusion_rate | active_todo_precision | wrong_domain_urgent_intrusion_rate | stale_preference_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core_v2 | 0.944 | 0.763 | 0.556 | 0.857 | 0.964 | 0.000 | 0.033 | 0.188 | 1.000 | 0.017 | 0.250 | 244.356 |
| wo_embedding | 0.944 | 0.762 | 0.500 | 0.857 | 0.964 | 0.000 | 0.033 | 0.188 | 1.000 | 0.017 | 0.250 | 236.178 |
| wo_decay | 0.333 | 0.317 | 0.278 | 0.714 | 0.071 | 0.000 | 0.033 | 0.588 | 1.000 | 0.017 | 0.617 | 225.017 |
| wo_role_matrix | 0.796 | 0.587 | 0.333 | 0.762 | 0.821 | 0.000 | 0.000 | 0.188 | 0.333 | 0.000 | 0.250 | 244.739 |
| wo_domain_gate | 0.917 | 0.724 | 0.556 | 0.857 | 0.893 | 0.000 | 0.258 | 0.100 | 1.000 | 0.100 | 0.133 | 240.256 |
| wo_tmt_condition | 0.926 | 0.753 | 0.556 | 0.714 | 0.964 | 0.000 | 0.033 | 0.188 | 1.000 | 0.017 | 0.250 | 244.689 |
| wo_eisenhower | 0.926 | 0.760 | 0.556 | 0.810 | 0.964 | 0.000 | 0.033 | 0.188 | 1.000 | 0.017 | 0.250 | 242.356 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_core_v2` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate | delta_active_todo_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wo_embedding | +0.065 | +0.018 | -0.056 | -0.143 | +0.143 | +0.000 | +0.000 |
| wo_decay | -0.444 | -0.393 | -0.278 | -0.143 | -0.607 | +0.000 | +0.000 |
| wo_role_matrix | -0.056 | -0.153 | -0.222 | -0.095 | +0.000 | +0.000 | -0.667 |
| wo_domain_gate | -0.074 | -0.061 | +0.000 | +0.000 | -0.143 | +0.000 | +0.000 |
| wo_tmt_condition | -0.019 | -0.011 | +0.000 | -0.143 | +0.000 | +0.000 | +0.000 |
| wo_eisenhower | -0.019 | -0.004 | +0.000 | -0.048 | +0.000 | +0.000 | +0.000 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_core_v2 | 0.857 | 0.845 | 0.714 | 0.000 |
| chat | wo_embedding | 0.810 | 0.700 | 0.286 | 0.000 |
| chat | wo_decay | 0.143 | 0.143 | 0.000 | 0.000 |
| chat | wo_role_matrix | 0.952 | 0.856 | 0.714 | 0.000 |
| chat | wo_domain_gate | 0.810 | 0.817 | 0.714 | 0.000 |
| chat | wo_tmt_condition | 0.810 | 0.818 | 0.714 | 0.000 |
| chat | wo_eisenhower | 0.857 | 0.845 | 0.714 | 0.000 |
| task | full_core_v2 | 0.682 | 0.609 | 0.455 | - |
| task | wo_embedding | 0.818 | 0.730 | 0.636 | - |
| task | wo_decay | 0.409 | 0.413 | 0.455 | - |
| task | wo_role_matrix | 0.530 | 0.352 | 0.091 | - |
| task | wo_domain_gate | 0.591 | 0.527 | 0.455 | - |
| task | wo_tmt_condition | 0.682 | 0.609 | 0.455 | - |
| task | wo_eisenhower | 0.652 | 0.602 | 0.455 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_preference | wo_embedding | +0.000 | -0.136 | -0.500 |
| chat_preference | wo_decay | -0.750 | -0.837 | -1.000 |
| chat_preference | wo_role_matrix | +0.250 | +0.101 | +0.000 |
| chat_preference | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_embedding | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_decay | -1.000 | -0.648 | +0.000 |
| chat_profile | wo_role_matrix | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| mixed | wo_embedding | -0.333 | -0.469 | -1.000 |
| mixed | wo_decay | -1.000 | -0.920 | -1.000 |
| mixed | wo_role_matrix | -0.333 | -0.326 | +0.000 |
| mixed | wo_domain_gate | -0.333 | -0.197 | +0.000 |
| mixed | wo_tmt_condition | -0.333 | -0.192 | +0.000 |
| mixed | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| negative | wo_embedding | +0.000 | +0.000 | +0.000 |
| negative | wo_decay | +0.000 | +0.000 | +0.000 |
| negative | wo_role_matrix | +0.000 | +0.000 | +0.000 |
| negative | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| negative | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| negative | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_context | wo_embedding | +0.167 | +0.067 | +0.000 |
| task_context | wo_decay | -0.167 | -0.276 | +0.000 |
| task_context | wo_role_matrix | +0.167 | +0.110 | +0.333 |
| task_context | wo_domain_gate | +0.000 | -0.067 | +0.000 |
| task_context | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_context | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_embedding | +0.500 | +0.429 | +0.000 |
| task_dependency | wo_decay | -0.500 | -0.264 | +0.000 |
| task_dependency | wo_role_matrix | -0.500 | -0.264 | +0.000 |
| task_dependency | wo_domain_gate | +0.000 | -0.027 | +0.000 |
| task_dependency | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_due | wo_embedding | +0.100 | +0.036 | +0.000 |
| task_due | wo_decay | -0.100 | -0.040 | +0.000 |
| task_due | wo_role_matrix | -0.333 | -0.578 | -1.000 |
| task_due | wo_domain_gate | -0.100 | -0.081 | +0.000 |
| task_due | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_due | wo_eisenhower | -0.067 | -0.014 | +0.000 |
| task_status | wo_embedding | +0.000 | +0.262 | +1.000 |
| task_status | wo_decay | -0.750 | -0.429 | +0.000 |
| task_status | wo_role_matrix | +0.000 | +0.000 | +0.000 |
| task_status | wo_domain_gate | -0.250 | -0.136 | +0.000 |
| task_status | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_status | wo_eisenhower | +0.000 | +0.000 | +0.000 |

## 8. Hard Case Results: top_k=5

| hard_case_tag | ablation | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | completed_error | todo_intrusion | wrong_domain_intrusion | stale_intrusion | far_before_near |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compatibility_chat_intrusion | full_core_v2 | 1.000 | 0.939 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_embedding | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| compatibility_chat_intrusion | wo_role_matrix | 1.000 | 0.939 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_domain_gate | 1.000 | 0.939 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_tmt_condition | 1.000 | 0.939 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_eisenhower | 1.000 | 0.939 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| completed_intrusion_check | full_core_v2 | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_embedding | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_decay | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_role_matrix | 0.500 | 0.303 | 0.000 | 0.500 | - | 0.667 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_domain_gate | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.400 | - | 0.000 |
| completed_intrusion_check | wo_tmt_condition | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| completed_intrusion_check | wo_eisenhower | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| decay_current_plan | full_core_v2 | 0.500 | 0.444 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_embedding | 1.000 | 0.646 | 0.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | 0.800 | - |
| decay_current_plan | wo_role_matrix | 0.500 | 0.272 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_domain_gate | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.200 | 0.000 | - |
| decay_current_plan | wo_tmt_condition | 0.500 | 0.444 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_eisenhower | 0.500 | 0.444 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_preference | full_core_v2 | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_embedding | 1.000 | 0.913 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| decay_current_preference | wo_role_matrix | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_domain_gate | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_tmt_condition | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_eisenhower | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| domain_wrong_urgent | full_core_v2 | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_embedding | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_decay | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_role_matrix | 0.500 | 0.303 | 0.000 | 0.500 | - | 0.667 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_domain_gate | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.400 | - | 0.000 |
| domain_wrong_urgent | wo_tmt_condition | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_eisenhower | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| mixed_plan_preference | full_core_v2 | 1.000 | 0.920 | 1.000 | 1.000 | 1.000 | - | - | - | - | - |
| mixed_plan_preference | wo_embedding | 0.667 | 0.451 | 0.000 | 0.000 | 1.000 | - | - | - | - | - |
| mixed_plan_preference | wo_decay | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | - | - | - |
| mixed_plan_preference | wo_role_matrix | 0.667 | 0.594 | 1.000 | 1.000 | 0.500 | - | - | - | - | - |
| mixed_plan_preference | wo_domain_gate | 0.667 | 0.723 | 1.000 | 1.000 | 0.500 | - | - | - | - | - |
| mixed_plan_preference | wo_tmt_condition | 0.667 | 0.728 | 1.000 | 0.000 | 1.000 | - | - | - | - | - |
| mixed_plan_preference | wo_eisenhower | 1.000 | 0.920 | 1.000 | 1.000 | 1.000 | - | - | - | - | - |
| negative_unknown_domain | full_core_v2 | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_embedding | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_decay | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_role_matrix | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_domain_gate | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_tmt_condition | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| negative_unknown_domain | wo_eisenhower | 1.000 | 1.000 | 0.000 | - | - | - | - | 0.000 | - | - |
| noise_resilience | full_core_v2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| noise_resilience | wo_embedding | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| noise_resilience | wo_decay | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.800 | - |
| noise_resilience | wo_role_matrix | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| noise_resilience | wo_domain_gate | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.200 | 0.000 | - |
| noise_resilience | wo_tmt_condition | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| noise_resilience | wo_eisenhower | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | - | - | 0.000 | 0.000 | - |
| old_preference_intrusion_check | full_core_v2 | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_embedding | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| old_preference_intrusion_check | wo_role_matrix | 1.000 | 0.906 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_domain_gate | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_tmt_condition | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| old_preference_intrusion_check | wo_eisenhower | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_completed_task | full_core_v2 | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_embedding | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_decay | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_role_matrix | 1.000 | 0.538 | 0.000 | 1.000 | 1.000 | 0.667 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_domain_gate | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.400 | - | 0.000 |
| penalty_completed_task | wo_tmt_condition | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_eisenhower | 1.000 | 0.939 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_old_preference | full_core_v2 | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_embedding | 0.500 | 0.444 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| penalty_old_preference | wo_role_matrix | 1.000 | 0.906 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_domain_gate | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_tmt_condition | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| penalty_old_preference | wo_eisenhower | 0.500 | 0.704 | 1.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | full_core_v2 | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_embedding | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 | - | 0.400 | - |
| profile_stable_old | wo_role_matrix | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_domain_gate | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_tmt_condition | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| profile_stable_old | wo_eisenhower | 1.000 | 0.648 | 0.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| stale_memory_filter | full_core_v2 | 0.500 | 0.521 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| stale_memory_filter | wo_embedding | 0.500 | 0.521 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| stale_memory_filter | wo_decay | 0.500 | 0.138 | 0.000 | - | 0.500 | - | - | 0.000 | 0.800 | - |
| stale_memory_filter | wo_role_matrix | 0.500 | 0.320 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| stale_memory_filter | wo_domain_gate | 0.500 | 0.413 | 0.000 | - | 0.500 | - | - | 0.200 | 0.000 | - |
| stale_memory_filter | wo_tmt_condition | 0.500 | 0.521 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| stale_memory_filter | wo_eisenhower | 0.500 | 0.521 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| task_dependency_current | full_core_v2 | 0.500 | 0.264 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_dependency_current | wo_embedding | 1.000 | 0.693 | 0.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_role_matrix | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | - | - |
| task_dependency_current | wo_domain_gate | 0.500 | 0.237 | 0.000 | - | 0.500 | - | - | 0.200 | - | - |
| task_dependency_current | wo_tmt_condition | 0.500 | 0.264 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_dependency_current | wo_eisenhower | 0.500 | 0.264 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_status_completed_contrast | full_core_v2 | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_embedding | 1.000 | 0.913 | 1.000 | - | 1.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_role_matrix | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_domain_gate | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.200 | - | - |
| task_status_completed_contrast | wo_tmt_condition | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| task_status_completed_contrast | wo_eisenhower | 0.500 | 0.352 | 0.000 | - | 0.500 | - | - | 0.000 | - | - |
| tmt_deadline_order | full_core_v2 | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_embedding | 1.000 | 0.885 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_decay | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_role_matrix | 0.500 | 0.303 | 0.000 | 1.000 | 0.000 | 0.667 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_domain_gate | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.400 | - | 0.000 |
| tmt_deadline_order | wo_tmt_condition | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_eisenhower | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | full_core_v2 | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_embedding | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_decay | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_role_matrix | 0.333 | 0.271 | 0.000 | 0.333 | - | 0.667 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_domain_gate | 1.000 | 0.921 | 1.000 | 1.000 | - | 0.000 | - | 0.400 | - | 0.000 |
| tmt_far_distractor | wo_tmt_condition | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_eisenhower | 0.667 | 0.895 | 1.000 | 0.667 | - | 0.000 | - | 0.000 | - | 0.000 |
| wrong_domain_status | full_core_v2 | 1.000 | 0.507 | 0.000 | - | 1.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_embedding | 0.500 | 0.469 | 1.000 | - | 0.500 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_decay | 0.000 | 0.000 | 0.000 | - | 0.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_role_matrix | 1.000 | 0.507 | 0.000 | - | 1.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_domain_gate | 0.500 | 0.235 | 0.000 | - | 0.500 | - | - | 0.200 | - | - |
| wrong_domain_status | wo_tmt_condition | 1.000 | 0.507 | 0.000 | - | 1.000 | - | - | 0.000 | - | - |
| wrong_domain_status | wo_eisenhower | 1.000 | 0.507 | 0.000 | - | 1.000 | - | - | 0.000 | - | - |

## 9. Component Contribution Analysis

- `wo_embedding`: top_k=5 下 memory_recall 变化为 +0.065，memory_NDCG 变化为 +0.018。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 -0.607；chat_history recall 变化为 -，chat_preference recall 变化为 -0.750。
- `wo_role_matrix`: top_k=5 下 todo_intrusion_rate 变化为 +0.000，active_todo_precision 变化为 -0.667。
- `wo_domain_gate`: top_k=5 下 wrong_domain_urgent_intrusion_rate 变化为 +0.167。
- `wo_tmt_condition`: top_k=5 下 task_context recall 变化为 +0.000。
- `wo_eisenhower`: top_k=5 下 deadline_ranking_accuracy 变化为 +0.000，far_deadline_before_near_rate 变化为 +0.000。

## 10. 结论

本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 bounded similarity、role matrix、domain gate、conditional TMT 和 Eisenhower 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。

当前版本已将主方法改为 `Sim × IntentGate × DomainGate × Accessibility`。其中 Sim 有 embedding/floor 兜底，IntentGate 是角色级矩阵，DomainGate 负责软硬结合的跨域隔离，TMT 只在任务调度型 query 下生效。