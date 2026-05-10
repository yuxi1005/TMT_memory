# Event 与 Memory Unit 字段设计说明

## 1. 总体设计原则

本机制采用 Event-Memory 双层结构：

```text
Event: 一段连续交互或任务讨论形成的上下文单元
Memory Unit, MU: 从 Event 中抽取出的原子记忆
```

Event 负责提供对话块级别的上下文召回，MU 负责提供可排序、可衰减、可激活的具体记忆证据。

字段设计遵循三个原则：

```text
1. 支持检索：能用于 event retrieval 和 memory ranking
2. 支持动态可访问性：能计算 accessible_score、TMT 激活和遗忘衰减
3. 支持实验评估：能和 gold label、query subtype、baseline 指标对应
```

不是每个字段在最小 demo 中都必须使用，但正式实验中大多字段都有明确作用。

## 2. Memory Unit 字段说明

| 字段 | 是否必要 | 作用 | 说明 |
|---|---|---|---|
| `memory_id` | 必要 | 唯一标识 MU | 用于 gold label、检索结果、评估指标和去重 |
| `content` | 必要 | 记忆文本内容 | 可直接进入 LLM context，也是 semantic retrieval 的主要文本 |
| `timestamp` | 必要 | 记忆产生时间 | 用于 recency、forgetting decay、时间过滤和状态更新判断 |
| `embedding` | 可选但推荐 | 语义向量 | toy 数据可为 null；正式实验应使用 embedding similarity |
| `event_id` | 必要 | 连接所属 Event | 支持 Event-MU 双层结构和 event-level 聚合 |
| `memory_type` | 必要 | 区分记忆类型 | 决定使用 TMT 还是 decay，也支持 query-mode-aware ranking |
| `ddl` | todo 必要，non-todo 必须 null | 截止时间 | TMT 激活核心字段，用于 task_due/task_priority 排序 |
| `importance` | 必要 | 记忆重要性 | 用于排序、TMT 价值项、长期偏好保留 |
| `accessible_score` | 必要 | 当前可访问性 | 表示 memory 当前被取出的容易程度，是动态记忆机制的核心输出 |
| `is_done` | todo 必要，non-todo 必须 null | 任务完成状态 | 用于 task_status、completed_task_error_rate，避免已完成任务误召回 |

### 2.1 `memory_id`

必要。

这是 MU 的主键。实验中 gold label 必须指向具体 memory，因此没有 `memory_id` 就无法计算 memory-level recall、NDCG、MRR。

用途：

```text
gold label 标注
检索结果排序
去重
状态更新
错误分析
```

### 2.2 `content`

必要。

这是记忆真正进入 context 的文本。它应当是简洁、可直接给 LLM 使用的自然语言句子。

例如：

```text
User needs to submit the hospital schedule swap form by 2026-05-06.
```

用途：

```text
语义检索
关键词/实体匹配
LLM answer generation
人工检查 gold label
```

### 2.3 `timestamp`

必要。

用于描述记忆产生或最后更新的时间。它不等同于 ddl。`timestamp` 是“这条记忆什么时候进入记忆库”，`ddl` 是“任务什么时候截止”。

用途：

```text
recency baseline
forgetting decay
时间段过滤
判断新旧偏好冲突
判断 status update 覆盖关系
```

如果没有 `timestamp`，就无法实现艾宾浩斯式衰减，也无法对比 recency baseline。

### 2.4 `embedding`

正式实验推荐，toy 阶段可为 null。

它用于真实 semantic retrieval。当前 toy 代码用词面 overlap 只是临时代替，不适合正式论文结论。

用途：

```text
similarity_score
event smooth-max 聚合
semantic-only baseline
hybrid baseline
```

是否必须？

```text
toy / schema 设计阶段: 可选
正式实验阶段: 基本必要
```

### 2.5 `event_id`

必要。

MU 必须知道自己属于哪个 Event，否则 Event-Memory 双层结构无法建立。

用途：

```text
从 event 找内部 MU
从 MU 回溯 event
event-level scoring
gold_event_ids 评估
context packing
```

