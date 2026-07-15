import os
import hmac
import hashlib
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import get_db, Store, Product, Sale
from datetime import datetime

router = APIRouter()

SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")
APP_URL = "https://stocksense-ai-6enu.onrender.com"
SCOPES = "read_orders,read_products,read_inventory,read_fulfillments"


@router.get("/api/v1/shopify/install")
def shopify_install(shop: str):
    """Step 1 — redirect store owner to Shopify OAuth page."""
    if not shop:
        raise HTTPException(status_code=400, detail="shop parameter required")

    redirect_uri = f"{APP_URL}/api/v1/shopify/callback"
    auth_url = (
        f"https://{shop}/admin/oauth/authorize"
        f"?client_id={SHOPIFY_CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={redirect_uri}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/api/v1/shopify/callback")
async def shopify_callback(code: str, shop: str, db: Session = Depends(get_db)):
    """Step 2 — exchange code for access token, then sync orders."""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"https://{shop}/admin/oauth/access_token",
            json={
                "client_id": SHOPIFY_CLIENT_ID,
                "client_secret": SHOPIFY_CLIENT_SECRET,
                "code": code,
            }
        )
        token_data = res.json()

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    # Get or create store, always update token
    store = db.query(Store).filter(Store.name == shop).first()
    if not store:
        store = Store(name=shop, shopify_domain=shop, shopify_token=access_token)
        db.add(store)
    else:
        store.shopify_token = access_token
        store.shopify_domain = shop
    db.commit()
    db.refresh(store)

    # Sync last 90 days of orders
    await sync_shopify_orders(shop, access_token, store.id, db)

    return RedirectResponse(
        url=f"https://stocksense-ai-frontend-gamma.vercel.app/?shop={shop}&connected=true"
    )


async def sync_shopify_orders(shop: str, token: str, store_id: int, db: Session):
    """Pull last 90 days of orders from Shopify and store as sales."""
    headers = {"X-Shopify-Access-Token": token}

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://{shop}/admin/api/2024-01/orders.json"
            f"?status=any&limit=250",
            headers=headers,
        )
        orders = res.json().get("orders", [])

    for order in orders:
        for item in order.get("line_items", []):
            sku = item.get("sku") or f"shopify-{item.get('product_id')}"
            name = item.get("title", "Unknown Product")

            product = db.query(Product).filter(
                Product.store_id == store_id,
                Product.sku == sku
            ).first()

            if not product:
                product = Product(
                    store_id=store_id,
                    name=name,
                    sku=sku,
                    current_stock=0,
                    supplier_lead_time_days=7,
                )
                db.add(product)
                db.commit()
                db.refresh(product)

            try:
                sold_at = datetime.fromisoformat(
                    order["created_at"].replace("Z", "+00:00")
                )
            except Exception:
                continue

            sale = Sale(
                product_id=product.id,
                quantity_sold=item.get("quantity", 1),
                price=float(item.get("price", 0)),
                sold_at=sold_at,
            )
            db.add(sale)

    db.commit()


@router.post("/api/v1/shopify/webhook/orders")
async def shopify_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive real-time order webhooks from Shopify."""
    body = await request.body()

    # Verify webhook signature
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
    computed = hmac.new(
        SHOPIFY_CLIENT_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json
    order = json.loads(body)
    shop = request.headers.get("X-Shopify-Shop-Domain", "")

    store = db.query(Store).filter(Store.name == shop).first()
    if not store:
        return {"status": "store not found"}

    for item in order.get("line_items", []):
        sku = item.get("sku") or f"shopify-{item.get('product_id')}"
        product = db.query(Product).filter(
            Product.store_id == store.id,
            Product.sku == sku
        ).first()

        if not product:
            product = Product(
                store_id=store.id,
                name=item.get("title", "Unknown"),
                sku=sku,
                current_stock=0,
                supplier_lead_time_days=7,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        sale = Sale(
            product_id=product.id,
            quantity_sold=item.get("quantity", 1),
            price=float(item.get("price", 0)),
            sold_at=datetime.utcnow(),
        )
        db.add(sale)

    db.commit()
    return {"status": "ok"}