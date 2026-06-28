"""Report generation and export routes."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.database.database import get_db
from backend.services.report_service import (
    get_email_stats, export_to_csv, export_to_excel, export_to_pdf
)

router = APIRouter()


@router.get("/stats")
async def stats(db: Session = Depends(get_db)):
    return get_email_stats(db)


@router.get("/export/csv")
async def export_csv(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    data = export_to_csv(db, status)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=email_report.csv"},
    )


@router.get("/export/excel")
async def export_excel(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    data = export_to_excel(db, status)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=email_report.xlsx"},
    )


@router.get("/export/pdf")
async def export_pdf(db: Session = Depends(get_db)):
    data = export_to_pdf(db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=email_report.pdf"},
    )