### 2.6 `memory_type`

必要。

这是整个方法区分 todo 与 non-todo 的关键字段。

建议类型：

```text
todo
preference
profile
fact
habit
constraint
dependency
status_update
```

用途：

```text
todo 使用 TMT_score
non-todo 使用 forgetting_decay
query_mode routing
todo_intrusion_rate
non_todo_recall
```

如果没有 `memory_type`，你的方法就退化成普通统一权重检索。

### 2.7 `ddl`

todo 必要，non-todo 必须为 null。

这是 TMT 激活的核心字段。Todo 任务越接近 ddl，理论上越应该提高 accessible score。

用途：

```text
TMT_score
deadline_activation
task_due query
deadline_ranking_accuracy
过期任务检测
```

注意：

```text
ddl 不应直接决定排序
ddl 应与 importance、query_subtype、is_done 一起使用
```

否则会出现当前实验中暴露的问题：近 ddl 但任务域不匹配的事件被过度激活。

### 2.8 `importance`

必要。

表示用户或系统认为该记忆的重要性，范围 `[0, 1]`。

用途：

```text
TMT 中的 Value
Generative Agents-style baseline
长期偏好保留
event_value 计算
排序加权
```

importance 和 accessible_score 的区别：

```text
importance: 这条记忆本身有多重要，偏静态
accessible_score: 当前有多容易被取出，偏动态
```

例如，一个半年后截止的重要任务 importance 高，但当前 accessible_score 可能中等。

### 2.9 `accessible_score`

必要。

这是本机制的核心字段。它表示当前时刻该记忆被检索到的容易程度。

用途：

```text
memory ranking
context selection
动态记忆更新
实验中比较不同策略的 retrieval ease
```

对 todo：

```text
接近 ddl 时 accessible_score 可升高
完成后 accessible_score 可降低
过期未完成时可触发 overdue boost
```

对 non-todo：

```text
随时间衰减
被访问或确认后增强
稳定偏好衰减较慢
```

理论上 `accessible_score` 可以不存储、每次动态计算。但保留这个字段有两个好处：

```text
1. 可解释：能观察每条记忆当前状态
2. 可缓存：避免每次检索都从零计算
```

### 2.10 `is_done`

todo 必要，non-todo 必须为 null。

任务管理场景中非常关键。没有它，就无法区分“已完成任务”和“未完成任务”。

用途：

```text
task_status query
completed_task_error_rate
task recommendation
TMT 完成惩罚
避免已完成任务进入今日待办
```

示例：

```text
已完成但语义相关的 todo 应该在 task_context 中可能被召回
但在 task_due/task_priority 中应被降权
```

## 3. Event 字段说明

| 字段 | 是否必要 | 作用 | 说明 |
|---|---|---|---|
| `event_id` | 必要 | Event 唯一标识 | 用于 event-level gold label、检索和 context packing |
| `title` | 推荐 | Event 简短标题 | 便于人工检查，也可参与检索 |
| `time_range` | 必要 | Event 时间范围 | 用于 recency、时间过滤、event ordering |
| `event_text` | 必要 | Event 文本表示 | event-level retrieval 的主要文本 |
| `event_embedding` | 可选但推荐 | Event 向量 | 正式实验可用于 event similarity baseline |
| `memory_ids` | 必要 | Event 内部 MU 集合 | Event-Memory 双层结构的连接字段 |
| `event_value` | 推荐 | Event 当前价值 | 可作为 event prior 或聚合 importance |
| `event_status` | 推荐 | Event 状态 | active/closed/dormant/superseded，辅助过滤和排序 |

### 3.1 `event_id`

必要。

Event 级别的主键。没有它就无法标注 `gold_event_ids`。

用途：

```text
event retrieval
supporting_event_recall
context packing
错误分析
```

### 3.2 `title`

推荐。

不是算法绝对必需，但对人工检查和可解释性很重要。标题也可以作为 event_text 的补充参与检索。

用途：

```text
人工浏览
错误分析
检索解释
CSV 输出
```

如果极简实现，可以省略；但论文实验建议保留。

### 3.3 `time_range`

