"""Email sending API routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.models import EmailLog, EmailStatus
from backend.services.email_service import send_bulk_emails, retry_failed_emails

router = APIRouter()


class SendEmailRequest(BaseModel):
    contact_ids: List[int]
    subject_template: str
    body_template: str
    sender_name: str = "HR Team"
    use_ai: bool = False
    ai_tone: str = "Professional and Friendly"


class ScheduleEmailRequest(BaseModel):
    contact_ids: List[int]
    subject_template: str
    body_template: str
    sender_name: str = "HR Team"
    scheduled_at: str  # ISO format datetime string
    timezone: str = "UTC"
    use_ai: bool = False


@router.post("/send")
async def send_emails(req: SendEmailRequest, db: Session = Depends(get_db)):
    try:
        result = send_bulk_emails(
            db=db,
            contact_ids=req.contact_ids,
            subject_template=req.subject_template,
            body_template=req.body_template,
            sender_name=req.sender_name,
            use_ai=req.use_ai,
            ai_tone=req.ai_tone,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_email(req: ScheduleEmailRequest, db: Session = Depends(get_db)):
    from datetime import datetime
    from backend.scheduler.scheduler import schedule_bulk_email
    import uuid

    try:
        run_at = datetime.fromisoformat(req.scheduled_at)
        job_id = f"email_job_{uuid.uuid4().hex[:8]}"
        schedule_bulk_email(
            job_id=job_id,
            contact_ids=req.contact_ids,
            subject_template=req.subject_template,
            body_template=req.body_template,
            sender_name=req.sender_name,
            run_at=run_at,
            timezone_str=req.timezone,
            use_ai=req.use_ai,
        )
        return {"success": True, "job_id": job_id, "scheduled_at": req.scheduled_at}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-failed")
async def retry_failed(db: Session = Depends(get_db)):
    result = retry_failed_emails(db)
    return result


@router.get("/logs")
async def get_logs(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(EmailLog)
    if status:
        query = query.filter(EmailLog.status == status)
    if search:
        query = query.filter(
            (EmailLog.recipient_email.ilike(f"%{search}%")) |
            (EmailLog.recipient_name.ilike(f"%{search}%")) |
            (EmailLog.subject.ilike(f"%{search}%"))
        )
    logs = query.order_by(EmailLog.created_at.desc()).offset(skip).limit(limit).all()
    return [l.to_dict() for l in logs]


@router.get("/stats")
async def email_stats(db: Session = Depends(get_db)):
    from backend.services.report_service import get_email_stats
    return get_email_stats(db)
