我正在做一个长期个人记忆检索 benchmark。

这个 benchmark 面向高频 AI agent 用户。用户不会只用 agent 做工作或学习，也会用它处理生活、情绪、购物、健康、家庭、临时想法等事情。

benchmark 的核心假设是：
memory 是否应该被召回，不只取决于语义相关性，还取决于它在当前时间、任务状态、完成状态和稳定性下是否 cognitively accessible。

本阶段任务：
只扩充 user profile，不生成事件、不生成 memory、不生成 query、不生成 gold。

user profile 的作用：
它不是人物小传，而是后续 latent world / event timeline / memory generation 的控制器。
每个字段都应该能影响后续会生成什么任务、偏好、噪音、计划变化和记忆风格。

请为每个 seed user 扩充以下字段：

- user_id
- macro_archetype
- user_archetype
- concrete_identity
- life_stage
- agent_usage_level
- agent_usage_style
- main_life_domains
- primary_goals
- stable_preferences
- dynamic_preferences
- recurring_tasks
- typical_noise_sources
- memory_style
- likely_task_states
- likely_plan_changes
- likely_hard_negatives

字段要求：

1. concrete_identity
具体身份，不能太泛。
例如：不是“学生”，而是“硕士 NLP 学生，正在论文方法设计和实验初版阶段”。

2. life_stage
当前阶段。它要能决定后续事件。
例如：投稿返修期、找实习期、融资材料准备期、装修前期、慢病复诊前期。

3. agent_usage_style
列 3-5 条，说明他怎么用 agent。
必须包含工作/学习用途，也可以包含生活用途。

4. main_life_domains
列 4-6 个领域。
不要只有工作/学习，至少包含 1-2 个生活域或噪音域。

5. primary_goals
列 2-4 个当前长期目标。
这些目标未来会生成 active tasks 和 plans。

6. stable_preferences
列 2-4 条长期稳定偏好。
这些偏好未来应该比临时事实更稳定。

7. dynamic_preferences
列 2-4 条容易变化的偏好。
这些未来会产生 old preference / updated preference 干扰。

8. recurring_tasks
列 3-5 条反复出现的任务。
这些任务未来会生成 recurring memory。

9. typical_noise_sources
列 3-5 条噪音来源。
必须真实，不要全是有用任务。
可以包括情绪、购物、健康、家庭、娱乐、临时想法、短期焦虑等。

10. memory_style
一句话描述这个用户留下 memory 的语言风格。
例如：碎碎念、清单化、正式总结、焦虑型、半句笔记、口语化。

11. likely_task_states
列出这个用户后续最可能出现的任务状态。
例如：active、completed、overdue、cancelled、postponed。

12. likely_plan_changes
列 2-3 条这个用户自然会出现的计划变化。
例如：大计划缩小、deadline 提前、换项目优先级、旧方案被新方案替代。

13. likely_hard_negatives
列 2-3 类后续适合生成的 hard negative。
例如：旧计划、已完成 todo、语义相似但不同项目、临时偏好、过期健康记录。

输出要求：
- 只输出 JSON。
- 不要输出解释。
- 不要生成 timeline。
- 不要生成 memory。
- 不要生成 query。
- 不要生成 gold。
- 保留原 user_id。
- 不要改变 macro_archetype。
- 每个用户必须保持和 seed identity 一致，但要有个体差异。