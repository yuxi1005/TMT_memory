import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_JSONL = ROOT / "data" / "pilot_v3_dataset.jsonl"
OUT_PRETTY = ROOT / "data" / "pilot_v3_dataset.pretty.json"
OUT_SUMMARY = ROOT / "data" / "pilot_v3_generation_summary.csv"

TZ = timezone(timedelta(hours=8))
NOW_DT = datetime(2026, 5, 6, 9, 0, tzinfo=TZ)
NOW = NOW_DT.isoformat()

DOMAINS = [
    ("thesis_ablation_report", "visa_renewal_forms", "writing_style"),
    ("beta_release_brief", "office_move_checklist", "status_update_format"),
    ("clinic_exam_review", "family_budget_sheet", "study_plan_format"),
    ("dashboard_metric_audit", "travel_booking_plan", "analysis_summary_style"),
    ("client_cover_art", "tax_receipt_cleanup", "client_message_style"),
    ("payment_bug_triage", "conference_slide_polish", "engineering_update_format"),
    ("moot_court_argument", "apartment_repair_plan", "case_note_format"),
    ("video_script_launch", "insurance_claim_packet", "script_structure_preference"),
    ("monthly_report_delivery", "birthday_party_plan", "dashboard_note_style"),
    ("vendor_contract_review", "fitness_training_log", "comparison_table_style"),
]


def iso_days_ago(days, hour=10, minute=0):
    return (NOW_DT - timedelta(days=days)).replace(hour=hour, minute=minute).isoformat()


def iso_days_from_now(days, hour=18, minute=0):
    return (NOW_DT + timedelta(days=days)).replace(hour=hour, minute=minute).isoformat()


