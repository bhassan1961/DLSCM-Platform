from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    disaster_id = Column(Integer, ForeignKey("disasters.id"), nullable=False)
    category = Column(String, nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    daily_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    disaster = relationship("Disaster", back_populates="demand_forecasts")
