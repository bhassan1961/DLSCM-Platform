from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class DonorReport(Base):
    __tablename__ = "donor_reports"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    title = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    content = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    disaster = relationship("Disaster", back_populates="donor_reports")


class AfterActionReview(Base):
    __tablename__ = "after_action_reviews"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    title = Column(String, nullable=False)
    review_date = Column(DateTime, nullable=False)
    response_time_hours = Column(Float)
    cost_per_beneficiary = Column(Float)
    stockout_events = Column(Integer)
    lessons_learned = Column(Text)
    recommendations = Column(Text)
    overall_score = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    disaster = relationship("Disaster", back_populates="after_action_reviews")
