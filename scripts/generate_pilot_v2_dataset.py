import csv
import json
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSONL = ROOT / "pilot_v2_dataset.jsonl"
OUT_PRETTY = ROOT / "pilot_v2_dataset.pretty.json"
OUT_SUMMARY = ROOT / "pilot_v2_generation_summary.csv"

NOW = "2026-05-06T09:00:00+08:00"


USERS = [
    {
        "user_id": "u001",
        "persona": "研究生，课程项目 + 论文实验 + 健康计划",
        "domains": ["课程项目汇报", "论文实验复现", "健身计划", "奖学金材料"],
        "preference": "用户喜欢简洁、清单式的计划，并倾向上午处理高认知负荷任务。",
        "updated_preference_old": "用户过去认为晚上更适合深度工作。",
        "updated_preference_new": "用户最近发现上午更适合深度工作，晚上适合整理类任务。",
    },
    {
        "user_id": "u002",
        "persona": "产品经理，版本发布 + 用户访谈 + stakeholder update",
        "domains": ["beta 发布", "用户访谈", "风险同步", "路线图评审"],
        "preference": "用户喜欢把风险写在进展之前，并保留客户原话。",
        "updated_preference_old": "用户过去喜欢用长段落写周报。",
        "updated_preference_new": "用户现在偏好 progress、risks、asks 三段式 bullet 周报。",
    },
    {
        "user_id": "u003",
        "persona": "自由插画师，客户稿件 + 作品集 + 学习计划",
        "domains": ["客户封面稿", "作品集更新", "色彩练习", "客户沟通"],
        "preference": "用户喜欢先做 moodboard，再进入正式绘制。",
        "updated_preference_old": "用户过去给客户写消息时语气偏正式。",
        "updated_preference_new": "用户现在希望客户消息温暖自然，不要过于正式。",
    },
    {
        "user_id": "u004",
        "persona": "医生/医学生，排班事项 + 考试复习 + 家庭任务",
        "domains": ["排班行政", "执业考试复习", "家庭照护", "夜班恢复"],
        "preference": "用户下班后喜欢 30 分钟以内的紧凑复习块。",
        "updated_preference_old": "用户过去喜欢一次性刷完长题组。",
        "updated_preference_new": "用户现在偏好短题组加错题回顾，避免夜班后密集阅读。",
    },
    {
        "user_id": "u005",
        "persona": "运营负责人，办公室搬迁 + vendor 协调 + 旅行计划",
        "domains": ["办公室搬迁", "供应商合同", "网络迁移", "差旅行程"],
        "preference": "用户喜欢用表格比较供应商的价格、可靠性和支持响应。",
        "updated_preference_old": "用户过去只按价格比较供应商。",
        "updated_preference_new": "用户现在同时看可靠性、周末支持和响应速度。",
    },
    {
        "user_id": "u006",
        "persona": "初创公司工程师，bug 修复 + sprint planning + 技术债",
        "domains": ["支付 bug", "sprint planning", "技术债清理", "监控告警"],
        "preference": "用户喜欢先修影响用户的 bug，再处理内部重构。",
        "updated_preference_old": "用户过去喜欢先做重构再修 bug。",
        "updated_preference_new": "用户现在优先处理用户可见问题，重构排到稳定窗口。",
    },
    {
        "user_id": "u007",
        "persona": "法学院学生，case reading + moot court + 申请材料",
        "domains": ["案例阅读", "模拟法庭", "申请材料", "导师邮件"],
        "preference": "用户喜欢用 issue-rule-analysis-conclusion 格式整理案例。",
        "updated_preference_old": "用户过去按时间顺序整理案例笔记。",
        "updated_preference_new": "用户现在优先按争点和规则整理案例笔记。",
    },
    {
        "user_id": "u008",
        "persona": "独立内容创作者，视频脚本 + 发布计划 + 品牌偏好",
        "domains": ["视频脚本", "发布排期", "品牌合作", "素材剪辑"],
        "preference": "用户喜欢先写 hook，再写正文脚本。",
        "updated_preference_old": "用户过去偏好一镜到底的长视频。",
        "updated_preference_new": "用户现在更偏好短节奏、多段落的视频结构。",
    },
    {
        "user_id": "u009",
        "persona": "家庭照护者，医疗预约 + 财务事项 + 日常采购",
        "domains": ["医疗预约", "保险报销", "日常采购", "家人用药"],
        "preference": "用户喜欢把照护事项按医院、药品、票据分组。",
        "updated_preference_old": "用户过去把所有照护事项放在一个列表里。",
        "updated_preference_new": "用户现在按地点和材料分组管理照护任务。",
    },
    {
        "user_id": "u010",
        "persona": "数据分析师，报表交付 + dashboard 维护 + 学习目标",
        "domains": ["月度报表", "dashboard 维护", "SQL 学习", "业务复盘"],
        "preference": "用户喜欢先确认指标口径，再做图表。",
        "updated_preference_old": "用户过去先画图再核对指标。",
        "updated_preference_new": "用户现在先冻结指标定义，再进入 dashboard 制作。",
    },
]


