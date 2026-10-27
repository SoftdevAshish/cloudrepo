from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.schemas import ItemCreate, ItemUpdate


def create_item(db: Session, data: ItemCreate) -> Item:
    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def list_items(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    stmt = select(Item).order_by(Item.id).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def update_item(db: Session, item: Item, data: ItemUpdate) -> Item:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: Item) -> None:
    db.delete(item)
    db.commit()
