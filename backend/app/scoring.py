import math
from datetime import datetime, timezone
from collections.abc import Iterable
from .models import IntentEvent
DECAY_RATE = 0.05
def calculate_intent_score(events: Iterable[IntentEvent], now: datetime | None = None) -> float:
    ref = now or datetime.now(timezone.utc); total = 0.0
    for event in events:
        stamp = event.timestamp if event.timestamp.tzinfo else event.timestamp.replace(tzinfo=timezone.utc)
        total += event.weight * math.exp(-DECAY_RATE * max(0, (ref - stamp).total_seconds() / 86400))
    return round(min(100.0, max(0.0, total)), 2)
