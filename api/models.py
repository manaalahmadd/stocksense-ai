from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stocksense.db")
# Fix for SQLAlchemy compatibility with Render's postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shopify_domain = Column(String, nullable=True)
    shopify_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="store")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id"))
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    current_stock = Column(Integer, default=0)
    supplier_lead_time_days = Column(Integer, default=7)

    store = relationship("Store", back_populates="products")
    sales = relationship("Sale", back_populates="product")


class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity_sold = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    sold_at = Column(DateTime, nullable=False)

    product = relationship("Product", back_populates="sales")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, unique=True)
    plan = Column(String, default="free")  # free, starter, growth
    status = Column(String, default="active")  # active, cancelled
    razorpay_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()