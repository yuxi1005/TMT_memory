# Pilot v2 升级公式实验报告

## 1. 方法更新

本次将 proposed selector 从原来的粗粒度 `TASK/CHAT` 权重公式，升级为统一的 query-conditioned accessibility 公式：

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
Acc(m, t) = TMT(m, t), if m is todo
Acc(m, t) = Decay(m, t), otherwise
```

Event 仍然只是容器：

```text
Score(q, e, t) =
SmoothMax({ Score(q, m_i, t) | m_i in e })
```

这保持了公式统一性，没有为每个 query subtype 写独立公式，只通过少量 query-conditioned gates 和 type compatibility matrix 调整不同项的贡献。

## 2. 总体结果对比

### top_k = 3

| method | supporting_event_recall | top1_accuracy | NDCG@3 | LLM can answer | avg token cost |
|---|---:|---:|---:|---:|---:|
| recency_only | 0.175 | 0.100 | 0.154 | 0.050 | 251.7 |
| similarity_only | 0.634 | 0.695 | 0.643 | 0.350 | 225.1 |
| recency_similarity_hybrid | 0.211 | 0.300 | 0.220 | 0.050 | 248.4 |
| proposed_QCA | 0.708 | 0.660 | 0.710 | 0.450 | 225.1 |

升级后 proposed 已经超过 similarity-only：

```text
supporting_event_recall: 0.634 -> 0.708
NDCG@3: 0.643 -> 0.710
LLM can answer: 0.350 -> 0.450
```

相比旧 proposed：

```text
supporting_event_recall: 0.317 -> 0.708
NDCG@3: 0.254 -> 0.710
LLM can answer: 0.150 -> 0.450
```

## 3. top_k 效果

| top_k | proposed recall | similarity recall | proposed NDCG@3 | similarity NDCG@3 |
|---:|---:|---:|---:|---:|
| 1 | 0.366 | 0.374 | 0.459 | 0.465 |
| 2 | 0.594 | 0.502 | 0.643 | 0.572 |
| 3 | 0.708 | 0.634 | 0.710 | 0.643 |

解释：

```text
top_k=1 时 similarity-only 仍略强，因为 query 和 gold event 的词面/语义线索较直接。
top_k=2/3 时 proposed 明显更强，说明 accessibility + compatibility 有助于补齐多证据 context。
```

## 4. 各 Query Subtype 改善情况

### 旧 proposed vs 升级 proposed，top_k = 3

| subtype | old recall | new recall | old NDCG@3 | new NDCG@3 |
|---|---:|---:|---:|---:|
| chat_history | 0.500 | 1.000 | 0.387 | 0.976 |
| chat_preference | 0.000 | 0.500 | 0.000 | 0.567 |
| chat_profile | 0.000 | 0.500 | 0.000 | 0.704 |
| mixed | 0.667 | 0.750 | 0.655 | 0.822 |
| negative | 1.000 | 1.000 | 1.000 | 1.000 |
| task_context | 0.000 | 1.000 | 0.000 | 0.767 |
| task_dependency | 0.417 | 0.833 | 0.344 | 0.905 |
| task_due | 0.417 | 0.667 | 0.281 | 0.650 |
| task_priority | 0.000 | 0.333 | 0.000 | 0.409 |
| task_status | 0.458 | 0.792 | 0.286 | 0.719 |

升级公式显著修复了旧 proposed 的主要短板：

```text
chat_preference 不再为 0
chat_profile 不再为 0
task_context 从 0 提升到 1.0
task_status 从 0.458 提升到 0.792
task_dependency 从 0.417 提升到 0.833
```

## 5. 当前结论

升级后的 proposed selector 更符合论文方法设定：

```text
1. Event 仍是容器，不引入 event_value/event_status。
2. MU 是真正的评分与状态流转实体。
3. 公式保持统一，没有堆叠多个 subtype-specific 公式。
4. Query intent 通过少量 gate 调节 semantic、accessibility、compatibility 和 domain match。
```

当前 Pilot v2 结果已经可以支持一个较稳的实验结论：

> Query-conditioned accessibility ranking can outperform similarity-only event retrieval under constrained context budgets, especially when queries require task status, dependency, preference, and mixed memory evidence.

## 6. 后续仍需注意

当前结果仍然是 event-level。下一步应补充 MU-level retrieval 评估：

```text
memory_recall@k
memory_NDCG@k
todo_recall@k
non_todo_recall@k
completed_task_error_rate
todo_intrusion_rate
deadline_ranking_accuracy
```

此外，当前 similarity 仍是词面 overlap。正式实验应替换为 embedding similarity，避免审稿人认为结果依赖 synthetic lexical pattern。

