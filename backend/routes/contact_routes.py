"""Contact management API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.models import Contact
from backend.services.contact_service import (
    parse_file_to_df, validate_contacts_df,
    import_contacts_to_db, search_contacts, get_contact_stats,
)

router = APIRouter()


class ContactCreate(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    domain: Optional[str] = None
    position: Optional[str] = None
    joining_date: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None


@router.get("/")
async def list_contacts(
    q: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    contacts = search_contacts(db, q, department, company, skip, limit)
    return [c.to_dict() for c in contacts]


@router.get("/stats")
async def contact_stats(db: Session = Depends(get_db)):
    return get_contact_stats(db)


@router.post("/")
async def create_contact(data: ContactCreate, db: Session = Depends(get_db)):
    existing = db.query(Contact).filter(Contact.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact.to_dict()


@router.put("/{contact_id}")
async def update_contact(contact_id: int, data: ContactCreate, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    for k, v in data.model_dump().items():
        setattr(contact, k, v)
    db.commit()
    db.refresh(contact)
    return contact.to_dict()


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.is_active = False
    db.commit()
    return {"success": True}


@router.post("/upload/validate")
async def validate_upload(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = parse_file_to_df(content, file.filename)
        result = validate_contacts_df(df)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload/import")
async def import_upload(
    file: UploadFile = File(...),
    skip_duplicates: bool = True,
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        df = parse_file_to_df(content, file.filename)
        validation = validate_contacts_df(df)
        if "error" in validation:
            raise HTTPException(status_code=400, detail=validation["error"])
        result = import_contacts_to_db(validation["valid_rows"], db, skip_duplicates)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