class Builder:
    def __init__(self, user_index, primary, secondary, preference_topic):
        self.uid = f"v3u{user_index:03d}"
        self.primary = primary
        self.secondary = secondary
        self.preference_topic = preference_topic
        self.event_no = 0
        self.memory_no = 0
        self.query_no = 0
        self.events = []
        self.memories = []
        self.queries = []
        self.refs = {}

    def next_event_id(self):
        self.event_no += 1
        return f"{self.uid}_e{self.event_no:03d}"

    def next_memory_id(self):
        self.memory_no += 1
        return f"{self.uid}_m{self.memory_no:04d}"

    def add_event(self, title, days_ago, event_text, memory_specs):
        event_id = self.next_event_id()
        start = iso_days_ago(days_ago, 9 + (self.event_no % 8), 5)
        memory_ids = []
        for spec in memory_specs:
            memory_id = self.next_memory_id()
            memory = {
                "memory_id": memory_id,
                "content": spec["content"],
                "timestamp": spec.get("timestamp", start),
                "embedding": None,
                "event_id": event_id,
                "memory_type": spec["memory_type"],
                "ddl": spec.get("ddl"),
                "importance": round(float(spec.get("importance", 0.5)), 2),
                "accessible_score": round(float(spec.get("accessible_score", 0.5)), 2),
                "is_done": spec.get("is_done"),
                "domain": spec.get("domain"),
                "distractor_role": spec.get("distractor_role", ""),
                "temporal_bucket": spec.get("temporal_bucket", ""),
            }
            self.memories.append(memory)
            memory_ids.append(memory_id)
            if spec.get("ref"):
                self.refs[spec["ref"]] = memory_id
        self.events.append(
            {
                "event_id": event_id,
                "title": title,
                "time_range": {"start": start, "end": start},
                "event_text": event_text,
                "event_embedding": None,
                "memory_ids": memory_ids,
            }
        )

    def mem(self, ref, content, memory_type, domain, days_ago, importance, accessible_score, **kwargs):
        spec = {
            "ref": ref,
            "content": content,
            "memory_type": memory_type,
            "domain": domain,
            "timestamp": iso_days_ago(days_ago, kwargs.pop("hour", 10), kwargs.pop("minute", 0)),
            "importance": importance,
            "accessible_score": accessible_score,
        }
        spec.update(kwargs)
        return spec

    def add_query(self, tag, text, mode, subtype, gold_refs, answer_type):
        self.query_no += 1
        if subtype in {"chat_preference", "chat_profile", "chat_history"}:
            entities = ["profile"]
        elif subtype == "mixed":
            entities = [self.primary, "profile"]
        else:
            entities = [self.primary]
        refs = [(ref, relevance, reason) for ref, relevance, reason in gold_refs]
        gold = [{"memory_id": self.refs[ref], "relevance": relevance, "reason": reason} for ref, relevance, reason in refs]
        memory_to_event = {memory["memory_id"]: memory["event_id"] for memory in self.memories}
        gold_event_ids = []
        for ref, _, _ in refs:
            event_id = memory_to_event[self.refs[ref]]
            if event_id not in gold_event_ids:
                gold_event_ids.append(event_id)
        self.queries.append(
            {
                "query_id": f"{self.uid}_q{self.query_no:03d}",
                "query": text,
                "query_mode": mode,
                "query_subtype": subtype,
                "now": NOW,
                "hard_case_tag": tag,
                "constraints": {
                    "hard_case_tag": tag,
                    "entities": entities,
                    "keywords": text.split(),
                },
                "gold": gold,
                "gold_event_ids": gold_event_ids,
                "answer_type": answer_type,
            }
        )

    def build(self):
        p = self.primary
        s = self.secondary
        pref = self.preference_topic

        self.add_event(
            f"{p} active deadline set",
            1,
            f"Active planning for {p} with near, medium, and far deadline tasks.",
            [
                self.mem("near_task", f"Active todo for {p}: finish evidence_table before the near deadline.", "todo", p, 1, 0.95, 0.42, ddl=iso_days_from_now(1), is_done=False, distractor_role="near_deadline", temporal_bucket="recent"),
                self.mem("medium_task", f"Active todo for {p}: prepare reviewer_notes before the medium deadline.", "todo", p, 2, 0.85, 0.66, ddl=iso_days_from_now(10), is_done=False, distractor_role="medium_deadline", temporal_bucket="recent"),
                self.mem("far_task", f"Active todo for {p}: polish appendix_pack before the far deadline.", "todo", p, 4, 0.92, 0.98, ddl=iso_days_from_now(55), is_done=False, distractor_role="far_deadline", temporal_bucket="recent"),
                self.mem("task_dependency", f"For {p}, evidence_table must be completed before reviewer_notes and appendix_pack.", "dependency", p, 1, 0.78, 0.62, temporal_bucket="recent"),
                self.mem("task_constraint", f"{p} has a strict context rule: use only memories from {p}, not {s}.", "constraint", p, 1, 0.74, 0.6, temporal_bucket="recent"),
                self.mem("task_fact", f"{p} is the primary project this week.", "fact", p, 1, 0.7, 0.58, temporal_bucket="recent"),
            ],
        )

        self.add_event(
            f"{s} urgent wrong domain",
            0,
            f"Wrong-domain urgent distractors for {s}; recency and deadline are high but domain is wrong.",
            [
                self.mem("wrong_urgent_1", f"Active todo for {s}: finish evidence_table before the immediate deadline.", "todo", s, 0, 0.99, 0.99, ddl=iso_days_from_now(0, 12), is_done=False, distractor_role="wrong_domain", temporal_bucket="recent"),
                self.mem("wrong_urgent_2", f"Active todo for {s}: prepare reviewer_notes before tomorrow.", "todo", s, 0, 0.94, 0.94, ddl=iso_days_from_now(1, 10), is_done=False, distractor_role="wrong_domain", temporal_bucket="recent"),
                self.mem("wrong_status", f"{s} looks urgent but is unrelated to {p}.", "status_update", s, 0, 0.78, 0.9, distractor_role="wrong_domain", temporal_bucket="recent"),
                self.mem("wrong_constraint", f"Do not use {s} when the query asks about {p}.", "constraint", s, 0, 0.74, 0.88, distractor_role="wrong_domain", temporal_bucket="recent"),
                self.mem("wrong_fact", f"{s} shares words such as evidence_table, reviewer_notes, and deadline.", "fact", s, 0, 0.65, 0.9, distractor_role="wrong_domain", temporal_bucket="recent"),
                self.mem("wrong_noise", f"Recent side note for {s} with deadline language.", "fact", s, 0, 0.48, 0.86, distractor_role="wrong_domain", temporal_bucket="recent"),
            ],
        )

        self.add_event(
            f"{p} completed task distractors",
            2,
            f"Completed task records for {p}; useful for status but dangerous for open task queries.",
            [
                self.mem("completed_1", f"Completed todo for {p}: finish evidence_table draft before an old deadline.", "todo", p, 2, 0.96, 0.95, ddl=iso_days_from_now(0, 10), is_done=True, distractor_role="completed_task", temporal_bucket="recent"),
                self.mem("completed_2", f"Completed todo for {p}: prepare reviewer_notes outline.", "todo", p, 3, 0.9, 0.9, ddl=iso_days_from_now(1, 11), is_done=True, distractor_role="completed_task", temporal_bucket="recent"),
                self.mem("completed_status", f"The old {p} evidence_table draft is done and should not count as an open task.", "status_update", p, 2, 0.82, 0.86, distractor_role="completed_task", temporal_bucket="recent"),
                self.mem("open_status", f"The current unfinished item for {p} is the final evidence_table, not the completed draft.", "status_update", p, 1, 0.82, 0.55, temporal_bucket="recent"),
                self.mem("completed_fact", f"{p} has several completed todos that are semantically similar to active todos.", "fact", p, 2, 0.7, 0.82, distractor_role="completed_task", temporal_bucket="recent"),
                self.mem("completed_constraint", f"Completed {p} todos should be excluded when the user asks what remains open.", "constraint", p, 2, 0.72, 0.78, temporal_bucket="recent"),
            ],
        )

        self.add_event(
            f"current {pref}",
            1,
            f"Recent updated preference for {pref}.",
            [
                self.mem("new_pref", f"Updated preference for {pref}: user now wants concise checklist answers with short bullets.", "preference", "profile", 1, 0.88, 0.5, temporal_bucket="recent"),
                self.mem("new_pref_reason", f"The current {pref} preference favors checklist structure over narrative paragraphs.", "habit", "profile", 1, 0.76, 0.48, temporal_bucket="recent"),
                self.mem("new_pref_constraint", f"When using {pref}, avoid long narrative unless explicitly requested.", "constraint", "profile", 1, 0.72, 0.45, temporal_bucket="recent"),
                self.mem("new_pref_profile", f"User currently evaluates {pref} by clarity and scanability.", "profile", "profile", 1, 0.7, 0.42, temporal_bucket="recent"),
            ],
        )

        self.add_event(
            f"old {pref}",
            95,
            f"Stale preference record for {pref}; high accessibility but superseded.",
            [
                self.mem("old_pref", f"Old preference for {pref}: user wanted long narrative answers with detailed paragraphs.", "preference", "profile", 95, 0.84, 0.99, distractor_role="old_preference", temporal_bucket="old"),
                self.mem("old_pref_reason", f"Older {pref} notes preferred paragraph style and broad explanation.", "habit", "profile", 95, 0.72, 0.94, distractor_role="old_preference", temporal_bucket="old"),
                self.mem("old_pref_flag", f"This old preference for {pref} is likely superseded by the current checklist preference.", "constraint", "profile", 95, 0.68, 0.9, distractor_role="old_preference", temporal_bucket="old"),
                self.mem("stale_memory_1", f"Stale memory about {pref} uses the same keywords: concise checklist narrative paragraphs.", "fact", "profile", 150, 0.7, 0.93, distractor_role="stale_memory", temporal_bucket="stale"),
                self.mem("stale_memory_2", f"Very old {pref} memory from a different workflow.", "fact", "profile", 180, 0.62, 0.88, distractor_role="stale_memory", temporal_bucket="stale"),
            ],
        )

        self.add_event(
            f"{p} current plan",
            3,
            f"Current plan for {p}.",
            [
                self.mem("current_plan", f"Current plan for {p}: finish evidence_table first, then reviewer_notes, then appendix_pack.", "status_update", p, 3, 0.86, 0.48, temporal_bucket="recent"),
                self.mem("current_plan_reason", f"The current {p} plan prioritizes evidence_table because it blocks reviewer_notes.", "dependency", p, 3, 0.78, 0.46, temporal_bucket="recent"),
                self.mem("current_plan_constraint", f"For {p}, use the current plan rather than older ordering notes.", "constraint", p, 3, 0.74, 0.44, temporal_bucket="recent"),
                self.mem("current_plan_fact", f"{p} current plan was updated this week.", "fact", p, 3, 0.68, 0.42, temporal_bucket="recent"),
            ],
        )

        self.add_event(
            f"{p} old plan",
            120,
            f"Old plan for {p}; semantically close but outdated.",
            [
                self.mem("old_plan", f"Old plan for {p}: polish appendix_pack first, then evidence_table.", "fact", p, 120, 0.8, 0.98, distractor_role="old_plan", temporal_bucket="old"),
                self.mem("old_plan_reason", f"Older {p} plan assumed appendix_pack was the blocker.", "dependency", p, 120, 0.72, 0.92, distractor_role="old_plan", temporal_bucket="old"),
                self.mem("old_plan_flag", f"This old plan for {p} is superseded by the current plan.", "constraint", p, 120, 0.68, 0.88, distractor_role="old_plan", temporal_bucket="old"),
                self.mem("old_plan_noise", f"Stale {p} note repeats evidence_table reviewer_notes appendix_pack.", "fact", p, 150, 0.62, 0.86, distractor_role="stale_memory", temporal_bucket="stale"),
            ],
        )

        for index, days in enumerate([5, 8, 14, 21, 35, 60, 120, 180], start=1):
            role = "recent_noise" if days <= 14 else "stale_memory"
            bucket = "recent" if days <= 14 else "old" if days <= 120 else "stale"
            self.add_event(
                f"noise batch {index} for {p}",
                days,
                f"Noise batch {index} with lexical overlap for {p}, {s}, deadlines, preferences, and plans.",
                [
                    self.mem(f"noise_{index}_a", f"Noise memory for {p}: evidence_table deadline checklist but not answer evidence.", "fact", p, days, 0.5, 0.65, distractor_role=role, temporal_bucket=bucket),
                    self.mem(f"noise_{index}_b", f"Noise memory for {s}: reviewer_notes deadline urgent checklist.", "fact", s, days, 0.52, 0.7, distractor_role="wrong_domain" if days <= 14 else role, temporal_bucket=bucket),
                    self.mem(f"noise_{index}_c", f"Noise preference memory mentioning {pref}, checklist, narrative, current, old.", "preference", "profile", days, 0.48, 0.68, distractor_role=role, temporal_bucket=bucket),
                    self.mem(f"noise_{index}_d", f"Noise todo for {p}: low priority cleanup eventually.", "todo", p, days, 0.35, 0.52, ddl=iso_days_from_now(80 + index), is_done=False, distractor_role="far_deadline", temporal_bucket=bucket),
                    self.mem(f"noise_{index}_e", f"Noise status for {p}: not relevant to the current question.", "status_update", p, days, 0.42, 0.6, distractor_role=role, temporal_bucket=bucket),
                ],
            )

        self.add_query("tmt_deadline_order", f"For {p}, which active deadline task should be handled first?", "task", "task_due", [("near_task", 3, "Nearest active deadline."), ("task_dependency", 2, "Explains why this task blocks later work.")], "ranked_tasks")
        self.add_query("tmt_far_distractor", f"Rank active {p} todos by deadline, near before far.", "task", "task_due", [("near_task", 3, "Near deadline."), ("medium_task", 2, "Medium deadline."), ("far_task", 1, "Far but still relevant.")], "ranked_tasks")
        self.add_query("domain_wrong_urgent", f"What is due for {p}, ignoring urgent {s} items?", "task", "task_due", [("near_task", 3, "Correct domain near deadline."), ("medium_task", 2, "Correct domain medium deadline.")], "ranked_tasks")
        self.add_query("penalty_completed_task", f"What open {p} evidence_table work remains unfinished?", "task", "task_due", [("near_task", 3, "Open current todo."), ("open_status", 2, "Clarifies completed draft is not the open task.")], "ranked_tasks")
        self.add_query("decay_current_preference", f"What is the user's current {pref} preference?", "chat", "chat_preference", [("new_pref", 3, "Current preference."), ("new_pref_reason", 2, "Current reason.")], "short_answer")
        self.add_query("penalty_old_preference", f"Use the latest {pref} preference and ignore old narrative preference.", "chat", "chat_preference", [("new_pref", 3, "Latest preference."), ("new_pref_constraint", 2, "Says avoid long narrative.")], "short_answer")
        self.add_query("decay_current_plan", f"What is the current plan for {p}?", "task", "task_context", [("current_plan", 3, "Current plan."), ("current_plan_reason", 2, "Current dependency.")], "short_answer")
        self.add_query("compatibility_chat_intrusion", f"How should responses use {pref} for this user?", "chat", "chat_preference", [("new_pref", 3, "Preference answer."), ("new_pref_profile", 2, "Profile-style support.")], "short_answer")
        self.add_query("task_status_completed_contrast", f"Is the {p} evidence_table done or still open?", "task", "task_status", [("open_status", 3, "Current open status."), ("completed_status", 2, "Completed draft contrast.")], "yes_no_status")
        self.add_query("task_dependency_current", f"What blocks reviewer_notes for {p}?", "task", "task_dependency", [("task_dependency", 3, "Evidence table blocks reviewer notes."), ("current_plan_reason", 3, "Current dependency.")], "short_answer")
        self.add_query("mixed_plan_preference", f"Plan {p} using the user's current {pref} preference.", "chat", "mixed", [("current_plan", 3, "Task plan."), ("new_pref", 3, "Current preference."), ("near_task", 2, "Near deadline.")], "planning_suggestion")
        self.add_query("negative_unknown_domain", f"What is due for unrelated_quantum_pet_project?", "chat", "negative", [], "abstention")
        self.add_query("stale_memory_filter", f"Which {p} plan is current, not the old appendix-first plan?", "task", "task_context", [("current_plan", 3, "Current plan."), ("old_plan_flag", 1, "Warning that old plan is superseded.")], "short_answer")
        self.add_query("wrong_domain_status", f"Give status for {p}, not {s}.", "task", "task_status", [("current_plan", 3, "Correct domain status."), ("open_status", 2, "Correct domain open status.")], "short_answer")
        self.add_query("profile_stable_old", f"What stable formatting habit should I remember for {pref}?", "chat", "chat_profile", [("new_pref_profile", 3, "Current stable profile."), ("new_pref_reason", 2, "Current habit.")], "short_answer")
        self.add_query("noise_resilience", f"Find the relevant {p} evidence_table memory despite deadline checklist noise.", "task", "task_context", [("near_task", 3, "Relevant evidence table todo."), ("task_fact", 2, "Primary project fact.")], "short_answer")
        self.add_query("completed_intrusion_check", f"Do not include completed {p} todos; what remains active?", "task", "task_due", [("near_task", 3, "Active todo."), ("medium_task", 2, "Active todo.")], "ranked_tasks")
        self.add_query("old_preference_intrusion_check", f"Do not use old {pref} paragraphs; what is the current format?", "chat", "chat_preference", [("new_pref", 3, "Current checklist preference."), ("new_pref_constraint", 2, "Avoid narrative.")], "short_answer")

        return {
            "user_id": self.uid,
            "user_profile": {
                "background": f"Pilot v3 synthetic user with primary domain {p}.",
                "main_task_scenario": f"{p} with dense distractors from {s}.",
                "preferences": [f"Current {pref}: concise checklist answers with short bullets."],
            },
            "now": NOW,
            "events": self.events,
            "memories": self.memories,
            "queries": self.queries,
        }


def build_users():
    users = []
    for index in range(1, 31):
        primary, secondary, pref = DOMAINS[(index - 1) % len(DOMAINS)]
        users.append(Builder(index, f"{primary}_{index:02d}", f"{secondary}_{index:02d}", f"{pref}_{index:02d}").build())
    return users


def main():
    users = build_users()
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8", newline="\n") as handle:
        for user in users:
            handle.write(json.dumps(user, ensure_ascii=False) + "\n")
    OUT_PRETTY.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "users": len(users),
        "events": sum(len(user["events"]) for user in users),
        "memories": sum(len(user["memories"]) for user in users),
        "queries": sum(len(user["queries"]) for user in users),
        "hard_queries": sum(1 for user in users for query in user["queries"] if query.get("hard_case_tag")),
    }
    with OUT_SUMMARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)
    print(summary)
    print(f"wrote {OUT_JSONL}")


if __name__ == "__main__":
    main()
