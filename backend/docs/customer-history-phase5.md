# Phase 5 – Customer History & Insights (2025-10-19)

## Completed Actions
- **Customer Lifetime Summary**: Added `GET /api/v1/customers/{customer_id}/summary` delivering purchase totals, quantity, currency, last purchase identifiers, and temporal bounds for authorised sales/auditor roles.
- **Aggregate Pipeline**: Extended the sales repository with a `get_customer_sales_summary` aggregate that coalesces lifetime metrics without materialising every sale row and keeps currency/context for the latest order.
- **Use Case Orchestration**: Introduced `GetCustomerSummaryUseCase` to validate customer existence, compute averages, and expose a typed result for API and future desktop reuse.
- **Schema + Tests**: Published `CustomerSummaryOut` DTO and expanded the integration suite (`test_customers_api.py`) with authentication and happy-path assertions covering totals, averages, and last-sale linkage.

## Usage
```http
GET /api/v1/customers/{customer_id}/summary
Authorization: Bearer <token>
```

Sample response:
```json
{
  "customer_id": "01JF7B0PS3S2TQJZ8EZH4E4SXE",
  "currency": "USD",
  "total_sales": 12,
  "total_quantity": 37,
  "lifetime_value": "842.50",
  "average_order_value": "70.21",
  "first_purchase_at": "2025-09-01T12:24:55.918000+00:00",
  "last_purchase_at": "2025-10-19T05:44:02.337000+00:00",
  "last_sale_id": "01JF7B0Q0XZ5XYR5V1X80T5HVT",
  "last_sale_amount": "45.00"
}
```

Pairs with `/customers/{id}/sales` when the client needs paginated detail; the summary stays lightweight for dashboards and loyalty prompts.

## Follow-Up Backlog
1. **Multi-Currency Handling**: Surface per-currency breakdowns when customers purchase under multiple tenders; today the lifetime value assumes a single currency.
2. **Returns & Adjustments**: Deduct refunded totals once the returns domain exposes a reconciliation view, ensuring net lifetime value is accurate.
3. **Engagement Signals**: Add fields for `days_since_last_purchase` and `average_days_between_orders` to support churn detection inside the desktop client.
4. **Event Hooks**: Emit a domain event when the summary crosses configurable spend thresholds to trigger CRM automations.
5. **Materialised Snapshot**: Consider nightly materialisation or caching for large datasets to avoid repeated aggregation on high-volume customers.

Phase 5 deliverables are complete; ready to advance to Phase 6 once stakeholders sign off on the customer insight contract and desktop integration begins.
