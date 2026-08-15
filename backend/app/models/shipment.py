from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, nullable=False)
    request_id = Column(Integer, ForeignKey("supply_requests.id"), nullable=False)
    origin_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String, nullable=False, default="preparing")  # preparing, in_transit, delivered, delayed
    transport_mode = Column(String, nullable=False)  # road, air, sea, rail
    carrier = Column(String)
    current_lat = Column(Float)
    current_lng = Column(Float)
    eta = Column(DateTime)
    departed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    request = relationship("SupplyRequest", back_populates="shipments")
    origin_warehouse = relationship("Warehouse", back_populates="shipments")
    legs = relationship("ShipmentLeg", back_populates="shipment", order_by="ShipmentLeg.leg_order")


class ShipmentLeg(Base):
    __tablename__ = "shipment_legs"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    leg_order = Column(Integer, nullable=False)
    from_lat = Column(Float, nullable=False)
    from_lng = Column(Float, nullable=False)
    to_lat = Column(Float, nullable=False)
    to_lng = Column(Float, nullable=False)
    mode = Column(String, nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)

    shipment = relationship("Shipment", back_populates="legs")
