from shopify_integration import router as shopify_router
import contextlib
import io
import pandas as pd
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import init_db, get_db, Store, Product, Sale
from forecasting import forecast_demand
from reorder import calculate_reorder
from agent import ask_agent
from billing import router as billing_router
from auth import (
    fastapi_users, auth_backend, create_db_and_tables,
    current_active_user, User, UserRead, UserCreate, UserUpdate
)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    init_db()
    yield


app = FastAPI(title="StockSense AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(billing_router)
app.include_router(shopify_router)


@app.get("/")
def root():
    return {"status": "StockSense AI backend running"}


@app.get("/api/v1/stores")
def list_stores(db: Session = Depends(get_db)):
    return db.query(Store).all()


@app.get("/api/v1/products/{store_id}")
def list_products(store_id: int, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.store_id == store_id).all()


@app.get("/api/v1/forecasts/{product_id}")
def get_forecast(product_id: int, days_ahead: int = 30, db: Session = Depends(get_db)):
    return forecast_demand(db, product_id, days_ahead)


@app.get("/api/v1/reorder/{product_id}")
def get_reorder_recommendation(product_id: int, db: Session = Depends(get_db)):
    return calculate_reorder(db, product_id)


@app.get("/api/v1/dashboard/{store_id}")
def get_dashboard(store_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.store_id == store_id).all()
    results = []
    for product in products:
        reorder_info = calculate_reorder(db, product.id)
        results.append(reorder_info)
    return {"store_id": store_id, "products": results}


class ChatRequest(BaseModel):
    question: str


@app.post("/api/v1/agent/{store_id}")
def chat_with_agent(store_id: int, request: ChatRequest, db: Session = Depends(get_db)):
    return ask_agent(db, store_id, request.question)


@app.post("/api/v1/upload/{store_id}")
async def upload_sales_csv(
    store_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception:
        raise HTTPException(status_code=400, detail="Could not parse CSV file")

    required_cols = {"product_name", "sku", "quantity_sold", "price", "sold_at"}
    if not required_cols.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {required_cols}"
        )

    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        store = Store(name="Demo Store")
        db.add(store)
        db.commit()
        db.refresh(store)

    inserted_sales = 0
    for _, row in df.iterrows():
        product = db.query(Product).filter(
            Product.store_id == store_id,
            Product.sku == str(row["sku"])
        ).first()

        if not product:
            product = Product(
                store_id=store_id,
                name=str(row["product_name"]),
                sku=str(row["sku"]),
                current_stock=0,
                supplier_lead_time_days=7,
            )
            db.add(product)
            db.commit()
            db.refresh(product)

        try:
            sold_at = pd.to_datetime(row["sold_at"])
        except Exception:
            continue

        sale = Sale(
            product_id=product.id,
            quantity_sold=int(row["quantity_sold"]),
            price=float(row["price"]),
            sold_at=sold_at,
        )
        db.add(sale)
        inserted_sales += 1

    db.commit()
    return {"message": f"Imported {inserted_sales} sales records successfully"}


@app.get("/api/v1/me")
async def get_me(user: User = Depends(current_active_user)):
    return {"email": user.email, "id": str(user.id)}


@app.post("/api/v1/stores/create")
def create_store(name: str = "Demo Store", db: Session = Depends(get_db)):
    store = Store(name=name)
    db.add(store)
    db.commit()
    db.refresh(store)
    return {"id": store.id, "name": store.name}

@app.post("/api/v1/admin/migrate")
def run_migration(db: Session = Depends(get_db)):
    """Add missing columns to existing tables."""
    try:
        db.execute(__import__('sqlalchemy').text(
            "ALTER TABLE stores ADD COLUMN IF NOT EXISTS shopify_domain VARCHAR;"
        ))
        db.execute(__import__('sqlalchemy').text(
            "ALTER TABLE stores ADD COLUMN IF NOT EXISTS shopify_token VARCHAR;"
        ))
        db.commit()
        return {"status": "migration complete"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/api/v1/shopify/sync/{store_id}")
async def sync_shopify(store_id: int, db: Session = Depends(get_db)):
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store or not store.shopify_token:
        raise HTTPException(status_code=404, detail="Store not found or not connected")
    
    from shopify_integration import sync_shopify_orders
    await sync_shopify_orders(store.shopify_domain, store.shopify_token, store.id, db)
    return {"status": "sync complete"}