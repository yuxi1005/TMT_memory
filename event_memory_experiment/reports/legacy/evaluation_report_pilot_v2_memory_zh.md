# Pilot v2 MU-Level 实验报告

## 1. 实验目的

此前实验主要评估 Event-level retrieval，即 selector 是否能选中包含 gold memory 的事件。但本文方法的核心假设是：

```text
Event 是容器；
MU 才是真正的记忆状态实体；
TMT 激活、遗忘衰减、accessible_score 和四象限流转都发生在 MU 层。
```

因此，本次实验新增 MU-level retrieval and evaluation，直接评估方法是否能选中正确的 memory units。

## 2. 实验设置

数据集：

```text
pilot_v2_dataset.jsonl
users = 10
events = 200
memories = 800
queries = 200
```

方法：

```text
recency_only
similarity_only
recency_similarity_hybrid
proposed_TMT_decay_event_memory
```

Memory-level top_k：

```text
1, 3, 5, 10
```

## 3. 指标

本次新增指标：

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

其中：

```text
completed_task_error_rate:
在 task_due/task_priority 中，已完成 todo 被错误选入的比例。

todo_intrusion_rate:
在 chat_preference/chat_profile/chat_history 中，todo 记忆错误进入 context 的比例。

deadline_ranking_accuracy:
在 task_due/task_priority 中，首个被选中的 todo 是否是 gold 中最早 ddl 的未完成 todo。
```

## 4. 主要结果

### top_k = 5

| method | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | todo_intrusion | token_cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| similarity_only | 0.259 | 0.215 | 0.095 | 0.160 | 0.260 | 0.360 | 58.3 |
| proposed_QCA | 0.598 | 0.610 | 0.615 | 0.526 | 0.565 | 0.000 | 79.8 |

### top_k = 10

| method | memory_recall | memory_NDCG | top1_acc | todo_recall | non_todo_recall | todo_intrusion | token_cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| similarity_only | 0.574 | 0.348 | 0.095 | 0.524 | 0.566 | 0.410 | 134.3 |
| proposed_QCA | 0.807 | 0.689 | 0.615 | 0.897 | 0.656 | 0.000 | 157.7 |

## 5. 关键观察

### 5.1 MU-level 上 proposed 显著优于 similarity-only

在 `top_k=5`：

```text
memory_recall: 0.259 -> 0.598
memory_NDCG: 0.215 -> 0.610
top1_accuracy: 0.095 -> 0.615
todo_recall: 0.160 -> 0.526
non_todo_recall: 0.260 -> 0.565
```

这说明 query-conditioned accessibility 不只是选对 Event，也能更直接地选中正确 MU。

### 5.2 QCA 明显降低 chat 场景下的 todo intrusion

在 `chat_preference/chat_profile/chat_history` 中：

```text
similarity_only top_k=5 todo_intrusion_rate = 0.360
proposed_QCA top_k=5 todo_intrusion_rate = 0.000
```

这对论文很重要，因为它说明 proposed method 能根据 intent 抑制不应进入闲聊 context 的 todo 记忆。

### 5.3 Task 和 Chat 两类 query 都有提升

`top_k=5`：

| query_mode | method | memory_recall | memory_NDCG | top1_acc |
|---|---|---:|---:|---:|
| chat | similarity_only | 0.368 | 0.349 | 0.257 |
| chat | proposed_QCA | 0.670 | 0.718 | 0.729 |
| task | similarity_only | 0.200 | 0.143 | 0.008 |
| task | proposed_QCA | 0.559 | 0.551 | 0.554 |

这说明提升不是只来自某一类 query。

## 6. Query Subtype 结果

`top_k=5` 下 proposed_QCA：

| subtype | memory_recall | memory_NDCG | top1_acc |
|---|---:|---:|---:|
| chat_history | 0.667 | 0.641 | 0.900 |
| chat_preference | 0.500 | 0.523 | 0.600 |
| chat_profile | 0.500 | 0.704 | 1.000 |
| mixed | 0.763 | 0.817 | 1.000 |
| negative | 1.000 | 1.000 | 0.000 |
| task_context | 0.483 | 0.520 | 0.550 |
| task_dependency | 0.767 | 0.795 | 1.000 |
| task_due | 0.667 | 0.658 | 0.550 |
| task_priority | 0.422 | 0.420 | 0.333 |
| task_status | 0.542 | 0.491 | 0.500 |

较强的 subtype：

```text
mixed
task_dependency
task_due
chat_history
chat_profile
```

仍需改进的 subtype：

```text
task_priority
task_context
task_status
chat_preference
```

## 7. 暴露的问题

### 7.1 deadline_ranking_accuracy 仍然为 0

虽然 QCA 能召回大量 todo gold memories，但在 `task_due/task_priority` 中，它尚未把最早 ddl 的 gold todo 排为第一个 todo。

这说明：

```text
TMT 激活有助于召回 todo，
但当前公式还不能精确建模 deadline ordering。
```

下一步可以单独优化 todo 内部排序，而不是继续大幅改动统一公式。

### 7.2 QCA 的 token cost 略高

`top_k=5`：

```text
similarity_only token_cost = 58.3
proposed_QCA token_cost = 79.8
```

这是可接受的，因为 QCA 的 recall/NDCG 提升明显。但正式实验中应报告：

```text
recall per token
NDCG per token
```

### 7.3 当前 similarity 仍是 lexical overlap

当前 semantic similarity 仍是词面 overlap。正式实验需要替换为 embedding similarity，否则 similarity-only 的强弱都可能受 synthetic wording 影响。

## 8. 结论

MU-level 实验比 Event-level 更能支持本文核心假设。

当前结果表明：

```text
1. proposed_QCA 能显著提升 memory-level recall 和 NDCG。
2. proposed_QCA 能同时提升 todo 和 non-todo recall。
3. proposed_QCA 能有效降低 chat query 中的 todo intrusion。
4. Event 作为容器、MU 作为状态实体的设计在实验上是可验证的。
```

这一步已经补上了此前 event-level 实验的主要缺口。下一步建议做 ablation：

```text
w/o TMT
w/o decay
w/o compatibility
w/o domain match
w/o penalty
```

