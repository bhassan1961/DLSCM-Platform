from sqlalchemy import Column, Integer, String, Float, DateTime, Text, func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # cap, edxl, manual
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # extreme, severe, moderate, minor
    title = Column(String, nullable=False)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    status = Column(String, nullable=False, default="active")  # active, acknowledged, expired
    raw_message = Column(Text)
