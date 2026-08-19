from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Kit(Base):
    __tablename__ = "kits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)  # family_hygiene, shelter_basic, medical_emergency, etc.
    created_at = Column(DateTime, server_default=func.now())

    components = relationship("KitComponent", back_populates="kit")


class KitComponent(Base):
    __tablename__ = "kit_components"

    id = Column(Integer, primary_key=True, index=True)
    kit_id = Column(Integer, ForeignKey("kits.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    kit = relationship("Kit", back_populates="components")
    item = relationship("Item")
