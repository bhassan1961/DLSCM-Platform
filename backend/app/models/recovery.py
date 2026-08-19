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


class RecoveryPlan(Base):
    __tablename__ = "recovery_plans"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    target_completion = Column(String)
    current_phase = Column(String, nullable=False, default="assessment")
    phases = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    disaster = relationship("Disaster")
    procurement_items = relationship(
        "RecoveryProcurement", back_populates="plan", cascade="all, delete-orphan"
    )


class RecoveryProcurement(Base):
    __tablename__ = "recovery_procurement"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("recovery_plans.id"), nullable=False)
    item = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    supplier = Column(String)
    status = Column(String, nullable=False, default="planned")
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("RecoveryPlan", back_populates="procurement_items")
