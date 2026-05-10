import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "toy_dataset_5users.jsonl"
OUT_JSONL = ROOT / "toy_dataset_5users_expanded.jsonl"
OUT_PRETTY = ROOT / "toy_dataset_5users_expanded.pretty.json"


DISTRACTORS = {
    "u001": [
        ("Library Book Return", "User discussed returning library books and renewing a campus library card.", "closed", 0.28),
        ("Coffee Chat Scheduling", "User planned a casual coffee chat with a classmate about weekend plans.", "dormant", 0.24),
        ("Phone Storage Cleanup", "User talked about deleting duplicate photos and organizing phone storage.", "closed", 0.22),
        ("Apartment Utility Bill", "User planned to check an apartment utility bill and split payment with roommates.", "active", 0.35),
        ("Movie Watchlist", "User mentioned several science fiction movies to watch after finals.", "dormant", 0.18),
    ],
    "u002": [
        ("Office Snack Order", "User discussed ordering snacks for the office pantry and comparing delivery options.", "closed", 0.25),
        ("Team Birthday Card", "User planned a birthday card message for a teammate.", "dormant", 0.2),
        ("Laptop Replacement Notes", "User considered replacing an old laptop and comparing hardware specs.", "active", 0.33),
        ("Conference Hotel Ideas", "User browsed hotel ideas for a future product conference.", "dormant", 0.22),
        ("Expense Receipt Cleanup", "User planned to organize old taxi and meal receipts.", "closed", 0.27),
    ],
    "u003": [
        ("Desk Plant Care", "User talked about watering desk plants and moving them away from direct sun.", "dormant", 0.19),
        ("Brush Pack Trial", "User tried a new digital brush pack and noted some texture preferences.", "active", 0.36),
        ("Old Invoice Archive", "User planned to archive old invoices from completed client projects.", "closed", 0.3),
        ("Friend's Party Poster", "User casually discussed making a poster for a friend's small party.", "dormant", 0.26),
        ("Recipe Sketch Idea", "User mentioned sketching ingredients from a pasta recipe for fun.", "dormant", 0.17),
    ],
    "u004": [
        ("Laundry Pickup", "User talked about picking up laundry after a long hospital shift.", "closed", 0.18),
        ("Podcast Queue", "User mentioned medical podcasts to listen to during commuting.", "dormant", 0.21),
        ("Phone Plan Renewal", "User discussed renewing a phone plan and checking data usage.", "active", 0.3),
        ("Old Notes Archive", "User planned to archive old lecture notes that are not part of current exam prep.", "closed", 0.24),
        ("Kitchen Supplies", "User listed kitchen supplies to buy sometime this month.", "dormant", 0.2),
    ],
    "u005": [
        ("Gym Membership Renewal", "User discussed whether to renew a gym membership after the office move.", "active", 0.31),
        ("Personal Photo Backup", "User planned to back up personal travel photos to an external drive.", "closed", 0.23),
        ("Team Lunch Poll", "User mentioned creating a poll for a casual team lunch.", "dormant", 0.2),
        ("Old Desk Donation", "User considered donating an old desk but did not set a firm deadline.", "dormant", 0.28),
        ("Newsletter Cleanup", "User talked about unsubscribing from old vendor newsletters.", "closed", 0.19),
    ],
}


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_memory(user_id, event_id, index, title, status, value):
    base = f"{user_id}_d{index:03d}"
    done = status == "closed"
    return [
        {
            "memory_id": f"{base}_m001",
            "content": f"User mentioned: {title.lower()}.",
            "timestamp": f"2026-04-{18 + index:02d}T10:00:00+08:00",
            "embedding": None,
            "event_id": event_id,
            "memory_type": "fact",
            "ddl": None,
            "importance": round(max(0.2, value + 0.08), 2),
            "accessible_score": round(max(0.15, value + 0.03), 2),
            "is_done": None,
        },
        {
            "memory_id": f"{base}_m002",
            "content": f"User treated {title.lower()} as a low-priority side matter.",
            "timestamp": f"2026-04-{18 + index:02d}T10:06:00+08:00",
            "embedding": None,
            "event_id": event_id,
            "memory_type": "preference",
            "ddl": None,
            "importance": round(value, 2),
            "accessible_score": round(max(0.12, value - 0.02), 2),
            "is_done": None,
        },
        {
            "memory_id": f"{base}_m003",
            "content": f"User {'completed' if done else 'may later revisit'} the side task about {title.lower()}.",
            "timestamp": f"2026-04-{18 + index:02d}T10:12:00+08:00",
            "embedding": None,
            "event_id": event_id,
            "memory_type": "todo",
            "ddl": f"2026-05-{10 + index:02d}T18:00:00+08:00" if not done else f"2026-04-{24 + index:02d}T18:00:00+08:00",
            "importance": round(max(0.2, value + 0.04), 2),
            "accessible_score": round(max(0.12, value), 2),
            "is_done": done,
        },
    ]


def expand_user(user):
    expanded = deepcopy(user)
    existing_count = len(expanded["events"])
    for offset, (title, text, status, value) in enumerate(DISTRACTORS[expanded["user_id"]], start=1):
        index = existing_count + offset
        event_id = f"{expanded['user_id']}_e{index:03d}"
        memories = make_memory(expanded["user_id"], event_id, index, title, status, value)
        event = {
            "event_id": event_id,
            "title": title,
            "time_range": {
                "start": f"2026-04-{18 + offset:02d}T10:00:00+08:00",
                "end": f"2026-04-{18 + offset:02d}T10:25:00+08:00",
            },
            "event_text": text,
            "event_embedding": None,
            "memory_ids": [memory["memory_id"] for memory in memories],
            "event_value": value,
            "event_status": status,
        }
        expanded["events"].append(event)
        expanded["memories"].extend(memories)
    return expanded


def main():
    users = load_jsonl(SOURCE)
    expanded = [expand_user(user) for user in users]
    OUT_JSONL.write_text(
        "\n".join(json.dumps(user, ensure_ascii=False) for user in expanded) + "\n",
        encoding="utf-8",
    )
    OUT_PRETTY.write_text(
        json.dumps(expanded, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_JSONL}")
    print(f"wrote {OUT_PRETTY}")


if __name__ == "__main__":
    main()
