from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)  # ngo, government, private, un_agency
    country = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    users = relationship("User", back_populates="organization")
    warehouses = relationship("Warehouse", back_populates="organization")
    threew_entries = relationship("ThreeWEntry", back_populates="organization")
    surge_listings = relationship("SurgeCapacityListing", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # ops_director, field_coordinator, supply_manager, compliance_officer
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    organization = relationship("Organization", back_populates="users")
    supply_requests = relationship("SupplyRequest", back_populates="requester")
