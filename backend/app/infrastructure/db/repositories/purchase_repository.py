from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.purchases.ports import PurchaseRepository, SupplierPurchaseSummary
from app.domain.common.money import Money
from app.domain.purchases import PurchaseOrder, PurchaseOrderItem
from app.infrastructure.db.models.purchase_model import PurchaseOrderItemModel, PurchaseOrderModel


class SqlAlchemyPurchaseRepository(PurchaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_purchase(self, order: PurchaseOrder, items: Sequence[PurchaseOrderItem]) -> None:
        if not items:
            raise ValueError("Purchase must include items to persist")

        created_at = order.created_at
        model = PurchaseOrderModel(
            id=order.id,
            supplier_id=order.supplier_id,
            currency=order.currency,
            total_amount=order.total_amount.amount,
            total_quantity=order.total_quantity,
            created_at=created_at,
            received_at=order.received_at,
            items=[
                PurchaseOrderItemModel(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_cost=item.unit_cost.amount,
                    line_total=item.line_total.amount,
                    created_at=created_at,
                )
                for item in items
            ],
        )
        self._session.add(model)
        await self._session.flush()

    async def get_purchase(self, purchase_id: str) -> PurchaseOrder | None:
        stmt = (
            select(PurchaseOrderModel)
            .options(selectinload(PurchaseOrderModel.items))
            .where(PurchaseOrderModel.id == purchase_id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_purchase(model)

    async def list_purchases(
        self,
        *,
        supplier_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[PurchaseOrder], int]:
        stmt = select(PurchaseOrderModel).options(selectinload(PurchaseOrderModel.items))
        count_stmt = select(func.count(PurchaseOrderModel.id))

        if supplier_id:
            stmt = stmt.where(PurchaseOrderModel.supplier_id == supplier_id)
            count_stmt = count_stmt.where(PurchaseOrderModel.supplier_id == supplier_id)

        stmt = stmt.order_by(PurchaseOrderModel.created_at.desc()).offset(offset).limit(limit)

        rows_result = await self._session.execute(stmt)
        rows = rows_result.scalars().all()
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar_one()
        purchases: list[PurchaseOrder] = []
        for row in rows:
            purchase = self._to_purchase(row)
            if purchase is not None:
                purchases.append(purchase)
        return purchases, int(total)

    async def get_supplier_purchase_summary(self, supplier_id: str) -> SupplierPurchaseSummary:
        open_case = case((PurchaseOrderModel.received_at.is_(None), 1), else_=0)
        summary_stmt = (
            select(
                func.count(PurchaseOrderModel.id),
                func.coalesce(func.sum(PurchaseOrderModel.total_amount), 0),
                func.coalesce(func.sum(PurchaseOrderModel.total_quantity), 0),
                func.min(PurchaseOrderModel.created_at),
                func.max(PurchaseOrderModel.created_at),
                func.coalesce(func.sum(open_case), 0),
            )
            .where(PurchaseOrderModel.supplier_id == supplier_id)
        )
        result = await self._session.execute(summary_stmt)
        total_orders, total_amount, total_quantity, first_order_at, last_order_at, open_orders = result.one()

        total_orders_int = int(total_orders or 0)
        total_quantity_int = int(total_quantity or 0)
        total_amount_decimal = Decimal(total_amount or 0).quantize(Decimal("0.01"))
        open_orders_int = int(open_orders or 0)

        currency: str | None = None
        last_order_id: str | None = None
        last_order_amount: Decimal | None = None

        if total_orders_int > 0:
            last_stmt = (
                select(
                    PurchaseOrderModel.id,
                    PurchaseOrderModel.currency,
                    PurchaseOrderModel.total_amount,
                )
                .where(PurchaseOrderModel.supplier_id == supplier_id)
                .order_by(PurchaseOrderModel.created_at.desc())
                .limit(1)
            )
            last_result = await self._session.execute(last_stmt)
            last_row = last_result.first()
            if last_row is not None:
                last_order_id = last_row[0]
                currency = last_row[1]
                last_amount = last_row[2]
                last_order_amount = Decimal(last_amount).quantize(Decimal("0.01"))

        lead_stmt = (
            select(PurchaseOrderModel.created_at, PurchaseOrderModel.received_at)
            .where(PurchaseOrderModel.supplier_id == supplier_id)
            .where(PurchaseOrderModel.received_at.is_not(None))
        )
        lead_result = await self._session.execute(lead_stmt)
        lead_rows = lead_result.all()

        average_lead_time_hours: Decimal | None = None
        if lead_rows:
            total_seconds = Decimal("0")
            valid_count = 0
            for created_at, received_at in lead_rows:
                if received_at is None:
                    continue
                delta = received_at - created_at
                seconds = Decimal(str(delta.total_seconds()))
                if seconds < 0:
                    continue
                total_seconds += seconds
                valid_count += 1
            if valid_count > 0:
                avg_seconds = total_seconds / Decimal(valid_count)
                average_lead_time_hours = (avg_seconds / Decimal("3600")).quantize(Decimal("0.01"))

        average_currency = currency
        return SupplierPurchaseSummary(
            currency=average_currency,
            total_orders=total_orders_int,
            total_amount=total_amount_decimal,
            total_quantity=total_quantity_int,
            first_order_at=first_order_at,
            last_order_at=last_order_at,
            last_order_id=last_order_id,
            last_order_amount=last_order_amount,
            open_orders=open_orders_int,
            average_lead_time_hours=average_lead_time_hours,
        )

    def _to_purchase(self, model: PurchaseOrderModel | None) -> PurchaseOrder | None:
        if model is None:
            return None
        purchase = PurchaseOrder(
            id=model.id,
            supplier_id=model.supplier_id,
            currency=model.currency,
            created_at=model.created_at,
            received_at=model.received_at,
        )
        for item_model in model.items:
            item = PurchaseOrderItem(
                id=item_model.id,
                product_id=item_model.product_id,
                quantity=item_model.quantity,
                unit_cost=Money(item_model.unit_cost, purchase.currency),
                line_total=Money(item_model.line_total, purchase.currency),
            )
            purchase.items.append(item)
        return purchase
