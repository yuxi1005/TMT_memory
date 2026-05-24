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
| full_core_v2 | 0.559 | 0.544 | 0.485 | 0.436 | 0.520 | 0.076 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 83.477 |
| wo_embedding | 0.562 | 0.557 | 0.553 | 0.462 | 0.568 | 0.234 | 0.000 | 0.000 | 0.956 | 0.000 | 0.000 | 78.731 |
| wo_decay | 0.542 | 0.491 | 0.390 | 0.495 | 0.509 | 0.076 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 82.152 |
| wo_role_matrix | 0.354 | 0.283 | 0.117 | 0.356 | 0.318 | 0.424 | 0.000 | 0.000 | 0.474 | 0.000 | 0.000 | 75.398 |
| wo_domain_gate | 0.559 | 0.542 | 0.485 | 0.436 | 0.520 | 0.097 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 83.004 |
| wo_tmt_condition | 0.558 | 0.543 | 0.485 | 0.433 | 0.520 | 0.076 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 83.269 |
| wo_eisenhower | 0.563 | 0.544 | 0.443 | 0.475 | 0.520 | 0.076 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 83.769 |

## 4. Overall Results: top_k=10

| ablation | memory_recall | memory_NDCG | memory_top1_accuracy | todo_recall | non_todo_recall | todo_intrusion_rate | wrong_domain_intrusion_rate | stale_memory_intrusion_rate | active_todo_precision | wrong_domain_urgent_intrusion_rate | stale_preference_intrusion_rate | memory_token_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_core_v2 | 0.755 | 0.619 | 0.485 | 0.689 | 0.726 | 0.110 | 0.000 | 0.000 | 0.923 | 0.000 | 0.000 | 169.898 |
| wo_embedding | 0.753 | 0.630 | 0.553 | 0.782 | 0.716 | 0.340 | 0.000 | 0.000 | 0.909 | 0.000 | 0.000 | 162.720 |
| wo_decay | 0.720 | 0.556 | 0.390 | 0.583 | 0.770 | 0.066 | 0.000 | 0.000 | 0.920 | 0.000 | 0.000 | 168.614 |
| wo_role_matrix | 0.636 | 0.398 | 0.117 | 0.590 | 0.657 | 0.322 | 0.000 | 0.000 | 0.708 | 0.000 | 0.000 | 160.030 |
| wo_domain_gate | 0.755 | 0.616 | 0.485 | 0.689 | 0.726 | 0.079 | 0.000 | 0.000 | 0.924 | 0.000 | 0.000 | 169.443 |
| wo_tmt_condition | 0.743 | 0.614 | 0.485 | 0.633 | 0.726 | 0.110 | 0.000 | 0.000 | 0.923 | 0.000 | 0.000 | 169.920 |
| wo_eisenhower | 0.762 | 0.620 | 0.443 | 0.772 | 0.679 | 0.110 | 0.000 | 0.000 | 0.923 | 0.000 | 0.000 | 169.678 |

## 5. Component Delta: top_k=5

下表为各消融相对 `full_core_v2` 的变化，负值表示移除该组件后指标下降。

| ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy | delta_todo_recall | delta_non_todo_recall | delta_todo_intrusion_rate | delta_active_todo_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| wo_embedding | +0.003 | +0.013 | +0.068 | +0.025 | +0.048 | +0.159 | -0.044 |
| wo_decay | -0.017 | -0.053 | -0.095 | +0.059 | -0.010 | +0.000 | +0.000 |
| wo_role_matrix | -0.205 | -0.261 | -0.367 | -0.080 | -0.202 | +0.348 | -0.526 |
| wo_domain_gate | +0.000 | -0.002 | +0.000 | +0.000 | +0.000 | +0.021 | +0.000 |
| wo_tmt_condition | -0.001 | -0.001 | +0.000 | -0.003 | +0.000 | +0.000 | +0.000 |
| wo_eisenhower | +0.004 | +0.000 | -0.042 | +0.039 | +0.000 | +0.000 | +0.000 |

## 6. By Query Mode: top_k=5

| query_mode | ablation | memory_recall | memory_NDCG | top1_acc | todo_intrusion |
| --- | --- | --- | --- | --- | --- |
| chat | full_core_v2 | 0.551 | 0.556 | 0.443 | 0.076 |
| chat | wo_embedding | 0.555 | 0.569 | 0.523 | 0.234 |
| chat | wo_decay | 0.484 | 0.418 | 0.239 | 0.076 |
| chat | wo_role_matrix | 0.329 | 0.318 | 0.239 | 0.424 |
| chat | wo_domain_gate | 0.551 | 0.555 | 0.443 | 0.097 |
| chat | wo_tmt_condition | 0.548 | 0.554 | 0.443 | 0.076 |
| chat | wo_eisenhower | 0.551 | 0.556 | 0.443 | 0.076 |
| task | full_core_v2 | 0.563 | 0.538 | 0.506 | - |
| task | wo_embedding | 0.565 | 0.551 | 0.568 | - |
| task | wo_decay | 0.571 | 0.527 | 0.466 | - |
| task | wo_role_matrix | 0.366 | 0.266 | 0.057 | - |
| task | wo_domain_gate | 0.563 | 0.535 | 0.506 | - |
| task | wo_tmt_condition | 0.563 | 0.538 | 0.506 | - |
| task | wo_eisenhower | 0.569 | 0.539 | 0.443 | - |

