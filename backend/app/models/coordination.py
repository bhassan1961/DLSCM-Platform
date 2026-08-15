from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class ThreeWEntry(Base):
    __tablename__ = "threew_entries"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    activity = Column(String, nullable=False)  # food_distribution, medical_services, shelter_provision, water_sanitation, protection, education, logistics
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    beneficiaries = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String, nullable=False, default="active")  # planned, active, completed
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    organization = relationship("Organization", back_populates="threew_entries")
    disaster = relationship("Disaster", back_populates="threew_entries")
