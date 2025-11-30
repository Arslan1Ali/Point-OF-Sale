import asyncio
import pathlib
import sys
from decimal import Decimal

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

async def main() -> None:
    from app.infrastructure.db.session import async_session_factory
    from app.infrastructure.db.models.subscription_plan_model import SubscriptionPlanModel
    from app.domain.common.identifiers import new_ulid
    from sqlalchemy import select

    plans = [
        {
            "name": "Standard",
            "price": Decimal("10.00"),
            "duration_months": 1,
            "description": "Standard Monthly Plan"
        },
        {
            "name": "Premium",
            "price": Decimal("50.00"),
            "duration_months": 6,
            "description": "Premium 6-Month Plan"
        },
        {
            "name": "Exclusive",
            "price": Decimal("100.00"),
            "duration_months": 12,
            "description": "Exclusive Yearly Plan"
        }
    ]

    async with async_session_factory() as session:
        for plan_data in plans:
            stmt = select(SubscriptionPlanModel).where(SubscriptionPlanModel.name == plan_data["name"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                plan = SubscriptionPlanModel(
                    id=new_ulid(),
                    **plan_data
                )
                session.add(plan)
                print(f"Created plan: {plan_data['name']}")
            else:
                print(f"Plan already exists: {plan_data['name']}")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