def day(day_num, hour=10, minute=0):
    dt = datetime(2026, 4, 1, hour, minute) + timedelta(days=day_num - 1)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def may(day_num, hour=18, minute=0):
    return f"2026-05-{day_num:02d}T{hour:02d}:{minute:02d}:00+08:00"


def june(day_num, hour=18, minute=0):
    return f"2026-06-{day_num:02d}T{hour:02d}:{minute:02d}:00+08:00"


class Builder:
    def __init__(self, config):
        self.config = config
        self.uid = config["user_id"]
        self.events = []
        self.memories = []
        self.queries = []
        self.event_no = 0
        self.memory_no = 0
        self.refs = {}

    def next_event_id(self):
        self.event_no += 1
        return f"{self.uid}_e{self.event_no:03d}"

    def next_memory_id(self):
        self.memory_no += 1
        return f"{self.uid}_m{self.memory_no:03d}"

    def add_memory(self, event_id, content, timestamp, memory_type, importance, accessible_score, ddl=None, is_done=None, ref=None):
        memory = {
            "memory_id": self.next_memory_id(),
            "content": content,
            "timestamp": timestamp,
            "embedding": None,
            "event_id": event_id,
            "memory_type": memory_type,
            "ddl": ddl,
            "importance": round(float(importance), 2),
            "accessible_score": round(float(accessible_score), 2),
            "is_done": is_done,
        }
        self.memories.append(memory)
        if ref:
            self.refs[ref] = memory["memory_id"]
        return memory

    def add_event(self, title, start_day, event_text, memory_specs):
        event_id = self.next_event_id()
        start = day(start_day, 9 + (self.event_no % 9), 5)
        end = day(start_day, 9 + (self.event_no % 9), 35)
        memory_ids = []
        while len(memory_specs) < 4:
            memory_specs.append(
                self.m(
                    f"Context note for {title}: this detail provides background but is not usually the primary answer.",
                    start,
                    "fact",
                    0.32,
                    0.26,
                )
            )
        for spec in memory_specs:
            memory = self.add_memory(event_id=event_id, **spec)
            memory_ids.append(memory["memory_id"])
        self.events.append(
            {
                "event_id": event_id,
                "title": title,
                "time_range": {"start": start, "end": end},
                "event_text": event_text,
                "event_embedding": None,
                "memory_ids": memory_ids,
            }
        )
        return event_id

    def m(self, content, timestamp, memory_type, importance, accessible_score, ddl=None, is_done=None, ref=None):
        return {
            "content": content,
            "timestamp": timestamp,
            "memory_type": memory_type,
            "importance": importance,
            "accessible_score": accessible_score,
            "ddl": ddl,
            "is_done": is_done,
            "ref": ref,
        }

    def gold(self, refs):
        return [
            {"memory_id": self.refs[ref], "relevance": rel, "reason": reason}
            for ref, rel, reason in refs
        ]

    def event_ids_for_refs(self, refs):
        memory_to_event = {m["memory_id"]: m["event_id"] for m in self.memories}
        ids = []
        for ref, _, _ in refs:
            eid = memory_to_event[self.refs[ref]]
            if eid not in ids:
                ids.append(eid)
        return ids

    def add_query(self, qid, query, mode, subtype, refs, answer_type, constraints=None):
        self.queries.append(
            {
                "query_id": f"{self.uid}_q{qid:03d}",
                "query": query,
                "query_mode": mode,
                "query_subtype": subtype,
                "now": NOW,
                "constraints": constraints or {"time_range": None, "entities": [], "keywords": []},
                "gold": self.gold(refs) if refs else [],
                "gold_event_ids": self.event_ids_for_refs(refs) if refs else [],
                "answer_type": answer_type,
            }
        )

    def build_events(self):
        d = self.config["domains"]
        p = self.config["preference"]

        self.add_event(
            f"{d[0]} planning",
            16,
            f"用户规划了{d[0]}，包含关键交付、截止时间和优先级。",
            [
                self.m(f"User needs to finish the main deliverable for {d[0]} by 2026-05-08.", day(16, 10), "todo", 0.92, 0.78, may(8, 20), False, "due_main"),
                self.m(f"User should prepare supporting materials for {d[0]} by 2026-05-07.", day(16, 10, 6), "todo", 0.84, 0.76, may(7, 18), False, "due_support"),
                self.m(f"{d[0]} is currently the user's highest priority project.", day(16, 10, 12), "fact", 0.72, 0.55, ref="main_fact"),
                self.m(p, day(16, 10, 18), "preference", 0.78, 0.58, ref="general_pref"),
            ],
        )
        self.add_event(
            f"{d[1]} planning",
            18,
            f"用户规划了{d[1]}，其中包含一个较远截止但重要性较高的任务。",
            [
                self.m(f"User needs to complete the core task for {d[1]} by 2026-05-15.", day(18, 11), "todo", 0.86, 0.57, may(15, 19), False, "far_important"),
                self.m(f"User should collect background notes for {d[1]} by 2026-05-11.", day(18, 11, 6), "todo", 0.62, 0.45, may(11, 18), False, "mid_task"),
                self.m(f"User wants a reproducible checklist for {d[1]}.", day(18, 11, 12), "preference", 0.66, 0.47, ref="domain_pref"),
                self.m(f"{d[1]} depends on a small set of reference materials.", day(18, 11, 18), "fact", 0.5, 0.38),
            ],
        )
        self.add_event(
            f"{d[2]} planning",
            20,
            f"用户讨论了{d[2]}，该事件包含低重要但近截止任务。",
            [
                self.m(f"User needs to do a small check-in for {d[2]} by 2026-05-06.", day(20, 12), "todo", 0.38, 0.61, may(6, 21), False, "low_near"),
                self.m(f"User wants to keep {d[2]} lightweight this week.", day(20, 12, 6), "preference", 0.46, 0.34),
                self.m(f"{d[2]} is useful but should not override urgent work tasks.", day(20, 12, 12), "constraint", 0.48, 0.35, ref="low_near_context"),
            ],
        )
        self.add_event(
            f"{d[3]} planning",
            22,
            f"用户规划了{d[3]}，其中有远期任务和资料整理事项。",
            [
                self.m(f"User needs to draft materials for {d[3]} by 2026-06-10.", day(22, 13), "todo", 0.7, 0.36, june(10, 20), False, "far_task"),
                self.m(f"User should organize references for {d[3]} before the draft.", day(22, 13, 6), "dependency", 0.58, 0.4, ref="far_dependency"),
                self.m(f"User treats {d[3]} as important but not urgent.", day(22, 13, 12), "fact", 0.52, 0.35),
            ],
        )

        self.add_event(
            f"{d[0]} status update",
            24,
            f"用户更新了{d[0]}的任务状态，部分任务已完成，部分任务延期。",
            [
                self.m(f"User completed the outline for {d[0]}.", day(24, 14), "todo", 0.65, 0.25, may(3, 18), True, "completed_main_old"),
                self.m(f"User still has not finished the supporting materials for {d[0]}.", day(24, 14, 6), "status_update", 0.82, 0.68, ref="status_support_unfinished"),
                self.m(f"The deadline for supporting materials of {d[0]} remains 2026-05-07.", day(24, 14, 12), "fact", 0.72, 0.58),
                self.m(f"User moved nonessential polishing for {d[0]} to later.", day(24, 14, 18), "todo", 0.36, 0.23, may(20, 18), False),
            ],
        )
        self.add_event(
            f"{d[1]} status update",
            26,
            f"用户更新了{d[1]}，包含已完成任务和仍待处理任务。",
            [
                self.m(f"User completed collecting initial notes for {d[1]}.", day(26, 15), "todo", 0.55, 0.24, may(2, 18), True, "completed_mid"),
                self.m(f"User still needs to complete the core task for {d[1]} by 2026-05-15.", day(26, 15, 6), "status_update", 0.82, 0.52, ref="status_far_unfinished"),
                self.m(f"User found one missing input for {d[1]}.", day(26, 15, 12), "dependency", 0.64, 0.5, ref="missing_input"),
            ],
        )
        self.add_event(
            f"{d[2]} status update",
            28,
            f"用户更新了{d[2]}，其中包含过期未完成事项。",
            [
                self.m(f"User missed the earlier check-in for {d[2]} before 2026-05-04.", day(28, 16), "todo", 0.5, 0.62, may(4, 20), False, "overdue_low"),
                self.m(f"User should not let overdue {d[2]} distract from {d[0]}.", day(28, 16, 6), "constraint", 0.55, 0.43, ref="overdue_constraint"),
                self.m(f"User completed one minor setup step for {d[2]}.", day(28, 16, 12), "todo", 0.34, 0.2, may(1, 18), True),
            ],
        )
        self.add_event(
            f"{d[3]} status update",
            30,
            f"用户更新了{d[3]}，其中包含旧任务被新计划覆盖的情况。",
            [
                self.m(f"User's old plan for {d[3]} was replaced by a shorter version.", day(30, 17), "status_update", 0.6, 0.42, ref="superseded_plan"),
                self.m(f"User completed a small checklist for {d[3]}.", day(30, 17, 6), "todo", 0.4, 0.22, may(2, 18), True),
                self.m(f"The new shorter version of {d[3]} is now the valid plan.", day(30, 17, 12), "fact", 0.66, 0.49, ref="new_valid_plan"),
            ],
        )

        self.add_event(
            f"{d[0]} dependency discussion",
            31,
            f"用户讨论了{d[0]}的前置依赖和等待事项。",
            [
                self.m(f"User cannot finalize {d[0]} until the supporting materials are prepared.", day(31, 10), "dependency", 0.82, 0.7, ref="main_dependency"),
                self.m(f"User needs to ask a collaborator for confirmation about {d[0]} by 2026-05-07.", day(31, 10, 6), "todo", 0.78, 0.72, may(7, 16), False, "dependency_todo"),
                self.m(f"The collaborator confirmation is a blocker for {d[0]}.", day(31, 10, 12), "constraint", 0.76, 0.65),
            ],
        )
        self.add_event(
            f"{d[1]} dependency discussion",
            32,
            f"用户讨论了{d[1]}的资料依赖和完成顺序。",
            [
                self.m(f"User needs the missing input before completing {d[1]}.", day(32, 11), "dependency", 0.7, 0.56, ref="far_dependency_detail"),
                self.m(f"User should check whether the missing input for {d[1]} has arrived by 2026-05-09.", day(32, 11, 6), "todo", 0.62, 0.5, may(9, 18), False, "far_dependency_todo"),
                self.m(f"{d[1]} can continue only after the input is confirmed.", day(32, 11, 12), "constraint", 0.6, 0.48),
            ],
        )

        self.add_event(
            "Stable preference and profile",
            33,
            "用户表达了稳定偏好、身份背景和长期工作习惯。",
            [
                self.m(self.config["preference"], day(33, 12), "preference", 0.82, 0.64, ref="stable_preference"),
                self.m(f"User background: {self.config['persona']}.", day(33, 12, 6), "profile", 0.74, 0.58, ref="profile"),
                self.m("User prefers reminders that explain why a task matters, not only what to do.", day(33, 12, 12), "preference", 0.68, 0.52, ref="reminder_pref"),
                self.m("User tends to batch low-cognitive tasks late in the day.", day(33, 12, 18), "habit", 0.58, 0.45, ref="batch_habit"),
            ],
        )
        self.add_event(
            "Old preference record",
            34,
            "用户过去的偏好被记录下来，但后续可能被更新。",
            [
                self.m(self.config["updated_preference_old"], day(34, 13), "preference", 0.62, 0.36, ref="old_preference"),
                self.m("This older preference should be treated cautiously if a newer preference exists.", day(34, 13, 6), "constraint", 0.55, 0.35),
                self.m("User did not explicitly confirm this old preference again.", day(34, 13, 12), "fact", 0.45, 0.28),
            ],
        )
        self.add_event(
            "Updated preference record",
            35,
            "用户更新了旧偏好，新偏好应覆盖旧偏好。",
            [
                self.m(self.config["updated_preference_new"], day(35, 14), "preference", 0.86, 0.72, ref="new_preference"),
                self.m("The newer preference should be preferred over the older preference when planning.", day(35, 14, 6), "status_update", 0.78, 0.66, ref="preference_update_rule"),
                self.m("User explicitly confirmed the updated preference.", day(35, 14, 12), "fact", 0.66, 0.54),
            ],
        )

        self.add_event(
            "Mixed planning for today",
            36,
            f"用户希望结合{d[0]}、个人偏好和时间安排来规划今天。",
            [
                self.m(f"User wants today's plan to prioritize {d[0]} before lower-value side tasks.", may(5, 9), "constraint", 0.86, 0.75, ref="today_plan_constraint"),
                self.m(f"User should schedule {d[0]} work during the time window matching the updated preference.", may(5, 9, 6), "todo", 0.8, 0.74, may(7, 18), False, "today_plan_todo"),
                self.m("User wants the plan to include one small recovery or admin block.", may(5, 9, 12), "preference", 0.58, 0.48),
            ],
        )
        self.add_event(
            "Mixed review and reminder",
            37,
            f"用户要求提醒事项同时考虑{d[1]}、任务依赖和长期偏好。",
            [
                self.m(f"User wants reminders for {d[1]} to mention the missing input dependency.", may(5, 15), "preference", 0.72, 0.62, ref="mixed_dependency_pref"),
                self.m(f"User should check {d[1]} dependency before doing deep work.", may(5, 15, 6), "todo", 0.68, 0.58, may(9, 18), False, "mixed_dependency_todo"),
                self.m("User prefers reminders grouped by urgency and dependency.", may(5, 15, 12), "preference", 0.7, 0.58, ref="grouped_reminder_pref"),
            ],
        )

        # Hard distractors.
        self.add_event(
            "Recent irrelevant side matter",
            38,
            "用户最近讨论了一个无关的生活小事，时间很近但与主要任务无关。",
            [
                self.m("User discussed buying a replacement water bottle yesterday.", may(5, 20), "fact", 0.22, 0.58, ref="recent_irrelevant"),
                self.m("The water bottle task is unrelated to current priority work.", may(5, 20, 6), "constraint", 0.25, 0.52),
                self.m("User may buy the water bottle next week.", may(5, 20, 12), "todo", 0.18, 0.5, may(14, 12), False),
            ],
        )
        self.add_event(
            "Semantic similar wrong status",
            25,
            f"用户讨论了一个与{d[0]}语义相似但已经完成的旧任务。",
            [
                self.m(f"User completed an older task similar to {d[0]} last week.", day(25, 9), "todo", 0.76, 0.26, may(1, 18), True, "similar_done"),
                self.m(f"The older {d[0]}-like task should not be treated as today's unfinished task.", day(25, 9, 6), "constraint", 0.68, 0.4),
                self.m(f"User only mentioned the old {d[0]} task as background.", day(25, 9, 12), "fact", 0.46, 0.32),
            ],
        )
        self.add_event(
            "Urgent wrong domain",
            39,
            f"用户有一个非常近截止但不属于 query 目标域的{d[2]}事项。",
            [
                self.m(f"User has an urgent but low-value {d[2]} side task due today.", may(6, 8), "todo", 0.32, 0.82, may(6, 13), False, "urgent_wrong_domain"),
                self.m(f"The urgent {d[2]} side task should not override {d[0]} when the query asks about {d[0]}.", may(6, 8, 6), "constraint", 0.6, 0.55),
                self.m(f"{d[2]} is a distractor for deadline-only ranking.", may(6, 8, 12), "fact", 0.42, 0.48),
            ],
        )
        self.add_event(
            "Old but stable preference",
            17,
            "用户较早表达过一个稳定偏好，虽然时间久但仍然有效。",
            [
                self.m("User strongly prefers concise checklists over long narrative plans.", day(17, 18), "preference", 0.84, 0.48, ref="old_stable_preference"),
                self.m("This checklist preference is stable across work and personal tasks.", day(17, 18, 6), "habit", 0.72, 0.42),
                self.m("The preference is old but should not be forgotten too aggressively.", day(17, 18, 12), "constraint", 0.7, 0.4),
            ],
        )
        self.add_event(
            "Superseded MU distractor",
            21,
            "用户有一条旧 MU 被后续 MU 更新或覆盖。",
            [
                self.m(f"Old memory: User planned to do {d[3]} as a long-form task.", day(21, 19), "fact", 0.55, 0.33, ref="old_superseded_mu"),
                self.m(f"Later update says {d[3]} should now use the shorter valid plan.", day(21, 19, 6), "status_update", 0.72, 0.5, ref="superseded_update"),
                self.m("The later MU should be preferred when a query asks for the current plan.", day(21, 19, 12), "constraint", 0.68, 0.48),
            ],
        )

    def build_queries(self):
        d = self.config["domains"]
        self.add_query(1, f"我最近最该先处理哪个{d[0]}任务？", "task", "task_due", [("due_support", 3, "近 ddl 且未完成"), ("due_main", 3, "高重要且近 ddl"), ("dependency_todo", 2, "同域依赖任务")], "ranked_tasks", {"time_range": "near_future", "entities": [d[0]], "keywords": ["最近", "先处理"]})
        self.add_query(2, "今天有哪些快到截止但不能被过度放大的事项？", "task", "task_due", [("due_support", 3, "目标主任务近 ddl"), ("urgent_wrong_domain", 1, "近 ddl 但错误任务域"), ("overdue_constraint", 2, "说明过期低价值事项不能覆盖主任务")], "ranked_tasks")
        self.add_query(3, f"{d[1]}接下来应该推进什么？", "task", "task_priority", [("far_important", 3, "高重要未完成"), ("missing_input", 2, "存在缺失输入"), ("far_dependency_todo", 2, "依赖检查任务")], "ranked_tasks")
        self.add_query(4, "现在最重要但不一定最紧急的任务是什么？", "task", "task_priority", [("far_important", 3, "高重要远 ddl"), ("due_main", 2, "高重要近 ddl"), ("far_task", 2, "重要但远期")], "ranked_tasks")
        self.add_query(5, f"{d[0]}还有什么没完成？", "task", "task_status", [("status_support_unfinished", 3, "明确未完成状态"), ("due_support", 3, "对应未完成任务"), ("similar_done", 1, "语义相似但已完成的干扰")], "yes_no_status")
        self.add_query(6, f"{d[1]}的资料收集完成了吗？", "task", "task_status", [("completed_mid", 3, "初始资料已完成"), ("status_far_unfinished", 2, "核心任务仍未完成")], "yes_no_status")
        self.add_query(7, f"{d[2]}那个过期事项现在应该怎么处理？", "task", "task_status", [("overdue_low", 3, "过期未完成"), ("overdue_constraint", 3, "不应覆盖高优先级任务")], "short_answer")
        self.add_query(8, f"{d[0]}为什么现在还不能最终完成？", "task", "task_context", [("main_dependency", 3, "说明前置依赖"), ("dependency_todo", 3, "需要协作者确认"), ("status_support_unfinished", 2, "支持材料未完成")], "short_answer")
        self.add_query(9, f"{d[3]}当前有效计划是什么？", "task", "task_context", [("new_valid_plan", 3, "新计划有效"), ("superseded_plan", 2, "旧计划被覆盖"), ("old_superseded_mu", 1, "旧 MU 干扰")], "short_answer")
        self.add_query(10, f"做{d[0]}前还缺什么依赖？", "task", "task_dependency", [("main_dependency", 3, "关键依赖"), ("dependency_todo", 3, "协作者确认"), ("today_plan_constraint", 2, "今日计划约束")], "short_answer")
        self.add_query(11, f"{d[1]}卡住的前置条件是什么？", "task", "task_dependency", [("far_dependency_detail", 3, "缺失输入"), ("missing_input", 3, "发现缺失输入"), ("mixed_dependency_pref", 2, "提醒中应说明依赖")], "short_answer")
        self.add_query(12, "我做计划时有什么稳定偏好？", "chat", "chat_preference", [("stable_preference", 3, "稳定偏好"), ("old_stable_preference", 3, "旧但稳定偏好"), ("reminder_pref", 2, "提醒偏好")], "short_answer")
        self.add_query(13, "关于深度工作时间，我现在应该遵循哪个偏好？", "chat", "chat_preference", [("new_preference", 3, "新偏好覆盖旧偏好"), ("preference_update_rule", 3, "说明新偏好优先"), ("old_preference", 1, "旧偏好干扰")], "short_answer")
        self.add_query(14, "我的背景和主要任务场景是什么？", "chat", "chat_profile", [("profile", 3, "用户画像"), ("main_fact", 2, "当前主项目事实")], "short_answer")
        self.add_query(15, "之前我提过哪些和提醒方式有关的要求？", "chat", "chat_history", [("reminder_pref", 3, "提醒解释偏好"), ("grouped_reminder_pref", 3, "按紧急度和依赖分组"), ("mixed_dependency_pref", 2, "依赖提醒偏好")], "short_answer")
        self.add_query(16, "帮我安排今天上午，结合任务优先级和个人偏好。", "chat", "mixed", [("today_plan_constraint", 3, "今日计划主约束"), ("today_plan_todo", 3, "今日任务"), ("new_preference", 3, "当前时间偏好"), ("due_support", 2, "近 ddl 任务")], "planning_suggestion")
        self.add_query(17, f"帮我写一个关于{d[1]}的提醒，要体现依赖关系。", "chat", "mixed", [("mixed_dependency_pref", 3, "提醒偏好"), ("far_dependency_detail", 3, "依赖内容"), ("mixed_dependency_todo", 2, "相关 todo")], "planning_suggestion")
        self.add_query(18, "我还有什么低优先级但今天可能会干扰我的事？", "task", "task_priority", [("urgent_wrong_domain", 3, "低价值近 ddl 干扰"), ("low_near", 2, "低重要近 ddl"), ("recent_irrelevant", 1, "最近但无关")], "ranked_tasks")
        self.add_query(19, f"那个类似{d[0]}的旧任务还需要今天做吗？", "task", "task_status", [("similar_done", 3, "语义相似但已完成"), ("due_main", 2, "真正未完成主任务")], "yes_no_status")
        self.add_query(20, "我有没有提过要学习法语考试？", "chat", "negative", [], "abstention", {"time_range": None, "entities": ["法语考试"], "keywords": ["有没有"]})

    def build(self):
        self.build_events()
        self.build_queries()
        return {
            "user_id": self.uid,
            "user_profile": {
                "background": self.config["persona"],
                "main_task_scenario": " / ".join(self.config["domains"]),
                "preferences": [self.config["preference"], self.config["updated_preference_new"]],
            },
            "now": NOW,
            "events": self.events,
            "memories": self.memories,
            "queries": self.queries,
        }


