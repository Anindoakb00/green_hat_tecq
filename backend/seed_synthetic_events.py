"""Demo-only synthetic buyer activity seeder.

This intentionally creates simulated records for demonstrations. It must not be
used as production intent data. Run from backend/ with:
    python seed_synthetic_events.py
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dotenv import load_dotenv
from supabase import Client, create_client

from app.scoring import calculate_intent_score
from app.models import IntentEvent

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_SOURCE = "synthetic-demo"


def main() -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    owner_id = os.getenv("SUPABASE_OWNER_USER_ID")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    if not owner_id:
        raise RuntimeError("SUPABASE_OWNER_USER_ID is required")

    client: Client = create_client(url, key)
    accounts = [
        {"name": "Apex Mining", "industry": "Mining & Resources", "target_tier": "1:1"},
        {"name": "BuildCorp", "industry": "Construction", "target_tier": "1:Few"},
        {"name": "TransPacific", "industry": "Logistics & Transport", "target_tier": "1:Many"},
    ]
    now = datetime.now(timezone.utc)
    event_plan = {
        "Apex Mining": [("pricing_page_visit", 35, 0), ("demo_request", 50, 1), ("whitepaper_download", 25, 2)],
        "BuildCorp": [("whitepaper_download", 25, 1), ("webinar_attendance", 20, 2), ("case_study_view", 15, 4)],
        "TransPacific": [("blog_visit", 5, 2), ("social_interaction", 5, 5), ("whitepaper_download", 25, 7)],
    }
    for definition in accounts:
        existing = client.table("accounts").select("id").eq("agency_user_id", owner_id).eq("name", definition["name"]).execute().data or []
        if existing:
            account_id = existing[0]["id"]
            client.table("intent_events").delete().eq("account_id", account_id).eq("source", DEMO_SOURCE).execute()
            client.table("accounts").update({"industry": definition["industry"], "target_tier": definition["target_tier"], "current_score": 0}).eq("id", account_id).execute()
        else:
            created = client.table("accounts").insert({**definition, "agency_user_id": owner_id}).execute().data[0]
            account_id = created["id"]
        rows = []
        score_events = []
        for event_type, weight, days_ago in event_plan[definition["name"]]:
            timestamp = now - timedelta(days=days_ago)
            rows.append({"id": str(uuid4()), "account_id": account_id, "source": DEMO_SOURCE, "event_type": event_type, "weight": weight, "timestamp": timestamp.isoformat()})
            score_events.append(IntentEvent(account_id=account_id, source=DEMO_SOURCE, event_type=event_type, weight=weight, timestamp=timestamp))
        client.table("intent_events").insert(rows).execute()
        score = calculate_intent_score(score_events, now=now)
        client.table("accounts").update({"current_score": score}).eq("id", account_id).execute()
        print(f"Seeded {definition['name']}: {len(rows)} synthetic events, score {score}")
    print("Synthetic demo seeding complete. These records are labeled synthetic-demo.")


if __name__ == "__main__":
    main()
