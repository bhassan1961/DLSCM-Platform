from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SurgeCapacityListing(Base):
    __tablename__ = "surge_capacity_listings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    listing_type = Column(String, nullable=False)  # warehouse_space, transport, personnel
    title = Column(String, nullable=False)
    description = Column(Text)
    capacity_value = Column(Float, nullable=False)
    capacity_unit = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    available_from = Column(DateTime, nullable=False)
    available_until = Column(DateTime)
    status = Column(String, nullable=False, default="available")  # available, reserved, fulfilled
    created_at = Column(DateTime, server_default=func.now())

    organization = relationship("Organization", back_populates="surge_listings")
