from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class MarketplaceBooking(Base):
    __tablename__ = "marketplace_bookings"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(
        Integer, ForeignKey("surge_capacity_listings.id"), nullable=False
    )
    requester_org = Column(String, nullable=False)
    quantity_needed = Column(Float, nullable=False)
    notes = Column(Text)
    status = Column(String, nullable=False, default="confirmed")
    booked_at = Column(DateTime, server_default=func.now())

    listing = relationship("SurgeCapacityListing")
