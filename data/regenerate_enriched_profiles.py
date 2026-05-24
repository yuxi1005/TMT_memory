import json
from pathlib import Path


SRC = Path("long_memory_benchmark_user_profiles.json")
OUT = Path("long_memory_benchmark_user_profiles_enriched_utf8_bom.json")


MEMORY_STYLES = [
    "清单化、夹杂少量口语提醒，常用“待做/已做/先不管”区分状态。",
    "碎片化灵感笔记，喜欢保留旧方案和新方案的对比。",
    "任务导向的短句记录，常把人名、截止时间和优先级写在一起。",
    "正式总结式记录，偏爱把假设、实验、结论和下一步分开写。",
    "反思型口语记录，容易把情绪状态和研究任务写在同一条里。",
    "半句笔记加关键词，重视症状、数据、对象和复查时间。",
]

STATES_BY_PREFIX = {
    "S": ["active", "completed", "overdue", "postponed", "stale"],
    "P": ["active", "completed", "blocked", "cancelled", "postponed"],
    "L": ["active", "completed", "overdue", "recurring", "stale"],
}

LIFE_STAGE_TEMPLATES = {
    "S": "{main0}和{main1}并行推进期，需要在学业产出、申请准备和个人状态之间频繁切换。",
    "P": "{main0}交付和{main1}协作密集期，工作计划常被会议、版本变化和临时沟通打断。",
    "L": "{main0}与{main1}持续经营期，日常事务、家庭安排和个人偏好变化会反复进入记忆。",
}

STABLE_POOL = {
    "S": [
        "偏好结构化步骤和可执行清单",
        "希望解释保留关键依据而不是只给结论",
        "更信任能标注当前状态和截止时间的建议",
        "喜欢把学习、申请和生活事项分开归档",
    ],
    "P": [
        "偏好可直接复制到文档或会议纪要的输出",
        "重视优先级、负责人和下一步动作",
        "希望 agent 主动指出旧计划和当前计划的差异",
        "喜欢简洁、面向决策的总结",
    ],
    "L": [
        "偏好口语化但可追踪的记录方式",
        "重视时间、地点、对象和当前状态",
        "希望建议贴近日常执行而不是过度宏观",
        "喜欢把重复事项和一次性想法区分开",
    ],
}

EXTRA_DOMAINS = {
    "S": ["作息与健康", "情绪压力", "社交与娱乐"],
    "P": ["会议沟通", "家庭与个人安排", "健康作息"],
    "L": ["家庭事务", "消费与娱乐", "健康与情绪"],
}


def unique_take(items, limit):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
        if len(result) >= limit:
            break
    return result


def enrich_one(seed, index):
    uid = seed["user_id"]
    prefix = uid[0]
    mains = seed.get("main_domains", [])
    uses = seed.get("agent_use_cases", [])
    noise = seed.get("common_noise_sources", [])

    main0 = mains[0] if len(mains) > 0 else seed.get("domain_or_industry", "核心事务")
    main1 = mains[1] if len(mains) > 1 else seed.get("specific_identity", "长期任务")
    main2 = mains[2] if len(mains) > 2 else "个人事务"
    use0 = uses[0] if uses else "任务拆解"
    use1 = uses[1] if len(uses) > 1 else "资料整理"
    noise0 = noise[0] if noise else "临时想法"
    noise1 = noise[1] if len(noise) > 1 else "情绪波动"

    life_stage = LIFE_STAGE_TEMPLATES.get(prefix, LIFE_STAGE_TEMPLATES["L"]).format(
        main0=main0,
        main1=main1,
    )

    return {
        "user_id": uid,
        "macro_archetype": seed["macro_archetype"],
        "user_archetype": f"{seed['level_or_role']} / {seed['domain_or_industry']} 高频 agent 用户",
        "concrete_identity": (
            f"{seed['specific_identity']}，处在{life_stage}"
            f"主要依赖 AI agent 处理{use0}、{use1}，但经常被{noise0}和{noise1}分散注意力。"
        ),
        "life_stage": life_stage,
        "agent_usage_level": "高频使用：几乎每天在工作/学习任务中调用，也会把生活琐事、临时想法和情绪记录交给 agent 整理。",
        "agent_usage_style": [
            f"用 agent 做{use0}，希望得到可直接执行的步骤。",
            f"把{use1}交给 agent 初步整理，再自己筛选和改写。",
            f"围绕{main0}和{main1}维护待办、计划和复盘记录。",
            f"偶尔把{noise0}、{noise1}等生活噪音也写进同一套记录系统。",
        ],
        "main_life_domains": unique_take(mains + EXTRA_DOMAINS.get(prefix, []), 6),
        "primary_goals": [
            f"稳定推进{main0}并减少重复返工。",
            f"把{main1}相关任务拆成可追踪的阶段计划。",
            f"在{main2}和个人生活噪音之间保持优先级清晰。",
        ],
        "stable_preferences": STABLE_POOL.get(prefix, STABLE_POOL["L"]),
        "dynamic_preferences": [
            f"对{main0}的优先级会随近期截止时间调整",
            f"对{use0}的输出格式会在简版和详细版之间切换",
            f"受{noise0}影响，短期关注点容易偏移",
            f"对{main1}的计划可能被新信息或他人反馈替换",
        ],
        "recurring_tasks": [
            f"定期推进{main0}相关任务",
            f"整理{main1}的材料和下一步",
            f"让 agent 协助{use0}",
            f"复盘{use1}产生的待办",
            f"清理{noise0}带来的临时记录",
        ],
        "typical_noise_sources": unique_take(
            noise + ["临时购物或娱乐想法", "健康作息波动", "短期焦虑和情绪记录"],
            5,
        ),
        "memory_style": MEMORY_STYLES[index % len(MEMORY_STYLES)],
        "likely_task_states": STATES_BY_PREFIX.get(prefix, STATES_BY_PREFIX["L"]),
        "likely_plan_changes": [
            f"{main0}的大计划被拆小或延后。",
            f"{main1}的旧方案被新反馈替代。",
            f"{use0}相关任务因为{noise0}或外部截止时间改变优先级。",
        ],
        "likely_hard_negatives": [
            f"关于{main0}的旧计划或已完成 todo。",
            f"语义相似但属于{main1}而不是当前任务的记录。",
            f"由{noise0}触发的临时偏好或过期想法。",
        ],
    }


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    profiles = []
    for index, seed in enumerate(data["user_profile_seeds"]):
        profiles.append(enrich_one(seed, index))
        print(f"enriched {seed['user_id']}")

    enriched = {
        "benchmark_context": data.get("benchmark_context", {}),
        "user_profiles": profiles,
    }
    OUT.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print(f"wrote {OUT} with {len(profiles)} profiles")


if __name__ == "__main__":
    main()
