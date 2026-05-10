# Pilot v2 Event-Level 实验评估报告

## 1. 实验设置

本次实验使用 `pilot_v2_dataset.jsonl`：

```text
users = 10
events = 200
memories = 800
queries = 200
```

新版 schema 中，Event 只作为容器存在，不包含 `event_value` 和 `event_status`。Event 分数完全由内部 MU 的分数通过 smooth-max 动态聚合得到。

实验方法：

```text
recency_only
similarity_only
recency_similarity_hybrid
proposed_TMT_decay_event_memory
```

同时评估：

```text
top_k = 1, 2, 3
```

## 2. 总体结果

| top_k | method | supporting_event_recall | top1_accuracy | NDCG@3 | LLM can answer | avg token cost |
|---:|---|---:|---:|---:|---:|---:|
| 1 | recency_only | 0.092 | 0.100 | 0.099 | 0.050 | 91.8 |
| 1 | similarity_only | 0.374 | 0.695 | 0.465 | 0.100 | 76.8 |
| 1 | recency_similarity_hybrid | 0.167 | 0.300 | 0.196 | 0.050 | 84.3 |
| 1 | proposed_TMT_decay_event_memory | 0.101 | 0.135 | 0.112 | 0.050 | 86.6 |
| 2 | recency_only | 0.158 | 0.100 | 0.148 | 0.050 | 174.8 |
| 2 | similarity_only | 0.502 | 0.695 | 0.572 | 0.175 | 149.2 |
| 2 | recency_similarity_hybrid | 0.211 | 0.300 | 0.220 | 0.050 | 166.5 |
| 2 | proposed_TMT_decay_event_memory | 0.213 | 0.135 | 0.188 | 0.110 | 173.7 |
| 3 | recency_only | 0.175 | 0.100 | 0.154 | 0.050 | 251.7 |
| 3 | similarity_only | 0.634 | 0.695 | 0.643 | 0.350 | 225.1 |
| 3 | recency_similarity_hybrid | 0.211 | 0.300 | 0.220 | 0.050 | 248.4 |
| 3 | proposed_TMT_decay_event_memory | 0.317 | 0.135 | 0.254 | 0.150 | 247.5 |

## 3. 按 Query Mode 分析

### top_k = 3

| query_mode | method | supporting_event_recall | NDCG@3 | LLM can answer |
|---|---|---:|---:|---:|
| chat | recency_only | 0.333 | 0.326 | 0.143 |
| chat | similarity_only | 0.681 | 0.738 | 0.443 |
| chat | recency_similarity_hybrid | 0.340 | 0.398 | 0.143 |
| chat | proposed_TMT_decay_event_memory | 0.405 | 0.385 | 0.286 |
| task | recency_only | 0.090 | 0.061 | 0.000 |
| task | similarity_only | 0.609 | 0.591 | 0.300 |
| task | recency_similarity_hybrid | 0.141 | 0.124 | 0.000 |
| task | proposed_TMT_decay_event_memory | 0.269 | 0.184 | 0.077 |

## 4. 关键子类型结果

在 `top_k=3` 下：

| query_subtype | proposed recall | similarity recall | 观察 |
|---|---:|---:|---|
| `task_due` | 0.417 | 0.242 | proposed 对近 ddl 任务有优势 |
| `task_status` | 0.458 | 0.792 | proposed 仍然不足，状态匹配弱 |
| `task_priority` | 0.000 | 0.556 | proposed 没有正确利用 task priority/query domain |
| `task_context` | 0.000 | 0.750 | proposed 缺少 context/semantic gate |
| `task_dependency` | 0.417 | 0.550 | proposed 有部分依赖信号，但仍弱于 similarity |
| `chat_preference` | 0.000 | 0.750 | proposed 没有把 preference 类型显式推高 |
| `chat_profile` | 0.000 | 0.100 | profile query 仍未处理好 |
| `mixed` | 0.667 | 0.833 | proposed 在 mixed 场景有一定效果 |

## 5. 与 Toy 实验对比

Toy expanded dataset：

```text
users = 5
events = 40
memories = 135
queries = 20
```

Toy 中每个 user 只有 8 个 events，distractor 较少，部分指标容易偏高。Pilot v2 扩展到每个 user 20 个 events 后，数据难度明显提高。

对比现象：

```text
1. recency_only 在 toy 中仍有一定表现，但在 Pilot v2 中几乎失效。
2. top_k=3 不再接近饱和，说明 Pilot v2 的事件数量和 distractor 数量更合理。
3. similarity_only 在 Pilot v2 中变成最强 baseline，说明 query 与 gold event/MU 的语义或词面线索仍然较直接。
4. proposed 在 toy 的 chat/mixed 中曾显示优势，但在 Pilot v2 中只在 task_due 和 mixed 上保留部分信号。
```

## 6. 当前结论

Pilot v2 数据比 toy 数据明显更适合正式实验。它已经能够区分方法优劣，也能暴露 proposed method 的真实缺陷。

当前结果不能支持 “proposed 全面优于 baseline”。更准确的结论是：

```text
1. Pilot v2 难度足够让 recency baseline 失效。
2. similarity-only 目前是最强 baseline。
3. proposed method 在 task_due 上体现了 TMT 激活的有效性。
4. proposed method 在 mixed query 上有部分效果。
5. proposed method 在 task_status、task_context、chat_preference、chat_profile 上明显不足。
```

## 7. 暴露的问题

### 7.1 Proposed 还没有真正实现 query subtype gate

当前 proposed 只粗略区分 `task` 和 `chat`，没有区分：

```text
task_due
task_priority
task_status
task_context
task_dependency
chat_preference
chat_profile
mixed
```

因此它无法针对不同 query 选择不同 MU 类型和不同排序权重。

### 7.2 TMT 激活有用，但覆盖面窄

`task_due` 中 proposed recall 高于 similarity-only，说明 deadline/TMT 信号是有效的。但 TMT 不能解决：

```text
任务状态
任务背景
用户偏好
profile 信息
旧偏好被新偏好覆盖
```

### 7.3 数据仍然偏向 similarity baseline

Pilot v2 中很多 query 直接包含任务域名称，例如：

```text
课程项目汇报
beta 发布
客户封面稿
排班行政
```

这会让 similarity-only 很强。正式实验中需要加入更多语义改写和隐式 query，例如：

```text
不要直接说任务域
使用代词或上下文指代
用中文 query 匹配英文 memory
加入语义相似但错误状态的 hard negative
```

## 8. 下一步建议

下一步不应继续扩大数据，而应先修 proposed selector：

```text
1. 加入 query_subtype gate
2. 加入 MU-level ranking 和 memory-level metrics
3. 对 task_status 显式使用 is_done/status_update
4. 对 chat_preference 显式提高 preference/habit/profile 权重
5. 对 task_context 显式提高 semantic/event_text/dependency 权重
6. 对 mixed query 采用 todo 与 non-todo 双通道召回
```

修完后重新跑 Pilot v2。如果 proposed 在以下指标上提升，才说明方法开始成型：

```text
task_due: proposed > similarity-only
mixed: proposed 接近或超过 similarity-only
chat_preference: proposed 明显提升
task_status: completed_task_error_rate 降低
overall: 在相近 token cost 下提高 NDCG@3 或 memory_NDCG@k
```

