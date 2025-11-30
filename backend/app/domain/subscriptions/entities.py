from dataclasses import dataclass
from decimal import Decimal
from app.domain.common.entities import Entity

@dataclass
class SubscriptionPlan(Entity):
    name: str
    price: Decimal
    duration_months: int
    description: str | None = None