def validate(users):
    for user in users:
        event_ids = {e["event_id"] for e in user["events"]}
        memory_ids = {m["memory_id"] for m in user["memories"]}
        assert len(user["events"]) == 20, user["user_id"]
        assert len(user["queries"]) == 20, user["user_id"]
        assert 80 <= len(user["memories"]) <= 120, user["user_id"]
        assert len(event_ids) == len(user["events"]), user["user_id"]
        assert len(memory_ids) == len(user["memories"]), user["user_id"]
        for event in user["events"]:
            assert "event_value" not in event and "event_status" not in event
            assert set(event["memory_ids"]).issubset(memory_ids), event["event_id"]
        for memory in user["memories"]:
            assert memory["event_id"] in event_ids, memory["memory_id"]
            assert 0 <= memory["importance"] <= 1
            assert 0 <= memory["accessible_score"] <= 1
            if memory["memory_type"] == "todo":
                assert memory["ddl"] is not None
                assert memory["is_done"] in (True, False)
            else:
                assert memory["ddl"] is None
                assert memory["is_done"] is None
        for query in user["queries"]:
            if query["query_subtype"] != "negative":
                assert query["gold"], query["query_id"]
                assert query["gold_event_ids"], query["query_id"]
            for gold in query["gold"]:
                assert gold["memory_id"] in memory_ids