## 7. By Query Subtype Delta: top_k=5

| query_subtype | ablation | delta_memory_recall | delta_memory_NDCG | delta_memory_top1_accuracy |
| --- | --- | --- | --- | --- |
| chat_history | wo_embedding | +0.000 | +0.000 | +0.000 |
| chat_history | wo_decay | +0.000 | +0.000 | +0.000 |
| chat_history | wo_role_matrix | +0.000 | +0.000 | +0.000 |
| chat_history | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| chat_history | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| chat_history | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_embedding | -0.061 | -0.059 | -0.053 |
| chat_preference | wo_decay | -0.167 | -0.307 | -0.474 |
| chat_preference | wo_role_matrix | -0.456 | -0.490 | -0.474 |
| chat_preference | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| chat_preference | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_embedding | -0.100 | -0.113 | +0.100 |
| chat_profile | wo_decay | -0.100 | -0.103 | +0.000 |
| chat_profile | wo_role_matrix | -0.400 | -0.257 | +0.000 |
| chat_profile | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| chat_profile | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| mixed | wo_embedding | +0.183 | +0.228 | +0.400 |
| mixed | wo_decay | +0.071 | +0.031 | +0.000 |
| mixed | wo_role_matrix | +0.088 | +0.015 | +0.000 |
| mixed | wo_domain_gate | +0.000 | -0.003 | +0.000 |
| mixed | wo_tmt_condition | -0.012 | -0.008 | +0.000 |
| mixed | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| negative | wo_embedding | +0.000 | +0.000 | +0.000 |
| negative | wo_decay | +0.000 | +0.000 | +0.000 |
| negative | wo_role_matrix | +0.000 | +0.000 | +0.000 |
| negative | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| negative | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| negative | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_context | wo_embedding | +0.064 | +0.160 | +0.346 |
| task_context | wo_decay | -0.115 | -0.171 | -0.269 |
| task_context | wo_role_matrix | -0.372 | -0.321 | -0.154 |
| task_context | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| task_context | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_context | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_embedding | +0.033 | +0.038 | +0.050 |
| task_dependency | wo_decay | +0.050 | +0.040 | +0.000 |
| task_dependency | wo_role_matrix | -0.050 | -0.259 | -0.600 |
| task_dependency | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_dependency | wo_eisenhower | +0.000 | +0.000 | +0.000 |
| task_due | wo_embedding | -0.022 | -0.039 | +0.000 |
| task_due | wo_decay | +0.000 | -0.002 | +0.000 |
| task_due | wo_role_matrix | -0.122 | -0.358 | -0.867 |
| task_due | wo_domain_gate | +0.000 | -0.009 | +0.000 |
| task_due | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_due | wo_eisenhower | -0.100 | -0.038 | +0.000 |
| task_priority | wo_embedding | +0.078 | +0.042 | +0.033 |
| task_priority | wo_decay | +0.000 | +0.000 | +0.000 |
| task_priority | wo_role_matrix | -0.122 | -0.194 | -0.367 |
| task_priority | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| task_priority | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_priority | wo_eisenhower | +0.100 | -0.030 | -0.367 |
| task_status | wo_embedding | -0.075 | -0.039 | +0.000 |
| task_status | wo_decay | +0.083 | +0.047 | +0.000 |
| task_status | wo_role_matrix | -0.325 | -0.178 | +0.000 |
| task_status | wo_domain_gate | +0.000 | +0.000 | +0.000 |
| task_status | wo_tmt_condition | +0.000 | +0.000 | +0.000 |
| task_status | wo_eisenhower | +0.100 | +0.081 | +0.000 |

## 8. Hard Case Results: top_k=5