必要。

表示该 Event 覆盖的对话时间段。Event 是一段连续对话块，因此它需要 start/end。

用途：

```text
event recency
时间段约束
按时间排序
区分旧事件与新事件
检测 superseded event
```

和 MU 的 `timestamp` 区别：

```text
event.time_range: 对话块的整体时间
memory.timestamp: 某条 MU 的产生/更新时间
```

### 3.4 `event_text`

必要。

这是 Event 的文本表示，可由 event summary、title 和关键 MU 摘要组成。

用途：

```text
event-level similarity
keyword/entity matching
LLM context 的 event summary
baseline 对比
```

如果不使用 `event_text`，Event retrieval 就只能依赖内部 MU 聚合。你的 proposed method 可以这样做，但 baseline 和解释都会变弱。

### 3.5 `event_embedding`

正式实验推荐，toy 阶段可为 null。

它用于直接进行 event-level semantic retrieval。

用途：

```text
Event-first + Similarity baseline
event retrieval
和 MU smooth-max 聚合方法对比
```

该字段可以由 `event_text` 生成，因此不是人工标注字段。

### 3.6 `memory_ids`

必要。

这是 Event 到 MU 的显式连接。没有它就无法在召回 Event 后进入 Event 内部做 MU ranking。

用途：

```text
Event 内 MU 排序
smooth-max event score
context packing
事件级召回后的证据展开
```

### 3.7 `event_value`

推荐。

表示该事件当前整体价值，范围 `[0, 1]`。它可以由内部 MU 的 importance、accessible_score、todo urgency 聚合得到，也可以在 synthetic data 中预设。

用途：

```text
event prior
排序 tie-breaker
衡量 event 是否值得进入 context
事件级衰减或激活
```

是否必须？

```text
最小实现: 可省略，由内部 MU 动态聚合
正式实验: 建议保留，方便解释与 ablation
```

### 3.8 `event_status`

推荐。

表示事件状态：

```text
active: 仍然相关
closed: 已结束
dormant: 暂时沉睡，可能未来有用
superseded: 被后续事件覆盖
```

用途：

```text
过滤过期事件
降低 closed/dormant 的 prior
处理偏好更新或任务状态更新
评估旧记忆冲突
```

在任务管理 agent 中，`event_status` 很有用，因为一个旧 event 可能语义相似，但已被后续状态更新覆盖。

## 4. 哪些字段可以简化？

如果只做最小 toy demo，可以保留：

```text
MemoryUnit:
memory_id
content
timestamp
event_id
memory_type
ddl
importance
accessible_score
is_done

Event:
event_id
title
time_range
event_text
memory_ids
event_status
```

可以暂时设为 null 或后续生成：

```text
embedding
event_embedding
```

可以动态计算但建议保留：

```text
event_value
accessible_score
```

## 5. 字段与研究贡献的对应关系

| 研究贡献 | 依赖字段 |
|---|---|
| Event-Memory 双层结构 | `event_id`, `memory_ids`, `event_text`, `event_embedding` |
| Todo TMT 激活 | `memory_type`, `ddl`, `importance`, `is_done`, `accessible_score` |
| Non-todo 遗忘衰减 | `memory_type`, `timestamp`, `importance`, `accessible_score` |
| Query-mode-aware ranking | `memory_type`, `ddl`, `is_done`, `event_status` |
| Event-level retrieval | `event_text`, `event_embedding`, `memory_ids`, `event_value` |
| 实验评估 | `memory_id`, `event_id`, `gold_event_ids`, `gold memory ids` |

## 6. 总结

当前字段设计整体是必要且合理的。真正必不可少的是：

```text
MU: memory_id, content, timestamp, event_id, memory_type, importance
Todo-specific: ddl, is_done
Dynamic retrieval: accessible_score
Event: event_id, time_range, event_text, memory_ids
```

`embedding`、`event_embedding` 和 `event_value` 在 toy 阶段可以为空或动态计算，但正式实验建议保留。`event_status` 不是数学公式必需项，但对任务管理、状态更新、旧记忆覆盖和错误分析非常有价值。

