import os
import razorpay
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db, Subscription
from pydantic import BaseModel

router = APIRouter()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

PLANS = {
    "starter": {"amount": 4900, "currency": "INR", "name": "Starter Plan"},
    "growth": {"amount": 14900, "currency": "INR", "name": "Growth Plan"},
}


@router.get("/api/v1/billing/plans")
def get_plans():
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": "₹4,900/mo",
                "features": [
                    "Up to 500 SKUs",
                    "AI reorder recommendations",
                    "CSV data upload",
                    "Weekly forecasts",
                ]
            },
            {
                "id": "growth",
                "name": "Growth",
                "price": "₹14,900/mo",
                "features": [
                    "Up to 5,000 SKUs",
                    "Real-time alerts",
                    "Chat with AI agent",
                    "Priority support",
                ]
            }
        ]
    }


class CreateOrderRequest(BaseModel):
    plan: str
    email: str


@router.post("/api/v1/billing/create-order")
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    if request.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    plan = PLANS[request.plan]

    order = client.order.create({
        "amount": plan["amount"],
        "currency": plan["currency"],
        "payment_capture": 1,
        "notes": {
            "email": request.email,
            "plan": request.plan
        }
    })

    return {
        "order_id": order["id"],
        "amount": plan["amount"],
        "currency": plan["currency"],
        "key_id": RAZORPAY_KEY_ID,
        "plan_name": plan["name"],
    }


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    email: str
    plan: str


@router.post("/api/v1/billing/verify-payment")
def verify_payment(request: VerifyPaymentRequest, db: Session = Depends(get_db)):
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": request.razorpay_order_id,
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature,
        })
    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Update or create subscription
    sub = db.query(Subscription).filter(
        Subscription.user_email == request.email
    ).first()

    if sub:
        sub.plan = request.plan
        sub.status = "active"
        sub.razorpay_payment_id = request.razorpay_payment_id
    else:
        sub = Subscription(
            user_email=request.email,
            plan=request.plan,
            status="active",
            razorpay_payment_id=request.razorpay_payment_id,
        )
        db.add(sub)

    db.commit()
    return {"status": "success", "plan": request.plan}


@router.get("/api/v1/billing/subscription/{email}")
def get_subscription(email: str, db: Session = Depends(get_db)):
    sub = db.query(Subscription).filter(
        Subscription.user_email == email
    ).first()

    if not sub:
        return {"plan": "free", "status": "active"}

    return {"plan": sub.plan, "status": sub.status}