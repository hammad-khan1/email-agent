"""App settings routes."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend.database.database import get_db
from backend.models.models import AppSettings

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: str


def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    row = db.query(AppSettings).filter(AppSettings.key == key).first()
    return row.value if row else default


def set_setting(db: Session, key: str, value: str) -> None:
    row = db.query(AppSettings).filter(AppSettings.key == key).first()
    if row:
        row.value = value
    else:
        db.add(AppSettings(key=key, value=value))
    db.commit()


@router.get("/")
async def get_all_settings(db: Session = Depends(get_db)):
    rows = db.query(AppSettings).all()
    return {r.key: r.value for r in rows}


@router.post("/")
async def update_setting(data: SettingUpdate, db: Session = Depends(get_db)):
    set_setting(db, data.key, data.value)
    return {"success": True, "key": data.key, "value": data.value}


@router.get("/{key}")
async def get_single_setting(key: str, db: Session = Depends(get_db)):
    value = get_setting(db, key)
    return {"key": key, "value": value}
