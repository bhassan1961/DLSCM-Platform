from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity_m3 = Column(Float, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    organization = relationship("Organization", back_populates="warehouses")
    stocks = relationship("Stock", back_populates="warehouse")
    shipments = relationship("Shipment", back_populates="origin_warehouse")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)  # food, water, medical, shelter, hygiene, nfi
    unit = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    volume_m3 = Column(Float, nullable=False)

    stocks = relationship("Stock", back_populates="item")
    request_items = relationship("RequestItem", back_populates="item")


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    lot_number = Column(String)
    expiry_date = Column(DateTime)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    warehouse = relationship("Warehouse", back_populates="stocks")
    item = relationship("Item", back_populates="stocks")
