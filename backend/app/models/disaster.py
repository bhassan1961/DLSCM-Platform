from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class Disaster(Base):
    __tablename__ = "disasters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    disaster_type = Column(String, nullable=False)  # drought, flood, earthquake, cyclone, conflict, epidemic
    severity = Column(String, nullable=False)  # minor, moderate, major, catastrophic
    status = Column(String, nullable=False, default="active")  # active, monitoring, resolved
    country = Column(String, nullable=False)
    region = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_population = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    supply_requests = relationship("SupplyRequest", back_populates="disaster")
    threew_entries = relationship("ThreeWEntry", back_populates="disaster")
    demand_forecasts = relationship("DemandForecast", back_populates="disaster")
    donor_reports = relationship("DonorReport", back_populates="disaster")
    after_action_reviews = relationship("AfterActionReview", back_populates="disaster")
