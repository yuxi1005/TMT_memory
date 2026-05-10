# Pilot v2 数据生成规范

## 1. 目标

Pilot v2 用于正式实验前的中等规模验证，目标是检验 Event-Memory + TMT/Decay 机制在任务管理场景下是否优于简单 recency、similarity 和普通 agent memory baseline。

该数据集不追求真实用户隐私数据，而是构造可控 synthetic users，使每个样本都能明确标注：

```text
哪些 events 应进入 context
哪些 memory units 是 gold evidence
哪些 distractors 会误导不同 baseline
LLM 是否有足够信息回答 query
```

## 2. 数据规模

建议规模：

```text
users: 10
events per user: 20
memories per event: 3-6
memories per user: 80-120
queries per user: 20
total events: 200
total memories: 800-1200
total queries: 200
```

每个 user 的 20 个 events 中：

```text
core task events: 6
task update events: 4
preference/profile events: 3
mixed planning events: 2
hard distractor events: 5
```

## 3. 基础 Schema

MemoryUnit 字段必须遵守：

```text
memory_id
content
timestamp
embedding
event_id
memory_type
ddl
importance
accessible_score
is_done
```

Event 字段必须遵守：

```text
event_id
title
time_range
event_text
event_embedding
memory_ids
```

Pilot v2 中 `embedding` 和 `event_embedding` 仍可设为 `null`。后续真实检索实验再统一补 embedding。

注意：Event 只作为对话块容器存在，不保存 `event_value` 和 `event_status`。真正参与四象限流转、任务状态变化、TMT 激活和遗忘衰减的是 Memory Unit。一个 Event 内可以同时包含不同状态、不同类型的 MU，因此不应给 Event 赋予单一状态或单一价值。

## 4. 用户画像分布

10 个 synthetic users 应覆盖不同任务管理场景：

```text
u001: 研究生，课程项目 + 论文实验 + 健康计划
u002: 产品经理，版本发布 + 用户访谈 + stakeholder update
u003: 自由插画师，客户稿件 + 作品集 + 学习计划
u004: 医生/医学生，排班事项 + 考试复习 + 家庭任务
u005: 运营负责人，办公室搬迁 + vendor 协调 + 旅行计划
u006: 初创公司工程师，bug 修复 + sprint planning + 技术债
u007: 法学院学生，case reading + moot court + 申请材料
u008: 独立内容创作者，视频脚本 + 发布计划 + 品牌偏好
u009: 家庭照护者，医疗预约 + 财务事项 + 日常采购
u010: 数据分析师，报表交付 + dashboard 维护 + 学习目标
```

每个用户必须有：

```text
长期偏好 3-5 条
稳定身份/背景信息 2-4 条
重复任务习惯 2-3 条
短期 todo 10-20 条
已完成 todo 5-10 条
过期未完成 todo 2-5 条
```

## 5. Event 类型与容器规则

每个 user 生成 20 个 events，建议分布如下：

| event 类型 | 数量 | 说明 |
|---|---:|---|
| `task_planning` | 4 | 新任务产生，包含 ddl、importance |
| `task_update` | 4 | 任务状态变化，如完成、延期、取消 |
| `task_dependency` | 2 | 包含前置条件、等待他人、材料依赖 |
| `preference_profile` | 3 | 用户偏好、习惯、身份信息 |
| `mixed_planning` | 2 | 需要结合任务、偏好、时间安排 |
| `hard_distractor` | 5 | 用于干扰 recency/similarity/TMT |

Event 的职责仅包括：

```text
聚合一段连续对话
提供 event_text 作为 event-level retrieval 的文本入口
通过 memory_ids 连接内部 MU
在进入 context 时提供局部上下文
```

Event 不应包含 `event_value` 或 `event_status`。如果需要 event 级分数，应在检索时由内部 MU 动态聚合得到：

```text
event_score(query, event) =
SmoothMax({ score(query, mu_i) | mu_i in event.memory_ids })
```

因此，Event 的价值是 query-dependent 的临时检索分数，而不是静态字段。

## 6. Memory 类型

`memory_type` 建议使用：

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

其中：

```text
todo: 具体任务
preference: 用户偏好
profile: 用户身份/背景
fact: 对话事实
habit: 用户习惯
constraint: 时间、地点、资源限制
dependency: 任务依赖
status_update: 对已有任务的状态更新
```

## 7. Todo 记忆生成规则

每个 user 的 todo 需要覆盖：

