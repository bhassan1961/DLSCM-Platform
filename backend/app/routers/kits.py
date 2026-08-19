from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.kit import Kit, KitComponent
from app.models.inventory import Item

router = APIRouter(prefix="/api/v1/kits", tags=["kits"])


# ── Schemas ────────────────────────────────────────────────────────────

class KitComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kit_id: int
    item_id: int
    item_name: str = ""
    quantity: int


class KitComponentCreate(BaseModel):
    item_id: int
    quantity: int


class KitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    category: str
    created_at: Optional[datetime] = None
    components: list[KitComponentOut] = []


class KitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    components: list[KitComponentCreate] = []


# ── Endpoints ──────────────────────────────────────────────────────────

def _to_kit_out(kit: Kit) -> KitOut:
    components_out = []
    for comp in kit.components:
        components_out.append(KitComponentOut(
            id=comp.id, kit_id=comp.kit_id, item_id=comp.item_id,
            item_name=comp.item.name if comp.item else "",
            quantity=comp.quantity,
        ))
    return KitOut(
        id=kit.id, name=kit.name, description=kit.description,
        category=kit.category, created_at=kit.created_at,
        components=components_out,
    )


@router.get("", response_model=list[KitOut])
def list_kits(db: Session = Depends(get_db)):
    kits = (
        db.query(Kit)
        .options(joinedload(Kit.components).joinedload(KitComponent.item))
        .all()
    )
    return [_to_kit_out(k) for k in kits]


@router.post("", response_model=KitOut)
def create_kit(kit_data: KitCreate, db: Session = Depends(get_db)):
    kit = Kit(name=kit_data.name, description=kit_data.description, category=kit_data.category)
    db.add(kit)
    db.flush()
    for comp in kit_data.components:
        item = db.query(Item).filter(Item.id == comp.item_id).first()
        if not item:
            raise HTTPException(status_code=400, detail=f"Item with id {comp.item_id} not found")
        db.add(KitComponent(kit_id=kit.id, item_id=comp.item_id, quantity=comp.quantity))
    db.commit()
    result = (
        db.query(Kit)
        .options(joinedload(Kit.components).joinedload(KitComponent.item))
        .filter(Kit.id == kit.id)
        .first()
    )
    return _to_kit_out(result)
