from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String, unique=True, nullable=False)
    request_id = Column(Integer, ForeignKey("supply_requests.id"), nullable=False)
    origin_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(String, nullable=False, default="preparing")
    transport_mode = Column(String, nullable=False)
    carrier = Column(String)
    current_lat = Column(Float)
    current_lng = Column(Float)
    eta = Column(DateTime)
    departed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    notes = Column(Text)
    customs_status = Column(
        String, default="not_required"
    )  # not_required, pending, cleared, held
    customs_docs = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    request = relationship("SupplyRequest", back_populates="shipments")
    origin_warehouse = relationship("Warehouse", back_populates="shipments")
    legs = relationship(
        "ShipmentLeg", back_populates="shipment", order_by="ShipmentLeg.leg_order"
    )
    tracking_events = relationship(
        "ShipmentTrackingEvent",
        back_populates="shipment",
        order_by="ShipmentTrackingEvent.timestamp",
    )


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
    carrier = Column(String, nullable=True)
    from_location = Column(String, nullable=True)
    to_location = Column(String, nullable=True)

    shipment = relationship("Shipment", back_populates="legs")


class ShipmentTrackingEvent(Base):
    __tablename__ = "shipment_tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    event_type = Column(
        String, nullable=False
    )  # departure, arrival, customs_hold, customs_clear, delay, handoff, delivery
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    event_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())

    shipment = relationship("Shipment", back_populates="tracking_events")
