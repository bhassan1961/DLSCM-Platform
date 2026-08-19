from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class DonationInKind(Base):
    __tablename__ = "donations_in_kind"

    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String, nullable=False)
    donor_contact = Column(String)
    items_description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # food, medical, shelter, nfi, mixed
    quantity = Column(Integer, nullable=False)
    unit = Column(String, nullable=False)
    quality_status = Column(String, nullable=False, default="pending_assessment")  # pending_assessment, acceptable, requires_sorting, rejected
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    received_date = Column(DateTime, nullable=False)
    assessed_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="received")  # received, assessed, stored, distributed, rejected
    created_at = Column(DateTime, server_default=func.now())
