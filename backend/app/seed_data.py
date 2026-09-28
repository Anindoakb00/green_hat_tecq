from .models import Account, IntentEvent


def seed_accounts() -> list[Account]:
    return [
        Account(
            id="acct-telstra",
            company_name="Telstra",
            industry="Telecommunications",
            target_tier="1:1",
            persona_type="Operations & Workforce",
            buying_stage="Prioritised",
            current_score=87.4,
            readiness_status="Qualified Demand",
            intent_events=[
                IntentEvent(id="evt-telstra-1", account_id="acct-telstra", event_type="Demo request", asset_name="Workforce optimisation demo", raw_weight=50, days_ago=1),
                IntentEvent(id="evt-telstra-2", account_id="acct-telstra", event_type="Pricing page visit", asset_name="Pricing", raw_weight=35, days_ago=4),
                IntentEvent(id="evt-telstra-3", account_id="acct-telstra", event_type="Case study view", asset_name="Customer outcomes", raw_weight=15, days_ago=8),
            ],
        ),
        Account(
            id="acct-schneider",
            company_name="Schneider Electric",
            industry="Energy & Automation",
            target_tier="1:Few",
            persona_type="Executive & Finance",
            buying_stage="Engaged",
            current_score=64.8,
            readiness_status="Engaged Demand",
            intent_events=[
                IntentEvent(id="evt-schneider-1", account_id="acct-schneider", event_type="Whitepaper download", asset_name="Energy efficiency guide", raw_weight=25, days_ago=2),
                IntentEvent(id="evt-schneider-2", account_id="acct-schneider", event_type="Webinar attendance", asset_name="Operational ROI briefing", raw_weight=20, days_ago=5),
                IntentEvent(id="evt-schneider-3", account_id="acct-schneider", event_type="Case study view", asset_name="Industrial efficiency", raw_weight=15, days_ago=7),
            ],
        ),
        Account(
            id="acct-atlassian",
            company_name="Atlassian",
            industry="Software",
            target_tier="1:Many",
            persona_type="OHS & Compliance",
            buying_stage="Target",
            current_score=31.2,
            readiness_status="Active Demand",
            intent_events=[
                IntentEvent(id="evt-atlassian-1", account_id="acct-atlassian", event_type="Blog visit", asset_name="Safer distributed teams", raw_weight=5, days_ago=3),
                IntentEvent(id="evt-atlassian-2", account_id="acct-atlassian", event_type="Social interaction", asset_name="Green Hat insights", raw_weight=5, days_ago=10),
            ],
        ),
    ]
