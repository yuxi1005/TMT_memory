# Event-Memory + TMT/Decay 记忆机制实验设计

## 1. 研究目标

本文评估一种面向 To-Do / 任务管理场景的大模型 Agent 记忆机制。该机制采用 Event-Memory 双层结构：Event 表示一段连续交互形成的上下文单元，Memory Unit 表示从对话中抽取出的具体任务、偏好、用户信息或事实记忆。核心假设是：不同类型记忆不应使用相同的衰减和召回策略。Todo 类记忆应受截止时间、重要性和完成状态影响；non-todo 类记忆应随时间降低可访问性，但不被物理删除。

## 2. Research Questions

RQ1：Event-Memory 双层结构是否比 flat memory retrieval 更能召回相关上下文？

RQ2：对 todo 类记忆引入 Temporal Motivation Theory 是否能提升任务型 query 下的任务召回和优先级排序？

RQ3：对 non-todo 类记忆引入遗忘曲线衰减，是否能减少无关旧记忆进入 context，同时保留稳定偏好和长期用户信息？

## 3. 数据集设计

主实验使用自建 synthetic task-memory dataset。Pilot v2 规模建议为：

```text
users: 10
events per user: 20
memories per user: 80-120
queries per user: 20
total queries: 200
```

每个 user 包含多类 event：任务规划、任务状态更新、偏好表达、个人信息、生活/工作干扰事件、长期目标和过期事项。每个 event 包含 3-6 条 memory units。

必须加入 hard distractors：

```text
最近但无关的 event
语义相似但任务状态不同的 event
ddl 很近但任务域不匹配的 todo
已完成但语义高度相关的 todo
旧偏好与新偏好冲突的 non-todo
同一任务的多轮状态更新
```

## 4. Query 类型

```text
task_due: 查询近期截止任务
task_priority: 查询当前最该优先做什么
task_status: 查询某任务是否完成
task_context: 查询某任务背景
task_dependency: 查询任务依赖
chat_preference: 查询用户偏好
chat_profile: 查询用户信息
chat_history: 查询过去对话事实
mixed: 同时需要 todo 和 non-todo 记忆
negative: 记忆库中没有答案
```

## 5. Gold Label

每个 query 标注两层 gold：

```json
{
  "gold_event_ids": ["e001", "e004"],
  "gold_memories": [
    {"memory_id": "m001", "relevance": 3},
    {"memory_id": "m007", "relevance": 2}
  ]
}
```

relevance 使用 0-3 分级：

```text
3 = 必须召回，缺失会导致答错
2 = 有帮助，可增强答案
1 = 弱相关，仅提供背景
0 = 不相关
```

## 6. Baselines

基础检索 baseline：

```text
Recency-only
Similarity-only
Similarity + Recency
Similarity + Importance
Flat-memory retrieval
Event-first + Similarity
```

Agent memory baseline：

```text
Generative Agents-style retrieval: relevance + recency + importance
MemoryBank-style decay: long-term memory + forgetting curve
MemGPT-style archival retrieval: core memory + archival memory retrieval
```

## 7. Proposed Method

第一阶段进行 event retrieval。Event 分数由其内部 memory unit 分数的 smooth maximum 聚合得到，以避免平均池化稀释关键记忆。

第二阶段进行 memory unit ranking。根据 query mode 和 query subtype 使用不同权重：

```text
task_due: 提高 ddl / TMT 权重
task_status: 提高 is_done / unfinished matching 权重
task_context: 提高 semantic / event_text 权重
chat_preference: 提高 preference / non-todo 权重
mixed: 同时保留 todo 与 non-todo 双通道召回
```

Todo memory 使用 TMT 风格激活；non-todo memory 使用遗忘曲线衰减。系统不删除记忆，只动态调整 accessible_score。

## 8. Metrics

Event-level：

```text
supporting_event_recall@k
event_NDCG@k
event_MRR
token_cost
```

Memory-level：

```text
memory_recall@k
memory_NDCG@k
todo_recall@k
non_todo_recall@k
completed_task_error_rate
todo_intrusion_rate
deadline_ranking_accuracy
```

Downstream answer：

```text
answer_accuracy
task_status_accuracy
deadline_recommendation_accuracy
abstention_accuracy
```

## 9. Ablation

```text
Ours full
w/o Event layer
w/o TMT activation
w/o forgetting decay
w/o query subtype routing
w/o dependency score
flat memory version of ours
```

## 10. 预期结果

预期 proposed method 在 mixed/chat query 中提升 non-todo 相关记忆召回，在 task_due/task_priority query 中提升 todo 记忆排序，在相同 token budget 下获得更高 supporting_event_recall 和 memory_NDCG。若 task_status query 表现较弱，需要验证是否是 TMT 过度激活导致，并通过 subtype gate 进行修正。