```text
近 ddl 未完成任务: 4-6
远 ddl 未完成任务: 4-6
已完成任务: 5-10
过期未完成任务: 2-5
高重要远 ddl: 2-3
低重要近 ddl: 2-3
有依赖任务: 2-4
被后续状态更新覆盖的任务: 2-4
```

字段约束：

```text
ddl: todo 类型必须有，non-todo 必须为 null
is_done: todo 类型为 true/false，non-todo 为 null
importance: 0.2-1.0
accessible_score: 0.1-0.9
```

时间分布以统一 `now` 为基准：

```text
now = 2026-05-06T09:00:00+08:00

timestamp:
2026-03-15 至 2026-05-06

ddl:
2026-04-20 至 2026-06-15
```

## 8. Non-todo 记忆生成规则

Non-todo 需要覆盖：

```text
稳定偏好: 衰减慢，importance 高
临时偏好: 衰减快，importance 中低
长期身份信息: 衰减极慢，importance 中高
一次性事实: 衰减快
习惯: 衰减中等，可被多次 query 使用
被更新偏好: 旧偏好与新偏好冲突
```

必须包含偏好更新样本，例如：

```text
旧记忆: 用户喜欢晚上处理深度工作
新记忆: 用户最近发现上午更适合深度工作
```

Gold label 应指向新记忆，旧记忆作为 distractor。

## 9. Hard Distractor 规则

每个 user 至少生成 5 个 hard distractor events。必须覆盖：

```text
recent_irrelevant:
最近发生但与 query 无关，干扰 recency-only

semantic_similar_wrong_status:
语义相似但任务已完成，干扰 similarity-only

urgent_wrong_domain:
ddl 很近但任务域不匹配，干扰 TMT-only

old_but_stable_preference:
时间久但仍重要，检验 forgetting decay 是否过度遗忘

superseded_or_updated_mu:
旧 MU 被新 MU 更新或覆盖，检验 MU 层的时间更新和状态更新能力
```

Distractor 不能只是明显无关的闲聊，否则实验过于简单。

## 10. Query 生成规则

每个 user 生成 20 个 queries：

| query_subtype | 数量 |
|---|---:|
| `task_due` | 3 |
| `task_priority` | 3 |
| `task_status` | 3 |
| `task_context` | 2 |
| `task_dependency` | 2 |
| `chat_preference` | 2 |
| `chat_profile` | 1 |
| `chat_history` | 1 |
| `mixed` | 2 |
| `negative` | 1 |

Query 语言建议以中文为主，但 memory content 可使用英文或中英混合。正式 embedding 实验中应避免只靠词面 overlap。

每个 query 必须标注：

```text
query_id
query
query_mode
query_subtype
now
constraints
gold_event_ids
gold
answer_type
```

`answer_type` 可取：

```text
ranked_tasks
yes_no_status
short_answer
planning_suggestion
abstention
```

## 11. Gold Label 规则

每个 query 标注：

```json
{
  "gold_event_ids": ["u001_e003", "u001_e014"],
  "gold": [
    {
      "memory_id": "u001_m021",
      "relevance": 3,
      "reason": "未完成且 ddl 最近的目标任务"
    }
  ]
}
```

相关性等级：

```text
3: 必须召回，缺失会导致答错
2: 有帮助，可增强答案
1: 弱相关背景
0: 不相关
```

每个 query 至少有：

```text
1 个 relevance=3 的 memory
1 个 gold_event_id
```

`negative` query 例外：

```text
gold = []
gold_event_ids = []
answer_type = abstention
```

## 12. 质检规则

生成后必须检查：

```text
每个 memory_id 唯一
每个 event_id 唯一
每个 event.memory_ids 都能找到对应 memory
每个 memory.event_id 都能找到对应 event
event 不应包含 event_value 或 event_status
todo memory 必须有 ddl 和 is_done
non-todo memory 的 ddl 必须为 null，is_done 必须为 null
importance 和 accessible_score 在 [0, 1]
每个非 negative query 至少有一个 gold memory
每个 user 正好 20 events 和 20 queries
每个 user 至少 5 个 hard distractor events
```

## 13. 文件输出

建议输出：

```text
data/pilot_v2_dataset.jsonl
data/pilot_v2_dataset.pretty.json
data/pilot_v2_generation_summary.csv
notes/pilot_v2_data_generation_spec_zh.md
```

JSONL 用于实验脚本；pretty JSON 用于人工检查；summary CSV 用于统计每个用户的 event/memory/query 分布。
