from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, func
from app.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    disaster_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_population = Column(Integer, nullable=False)
    parameters = Column(JSON)
    results = Column(JSON)
    status = Column(String, nullable=False, default="draft")  # draft, running, completed
    created_at = Column(DateTime, server_default=func.now())
