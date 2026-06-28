"""Gmail OAuth routes."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.models import GmailToken
from backend.gmail.gmail_service import get_auth_url, exchange_code_for_token, get_connected_email
import json

router = APIRouter()


@router.get("/auth-url")
async def gmail_auth_url():
    url = get_auth_url()
    return {"auth_url": url}


@router.get("/callback")
async def gmail_callback(code: str, db: Session = Depends(get_db)):
    try:
        token_data = exchange_code_for_token(code)
        token_json = json.dumps(token_data)
        email = get_connected_email(token_json) or "unknown"

        # Deactivate old tokens
        db.query(GmailToken).update({"is_active": False})
        new_token = GmailToken(email=email, token_json=token_json, is_active=True)
        db.add(new_token)
        db.commit()
        return {"success": True, "connected_email": email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def gmail_status(db: Session = Depends(get_db)):
    token = db.query(GmailToken).filter(GmailToken.is_active == True).first()
    if token:
        return {"connected": True, "email": token.email}
    return {"connected": False, "email": None}


@router.post("/disconnect")
async def gmail_disconnect(db: Session = Depends(get_db)):
    db.query(GmailToken).update({"is_active": False})
    db.commit()
    return {"success": True, "message": "Gmail disconnected"}
