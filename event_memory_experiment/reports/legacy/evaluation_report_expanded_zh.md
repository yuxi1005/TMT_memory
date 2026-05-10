# 扩展 Toy Dataset 实验评估

## 实验设置

- 数据集：5 个 synthetic users。
- 每个用户：8 个 events，其中原始 3 个是 gold-relevant 主事件，新增 5 个 distractor events。
- 总规模：40 events，135 memories，20 queries。
- 方法：
  - `recency_only`
  - `similarity_only`
  - `recency_similarity_hybrid`
  - `proposed_TMT_decay_event_memory`
- 同时评估：`top_k = 1, 2, 3`。

## 总体结果

| top_k | method | supporting_event_recall | top1_accuracy | NDCG@3 | LLM can answer | avg token cost |
|---:|---|---:|---:|---:|---:|---:|
| 1 | recency_only | 0.492 | 0.850 | 0.587 | 0.150 | 100.4 |
| 1 | similarity_only | 0.467 | 0.800 | 0.577 | 0.150 | 98.5 |
| 1 | recency_similarity_hybrid | 0.492 | 0.850 | 0.587 | 0.150 | 100.4 |
| 1 | proposed_TMT_decay_event_memory | 0.492 | 0.850 | 0.575 | 0.150 | 102.0 |
| 2 | recency_only | 0.833 | 0.850 | 0.816 | 0.700 | 196.6 |
| 2 | similarity_only | 0.808 | 0.800 | 0.800 | 0.650 | 193.5 |
| 2 | recency_similarity_hybrid | 0.833 | 0.850 | 0.816 | 0.700 | 196.6 |
| 2 | proposed_TMT_decay_event_memory | 0.808 | 0.850 | 0.802 | 0.700 | 197.5 |
| 3 | recency_only | 0.925 | 0.850 | 0.871 | 0.850 | 269.0 |
| 3 | similarity_only | 1.000 | 0.800 | 0.907 | 1.000 | 292.7 |
| 3 | recency_similarity_hybrid | 0.925 | 0.850 | 0.871 | 0.850 | 269.0 |
| 3 | proposed_TMT_decay_event_memory | 1.000 | 0.850 | 0.908 | 1.000 | 295.2 |

## 按 Query Mode 分析

### top_k = 2

| query_mode | method | supporting_event_recall | NDCG@3 | LLM can answer |
|---|---|---:|---:|---:|
| task | recency_only | 0.950 | 0.897 | 0.900 |
| task | similarity_only | 0.850 | 0.806 | 0.700 |
| task | recency_similarity_hybrid | 0.950 | 0.897 | 0.900 |
| task | proposed_TMT_decay_event_memory | 0.750 | 0.770 | 0.700 |
| chat | recency_only | 0.717 | 0.736 | 0.500 |
| chat | similarity_only | 0.767 | 0.795 | 0.600 |
| chat | recency_similarity_hybrid | 0.717 | 0.736 | 0.500 |
| chat | proposed_TMT_decay_event_memory | 0.867 | 0.834 | 0.700 |

## 主要观察

1. 加入 distractor events 后，`top_k=3` 不再完全饱和，实验比原始 toy dataset 更有诊断意义。

2. `proposed_TMT_decay_event_memory` 在 `chat/mixed` query 上表现最好。尤其在 `top_k=2` 时，它的 supporting event recall 达到 `0.867`，高于 similarity-only 的 `0.767` 和 recency-only 的 `0.717`。这说明 TMT + decay + event-memory 的组合确实更容易保留偏好、习惯、事实类事件。

3. `proposed_TMT_decay_event_memory` 在 task query 上暂时不如 recency/hybrid。主要问题是：当前 TMT 激活会把“有近 ddl 或过期 todo 的事件”推高，即使 query 指向的是另一个任务域或 task_status 场景。这说明 proposed method 还缺少 query-domain gate 和 task-status gate。

4. `recency_only` 和 `recency_similarity_hybrid` 在 task query 上表现强，是因为当前 synthetic dataset 中很多任务事件本身也较新。后续数据集需要加入更多“最近但无关”的任务干扰事件，否则 recency baseline 会过强。

5. `similarity_only` 在 `top_k=3` 的整体 recall 达到 `1.000`，但这不应被过度解释。当前 similarity 是词面 overlap，不是真实 embedding；同时 event theme 仍然较清晰，正式实验中需要替换成 embedding similarity。

## 当前结论

这一版扩展实验可以支持一个更谨慎的结论：

> Proposed method 在 mixed/chat 类型记忆检索中已经显示出优势，尤其是需要同时召回偏好、习惯、事实和任务背景时；但在纯 task query 中，当前 TMT 激活项过强，容易压过 query 的任务域约束。

因此，下一步不是继续扩大数据，而是先修正 proposed selector：

1. 增加 `query_subtype` gate：
   - `task_due`：提高 ddl / TMT 权重。
   - `task_status`：提高 is_done / unfinished matching 权重。
   - `task_context`：提高 semantic / event_text 权重。
   - `mixed`：保留 todo 和 non-todo 双通道。

2. 增加 task domain / entity matching：
   - 如果 query 指向“portfolio / hospital / vendor / launch”等域，TMT 不能把其他域的近 ddl task 强行推到前面。

3. 正式实验中应报告 `top_k=1,2,3`，并把 `top_k=2` 作为主要诊断设置，因为它足够紧张，也不会像 top1 那样过于苛刻。

