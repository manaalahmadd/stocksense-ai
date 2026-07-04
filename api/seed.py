from datetime import datetime, timedelta
import random
from models import init_db, SessionLocal, Store, Product, Sale

init_db()
db = SessionLocal()

# Clear existing data (so you can re-run this safely)
db.query(Sale).delete()
db.query(Product).delete()
db.query(Store).delete()
db.commit()

# Create a store
store = Store(name="Demo Mart")
db.add(store)
db.commit()
db.refresh(store)

# Create 5 products
product_data = [
    {"name": "Wireless Mouse", "sku": "WM-001", "current_stock": 45, "base_demand": 4},
    {"name": "USB-C Cable", "sku": "UC-002", "current_stock": 120, "base_demand": 8},
    {"name": "Notebook Set", "sku": "NB-003", "current_stock": 15, "base_demand": 2},
    {"name": "Desk Lamp", "sku": "DL-004", "current_stock": 30, "base_demand": 3},
    {"name": "Coffee Mug", "sku": "CM-005", "current_stock": 60, "base_demand": 5},
]

products = []
for p in product_data:
    product = Product(
        store_id=store.id,
        name=p["name"],
        sku=p["sku"],
        current_stock=p["current_stock"],
        supplier_lead_time_days=random.choice([3, 5, 7]),
    )
    db.add(product)
    products.append((product, p["base_demand"]))

db.commit()
for product, _ in products:
    db.refresh(product)

# Generate 90 days of sales history per product
today = datetime.utcnow()
for product, base_demand in products:
    for day_offset in range(90, 0, -1):
        sale_date = today - timedelta(days=day_offset)

        # Weekend boost (Saturday/Sunday sell more)
        is_weekend = sale_date.weekday() >= 5
        daily_demand = base_demand + (2 if is_weekend else 0)

        # Add randomness, occasionally a zero-sale day
        quantity = max(0, int(random.gauss(daily_demand, daily_demand * 0.4)))

        if quantity > 0:
            sale = Sale(
                product_id=product.id,
                quantity_sold=quantity,
                price=round(random.uniform(5, 50), 2),
                sold_at=sale_date,
            )
            db.add(sale)

db.commit()

store_name = store.name
store_id = store.id
num_products = len(products)

db.close()

print(f"Seeded store '{store_name}' (id={store_id}) with {num_products} products and 90 days of sales history.")