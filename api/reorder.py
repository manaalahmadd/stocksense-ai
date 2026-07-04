from sqlalchemy.orm import Session
from models import Product
from forecasting import forecast_demand


def calculate_reorder(db: Session, product_id: int) -> dict:
    """Determine if and when a product needs reordering, based on forecasted
    demand, current stock, and supplier lead time."""

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}

    forecast_result = forecast_demand(db, product_id, days_ahead=30)
    forecast = forecast_result["forecast"]

    current_stock = product.current_stock
    lead_time = product.supplier_lead_time_days

    running_stock = current_stock
    days_until_stockout = None

    for i, day in enumerate(forecast):
        running_stock -= day["predicted_demand"]
        if running_stock <= 0 and days_until_stockout is None:
            days_until_stockout = i + 1

    avg_daily_demand = sum(d["predicted_demand"] for d in forecast) / len(forecast)

    safety_buffer_days = 3
    reorder_point = avg_daily_demand * (lead_time + safety_buffer_days)

    needs_reorder = current_stock <= reorder_point

    suggested_order_qty = max(0, round((avg_daily_demand * 30) - current_stock))

    if days_until_stockout is not None:
        if days_until_stockout <= lead_time:
            urgency = "critical"
        elif days_until_stockout <= lead_time + 7:
            urgency = "warning"
        else:
            urgency = "ok"

        reasoning = (
            f"At current demand, stock will run out in {days_until_stockout} day(s). "
            f"Your supplier lead time is {lead_time} day(s), so "
            + (
                "you need to order NOW to avoid a stockout."
                if days_until_stockout <= lead_time
                else f"you should order within the next {days_until_stockout - lead_time} day(s)."
            )
        )
    else:
        urgency = "ok"
        reasoning = "Stock levels look sufficient for the next 30 days based on current demand trends."

    return {
        "product_id": product_id,
        "product_name": product.name,
        "current_stock": current_stock,
        "avg_daily_demand": round(float(avg_daily_demand), 1),
        "supplier_lead_time_days": lead_time,
        "days_until_stockout": int(days_until_stockout) if days_until_stockout is not None else None,
        "needs_reorder": bool(needs_reorder),
        "urgency": urgency,
        "suggested_order_qty": int(suggested_order_qty),
        "reasoning": reasoning,
    }