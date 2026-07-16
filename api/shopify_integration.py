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

    store = db.query(Store).filter(Store.name == shop).first()
    if not store:
        store = Store(name=shop, shopify_domain=shop, shopify_token=access_token)
        db.add(store)
    else:
        store.shopify_token = access_token
        store.shopify_domain = shop
    db.commit()
    db.refresh(store)

    await sync_shopify_products(shop, access_token, store.id, db)

    return RedirectResponse(
        url=f"https://stocksense-ai-frontend-gamma.vercel.app/?shop={shop}&connected=true"
    )


async def sync_shopify_products(shop: str, token: str, store_id: int, db: Session):
    """Sync products and inventory from Shopify."""
    headers = {"X-Shopify-Access-Token": token}

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://{shop}/admin/api/2024-01/products.json?limit=250",
            headers=headers,
        )
        products_data = res.json().get("products", [])

    for shopify_product in products_data:
        for variant in shopify_product.get("variants", []):
            sku = variant.get("sku") or f"shopify-{variant.get('id')}"
            name = shopify_product.get("title", "Unknown Product")
            stock = variant.get("inventory_quantity", 0)

            product = db.query(Product).filter(
                Product.store_id == store_id,
                Product.sku == sku
            ).first()

            if not product:
                product = Product(
                    store_id=store_id,
                    name=name,
                    sku=sku,
                    current_stock=stock,
                    supplier_lead_time_days=7,
                )
                db.add(product)
            else:
                product.current_stock = stock
                product.name = name

    db.commit()


# Keep this for backward compatibility
async def sync_shopify_orders(shop: str, token: str, store_id: int, db: Session):
    await sync_shopify_products(shop, token, store_id, db)


@router.post("/api/v1/shopify/webhook/orders")
async def shopify_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
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