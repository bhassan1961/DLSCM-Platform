from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SupplyRequest(Base):
    __tablename__ = "supply_requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, approved, sourcing, dispatched, delivered, cancelled
    priority = Column(String, nullable=False, default="medium")  # critical, high, medium, low
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    destination_name = Column(String, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    disaster = relationship("Disaster", back_populates="supply_requests")
    requester = relationship("User", back_populates="supply_requests")
    items = relationship("RequestItem", back_populates="request")
    shipments = relationship("Shipment", back_populates="request")


class RequestItem(Base):
    __tablename__ = "request_items"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("supply_requests.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity_requested = Column(Integer, nullable=False)
    quantity_fulfilled = Column(Integer, nullable=False, default=0)

    request = relationship("SupplyRequest", back_populates="items")
    item = relationship("Item", back_populates="request_items")
