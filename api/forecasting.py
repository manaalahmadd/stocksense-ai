import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session
from models import Sale
from datetime import datetime, timedelta


def get_sales_dataframe(db: Session, product_id: int) -> pd.DataFrame:
    """Pull sales history for a product and aggregate into daily totals."""
    sales = db.query(Sale).filter(Sale.product_id == product_id).all()

    if not sales:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame([{"ds": s.sold_at, "y": s.quantity_sold} for s in sales])
    df["ds"] = pd.to_datetime(df["ds"]).dt.date
    df = df.groupby("ds", as_index=False)["y"].sum()
    df["ds"] = pd.to_datetime(df["ds"])

    # Fill missing days with 0 sales (Prophet needs a continuous date range)
    full_range = pd.date_range(start=df["ds"].min(), end=df["ds"].max(), freq="D")
    df = df.set_index("ds").reindex(full_range, fill_value=0).rename_axis("ds").reset_index()

    return df


def forecast_demand(db: Session, product_id: int, days_ahead: int = 30) -> dict:
    """Forecast future daily demand for a product."""
    df = get_sales_dataframe(db, product_id)

    # Cold-start fallback: not enough data for Prophet
    if len(df) < 14:
        avg_demand = df["y"].mean() if len(df) > 0 else 0
        forecast_dates = [
            (datetime.utcnow() + timedelta(days=i)).date().isoformat()
            for i in range(1, days_ahead + 1)
        ]
        return {
            "method": "moving_average_fallback",
            "forecast": [
                {"date": d, "predicted_demand": round(avg_demand, 1),
                 "lower_bound": round(avg_demand * 0.5, 1),
                 "upper_bound": round(avg_demand * 1.5, 1)}
                for d in forecast_dates
            ],
        }

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        interval_width=0.8,
    )
    model.fit(df)

    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    future_only = forecast.tail(days_ahead)

    return {
        "method": "prophet",
        "forecast": [
            {
                "date": row["ds"].date().isoformat(),
                "predicted_demand": max(0, round(row["yhat"], 1)),
                "lower_bound": max(0, round(row["yhat_lower"], 1)),
                "upper_bound": max(0, round(row["yhat_upper"], 1)),
            }
            for _, row in future_only.iterrows()
        ],
    }