def write_summary(users):
    rows = []
    for user in users:
        type_counts = {}
        for memory in user["memories"]:
            type_counts[memory["memory_type"]] = type_counts.get(memory["memory_type"], 0) + 1
        rows.append(
            {
                "user_id": user["user_id"],
                "events": len(user["events"]),
                "memories": len(user["memories"]),
                "queries": len(user["queries"]),
                "todo": type_counts.get("todo", 0),
                "preference": type_counts.get("preference", 0),
                "profile": type_counts.get("profile", 0),
                "fact": type_counts.get("fact", 0),
                "habit": type_counts.get("habit", 0),
                "constraint": type_counts.get("constraint", 0),
                "dependency": type_counts.get("dependency", 0),
                "status_update": type_counts.get("status_update", 0),
            }
        )
    with OUT_SUMMARY.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    users = [Builder(config).build() for config in USERS]
    validate(users)
    OUT_JSONL.write_text("\n".join(json.dumps(user, ensure_ascii=False) for user in users) + "\n", encoding="utf-8")
    OUT_PRETTY.write_text(json.dumps(users, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(users)
    print(f"wrote {OUT_JSONL}")
    print(f"wrote {OUT_PRETTY}")
    print(f"wrote {OUT_SUMMARY}")
    print(f"users={len(users)} events={sum(len(u['events']) for u in users)} memories={sum(len(u['memories']) for u in users)} queries={sum(len(u['queries']) for u in users)}")


if __name__ == "__main__":
    main()
