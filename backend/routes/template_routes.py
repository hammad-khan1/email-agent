"""Email template CRUD routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.models import EmailTemplate

router = APIRouter()


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body_html: str
    body_text: Optional[str] = None


@router.get("/")
async def list_templates(db: Session = Depends(get_db)):
    templates = db.query(EmailTemplate).all()
    return [t.to_dict() for t in templates]


@router.post("/")
async def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    t = EmailTemplate(**data.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t.to_dict()


@router.get("/{template_id}")
async def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t.to_dict()


@router.put("/{template_id}")
async def update_template(template_id: int, data: TemplateCreate, db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    for k, v in data.model_dump().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t.to_dict()


@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(t)
    db.commit()
    return {"success": True}


@router.post("/{template_id}/duplicate")
async def duplicate_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    new_t = EmailTemplate(
        name=f"{t.name} (Copy)",
        subject=t.subject,
        body_html=t.body_html,
        body_text=t.body_text,
    )
    db.add(new_t)
    db.commit()
    db.refresh(new_t)
    return new_t.to_dict()
