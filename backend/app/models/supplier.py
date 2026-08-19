from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, func
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # food, medical, shelter, logistics, water, nfi, general
    country = Column(String, nullable=False)
    contact_email = Column(String)
    lead_time_days = Column(Integer)
    quality_rating = Column(Float)  # 1.0 - 5.0
    capacity_description = Column(String)
    pre_qualified = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