| hard_case_tag | ablation | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | completed_error | todo_intrusion | wrong_domain_intrusion | stale_intrusion | far_before_near |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adversarial_completed_todo_v2 | full_core_v2 | 0.688 | 0.871 | 1.000 | 1.000 | 0.375 | 0.000 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_embedding | 0.688 | 0.891 | 1.000 | 1.000 | 0.375 | 0.188 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_decay | 0.688 | 0.871 | 1.000 | 1.000 | 0.375 | 0.000 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_role_matrix | 1.000 | 0.659 | 0.000 | 1.000 | 1.000 | 0.396 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_domain_gate | 0.688 | 0.871 | 1.000 | 1.000 | 0.375 | 0.000 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_tmt_condition | 0.688 | 0.871 | 1.000 | 1.000 | 0.375 | 0.000 | - | 0.000 | - | 0.000 |
| adversarial_completed_todo_v2 | wo_eisenhower | 0.688 | 0.871 | 1.000 | 1.000 | 0.375 | 0.000 | - | 0.000 | - | 0.000 |
| compatibility_chat_intrusion | full_core_v2 | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_embedding | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_decay | 0.500 | 0.237 | 0.000 | - | 0.500 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_role_matrix | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.600 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_domain_gate | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_tmt_condition | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| compatibility_chat_intrusion | wo_eisenhower | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_plan | full_core_v2 | 1.000 | 0.626 | 0.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_embedding | 1.000 | 0.939 | 1.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_decay | 0.500 | 0.182 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_role_matrix | 0.500 | 0.272 | 0.000 | - | 0.500 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_domain_gate | 1.000 | 0.626 | 0.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_tmt_condition | 1.000 | 0.626 | 0.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_plan | wo_eisenhower | 1.000 | 0.626 | 0.000 | - | 1.000 | - | - | 0.000 | 0.000 | - |
| decay_current_preference | full_core_v2 | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 | - | 0.000 | - |
| decay_current_preference | wo_embedding | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.000 | - | 0.000 | - |
| decay_current_preference | wo_decay | 0.500 | 0.303 | 0.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| decay_current_preference | wo_role_matrix | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.600 | - | 0.000 | - |
| decay_current_preference | wo_domain_gate | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 | - | 0.000 | - |
| decay_current_preference | wo_tmt_condition | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 | - | 0.000 | - |
| decay_current_preference | wo_eisenhower | 1.000 | 1.000 | 1.000 | - | 1.000 | - | 0.200 | - | 0.000 | - |
| domain_wrong_urgent | full_core_v2 | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_embedding | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_decay | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_role_matrix | 0.500 | 0.521 | 0.000 | 0.500 | - | 0.500 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_domain_gate | 1.000 | 0.964 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_tmt_condition | 1.000 | 1.000 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| domain_wrong_urgent | wo_eisenhower | 0.500 | 0.826 | 1.000 | 0.500 | - | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | full_core_v2 | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_embedding | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_decay | 1.000 | 0.885 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_role_matrix | 1.000 | 0.679 | 0.000 | 1.000 | 1.000 | 0.500 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_domain_gate | 1.000 | 0.885 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_tmt_condition | 1.000 | 0.906 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_completed_task | wo_eisenhower | 1.000 | 0.939 | 1.000 | 1.000 | 1.000 | 0.000 | - | 0.000 | - | 0.000 |
| penalty_old_preference | full_core_v2 | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| penalty_old_preference | wo_embedding | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| penalty_old_preference | wo_decay | 0.500 | 0.356 | 0.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| penalty_old_preference | wo_role_matrix | 0.000 | 0.000 | 0.000 | - | 0.000 | - | 0.600 | - | 0.000 | - |
| penalty_old_preference | wo_domain_gate | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| penalty_old_preference | wo_tmt_condition | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| penalty_old_preference | wo_eisenhower | 0.500 | 0.826 | 1.000 | - | 0.500 | - | 0.200 | - | 0.000 | - |
| tmt_deadline_order | full_core_v2 | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_embedding | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_decay | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_role_matrix | 0.500 | 0.444 | 0.000 | 1.000 | 0.000 | 0.500 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_domain_gate | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_tmt_condition | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_deadline_order | wo_eisenhower | 0.500 | 0.704 | 1.000 | 1.000 | 0.000 | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | full_core_v2 | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_embedding | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_decay | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_role_matrix | 0.500 | 0.444 | 0.000 | 0.500 | - | 0.500 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_domain_gate | 1.000 | 0.906 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_tmt_condition | 1.000 | 0.939 | 1.000 | 1.000 | - | 0.000 | - | 0.000 | - | 0.000 |
| tmt_far_distractor | wo_eisenhower | 0.500 | 0.704 | 1.000 | 0.500 | - | 0.000 | - | 0.000 | - | 0.000 |

## 9. Component Contribution Analysis

- `wo_embedding`: top_k=5 下 memory_recall 变化为 +0.003，memory_NDCG 变化为 +0.013。
- `wo_decay`: top_k=5 下 non_todo_recall 变化为 -0.010；chat_history recall 变化为 +0.000，chat_preference recall 变化为 -0.167。
- `wo_role_matrix`: top_k=5 下 todo_intrusion_rate 变化为 +0.348，active_todo_precision 变化为 -0.526。
- `wo_domain_gate`: top_k=5 下 wrong_domain_urgent_intrusion_rate 变化为 +0.000。
- `wo_tmt_condition`: top_k=5 下 task_context recall 变化为 +0.000。
- `wo_eisenhower`: top_k=5 下 deadline_ranking_accuracy 变化为 +0.000，far_deadline_before_near_rate 变化为 +0.000。

## 10. 结论

本报告应优先按两层阅读：overall 用来观察全局平均性能，hard_case_tag 分组用来判断组件是否在对应困难场景中产生独立贡献。由于 bounded similarity、role matrix、domain gate、conditional TMT 和 Eisenhower 的作用域不同，单一 overall 均值可能会稀释特定组件的贡献。

当前版本已将主方法改为 `Sim × IntentGate × DomainGate × Accessibility`。其中 Sim 有 embedding/floor 兜底，IntentGate 是角色级矩阵，DomainGate 负责软硬结合的跨域隔离，TMT 只在任务调度型 query 下生效。