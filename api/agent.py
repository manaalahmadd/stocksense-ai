import os
from reorder import calculate_reorder
from sqlalchemy.orm import Session

USE_REAL_CLAUDE = os.getenv("ANTHROPIC_API_KEY") is not None


def ask_agent(db: Session, store_id: int, user_question: str) -> dict:
    """
    Chat-style entry point for the inventory agent.
    If no API key is set, returns a mocked response built from real data
    (not fake numbers — real reorder calculations, just no LLM reasoning yet).
    """
    from models import Product

    products = db.query(Product).filter(Product.store_id == store_id).all()
    reorder_data = [calculate_reorder(db, p.id) for p in products]

    if USE_REAL_CLAUDE:
        return _ask_real_claude(reorder_data, user_question)
    else:
        return _mock_agent_response(reorder_data, user_question)


def _mock_agent_response(reorder_data: list[dict], user_question: str) -> dict:
    """Rule-based stand-in for Claude, using the same real data the real
    agent would see. Swap to _ask_real_claude once ANTHROPIC_API_KEY is set."""

    critical = [p for p in reorder_data if p["urgency"] == "critical"]
    warning = [p for p in reorder_data if p["urgency"] == "warning"]

    if critical:
        names = ", ".join(p["product_name"] for p in critical)
        answer = (
            f"[Mock agent] You have {len(critical)} item(s) needing urgent attention: "
            f"{names}. I'd recommend ordering these today to avoid stockouts."
        )
    elif warning:
        names = ", ".join(p["product_name"] for p in warning)
        answer = (
            f"[Mock agent] {len(warning)} item(s) are approaching reorder thresholds: "
            f"{names}. Worth planning orders in the next week."
        )
    else:
        answer = "[Mock agent] All your inventory levels look healthy right now."

    return {
        "answer": answer,
        "mode": "mock",
        "note": "Add ANTHROPIC_API_KEY to .env to enable real Claude reasoning.",
        "supporting_data": reorder_data,
    }


def _ask_real_claude(reorder_data: list[dict], user_question: str) -> dict:
    """Real implementation — activates automatically once an API key exists."""
    import anthropic

    client = anthropic.Anthropic()

    system_prompt = (
        "You are an inventory management assistant for a small retail store. "
        "You have access to real-time stock levels, demand forecasts, and "
        "reorder calculations. Answer the store owner's question clearly and "
        "concisely, referencing specific numbers. Be direct and actionable."
    )

    data_context = "\n".join(
        f"- {p['product_name']}: {p['current_stock']} units in stock, "
        f"avg demand {p['avg_daily_demand']}/day, urgency: {p['urgency']}. "
        f"{p['reasoning']}"
        for p in reorder_data
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Current inventory data:\n{data_context}\n\nQuestion: {user_question}",
            }
        ],
    )

    return {
        "answer": message.content[0].text,
        "mode": "claude",
        "supporting_data": reorder_data,
    }