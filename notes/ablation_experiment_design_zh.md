# MU-Level Ablation 实验设计

## 1. 实验目标

当前主实验已经显示升级后的 proposed_QCA 在 Pilot v2 的 MU-level retrieval 上明显优于 similarity-only。消融实验的目标是回答：

```text
QCA 为什么有效？
到底是 TMT、decay、compatibility、domain match、penalty，还是它们的组合带来了提升？
```

消融实验应以 MU-level 为主，Event-level 为辅。因为本文的核心设定是：

```text
Event 是容器；
MU 是真正的状态实体；
TMT 激活、遗忘衰减、accessible_score 和四象限流转都发生在 MU 层。
```

## 2. 当前 Full QCA 公式

当前 proposed_QCA 采用统一公式：

```text
Score(q, m, t) =
w_s(q) · Sim(q, m)
+ w_a(q) · Acc(m, t)
+ w_c(q) · Compat(q, m)
+ w_d(q) · Domain(q, m)
+ w_b(q) · Base(m)
- Penalty(q, m)
```

其中：

```text
Sim(q, m): query 与 MU content 的语义相关性

Acc(m, t):
  TMT(m, t), if m is todo
  Decay(m, t), otherwise

Compat(q, m): query intent 与 memory_type 的兼容性

Domain(q, m): query 与 MU/Event 所属任务域或实体的匹配程度

Base(m): importance 与 accessible_score 的基础组合

Penalty(q, m): 已完成任务、任务域不匹配、旧偏好等惩罚项
```

Event 层仍然只作为容器：

```text
Score(q, e, t) =
SmoothMax({ Score(q, m_i, t) | m_i in e })
```

## 3. Ablation Variants

第一版消融建议做 6 组：

| ablation 名称 | 改动 | 目的 |
|---|---|---|
| `full_qca` | 完整方法 | 作为主方法 |
| `wo_tmt` | todo 的 `Acc(m,t)` 不使用 TMT，改为 `accessible_score` | 验证 TMT 对 task_due / todo_recall 的贡献 |
| `wo_decay` | non-todo 的 `Acc(m,t)` 不使用 forgetting decay，改为 `accessible_score` | 验证 decay 对 non-todo / chat memory 的贡献 |
| `wo_compatibility` | `Compat(q,m)=0` | 验证 intent-memory type compatibility 的贡献 |
| `wo_domain` | `Domain(q,m)=0` | 验证任务域/实体匹配的贡献 |
| `wo_penalty` | `Penalty(q,m)=0` | 验证 done/domain mismatch/old preference penalty 的贡献 |

暂时不做 `flat_qca`。原因是当前 MU-level ranking 本身就是全库 MU 排序，如果要严谨比较 Event 容器作用，需要另设 event-first context packing 实验。第一版消融先聚焦 QCA 公式内部组件。

## 4. 每个消融的实现方式

### 4.1 full_qca

保留当前公式全部项：

```text
semantic + accessibility + compatibility + domain + base - penalty
```

### 4.2 wo_tmt

仅修改 todo 的 accessibility：

```text
if memory_type == "todo":
    Acc(m, t) = accessible_score
else:
    Acc(m, t) = Decay(m, t)
```

预期影响：

```text
task_due 下降
todo_recall 下降
deadline 相关表现下降
```

### 4.3 wo_decay

仅修改 non-todo 的 accessibility：

```text
if memory_type == "todo":
    Acc(m, t) = TMT(m, t)
else:
    Acc(m, t) = accessible_score
```

预期影响：

```text
chat_preference 下降
non_todo_recall 下降
旧无关 non-todo 更容易进入 context
```

### 4.4 wo_compatibility

移除 query intent 与 memory type 的兼容性项：

```text
Compat(q, m) = 0
```

预期影响：

```text
chat_preference/chat_profile 下降
todo_intrusion_rate 上升
task_status/task_dependency 下降
```

### 4.5 wo_domain

移除任务域/实体匹配项：

```text
Domain(q, m) = 0
```

预期影响：

```text
task_context 下降
task_status 下降
mixed 下降
urgent_wrong_domain 更容易进入结果
```

### 4.6 wo_penalty

移除惩罚项：

```text
Penalty(q, m) = 0
```

预期影响：

```text
completed_task_error_rate 上升
todo_intrusion_rate 上升
旧偏好或错误任务域更容易被召回
```

## 5. 指标

主指标使用 MU-level：

```text
memory_recall@k
memory_NDCG@k
memory_top1_accuracy
todo_recall@k
non_todo_recall@k
completed_task_error_rate
todo_intrusion_rate
deadline_ranking_accuracy
memory_token_cost
```

辅助指标可使用 Event-level：

```text
supporting_event_recall@k
event_NDCG@k
event token_cost
```

第一版优先实现 MU-level ablation。

## 6. top_k 设置

建议先跑：

```text
top_k = 5
top_k = 10
```

报告主表使用 `top_k=5`，`top_k=10` 作为补充。

原因：

```text
top_k=1 过于苛刻，容易受单条排序波动影响；
top_k=10 更接近真实 context packing；
top_k=5 是较好的诊断设置。
```

## 7. 输出文件

建议新增：

```text
event_memory_experiment/run_ablation_experiment.py
event_memory_experiment/results_pilot_v2_ablation_memory_topk.csv
event_memory_experiment/evaluation_report_pilot_v2_ablation_zh.md
```

CSV 字段建议：

```text
top_k
ablation
user_id
query_id
query_mode
query_subtype
query
selected_memory_ids
selected_event_ids
selected_memory_types
selected_memory_scores
gold_memory_ids
gold_event_ids
memory_recall
memory_NDCG
memory_top1_accuracy
todo_recall
non_todo_recall
completed_task_error_rate
todo_intrusion_rate
deadline_ranking_accuracy
memory_token_cost
```

## 8. 报告结构

中文报告建议结构：

```text
1. 实验目标
2. Ablation variants
3. Overall results
4. By query mode
5. By query subtype
6. Component contribution analysis
7. 结论与下一步
```

## 9. 预期结果与解释方式

如果结果符合预期，可以这样解释：

```text
TMT:
主要贡献 task_due、todo_recall、deadline-sensitive retrieval。

Decay:
主要贡献 non-todo recall 和旧记忆过滤。

Compatibility:
主要贡献 intent-memory type 对齐，降低 todo intrusion。

Domain:
主要贡献任务域约束，避免近 ddl 但错误 domain 的任务被召回。

Penalty:
主要贡献错误召回控制，例如 completed task 和 old preference。
```

如果某个 ablation 没有明显下降，也不一定是坏事。可能说明：

```text
1. 该组件与其他组件功能重叠；
2. 当前 Pilot v2 数据没有充分覆盖该组件负责的困难样本；
3. 该组件权重过低，需要重新检查公式；
4. 指标没有直接测到该组件的贡献。
```

## 10. 下一轮对话继续方式

如果新开对话，可以直接说：

```text
根据 E:\MyDatum\小论文\Codex\notes\ablation_experiment_design_zh.md，
在当前 event_memory_experiment 代码基础上实现 MU-level ablation 实验。
```

