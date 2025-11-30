from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.db.session import get_session
from app.api.dependencies.auth import get_current_user
from app.domain.auth.entities import UserRole, User
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.subscription_plan_model import SubscriptionPlanModel
from app.domain.common.identifiers import new_ulid

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.get("/plans")
async def get_subscription_plans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    stmt = select(SubscriptionPlanModel)
    result = await db.execute(stmt)
    plans = result.scalars().all()
    return plans

@router.get("/")
async def get_tenants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    stmt = select(TenantModel)
    result = await db.execute(stmt)
    tenants = result.scalars().all()
    return tenants

@router.post("/")
async def create_tenant(
    name: str,
    subscription_plan_id: str,
    domain: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if plan exists
    plan = await db.get(SubscriptionPlanModel, subscription_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")

    tenant = TenantModel(
        id=new_ulid(),
        name=name,
        domain=domain,
        subscription_plan_id=subscription_plan_id
    )
    db.add(tenant)
    try:
        await db.commit()
        await db.refresh(tenant)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return tenant
