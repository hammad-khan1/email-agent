"""
Report generation service.
Exports email logs and statistics to Excel, CSV, and PDF.
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session
from loguru import logger

from backend.models.models import EmailLog, EmailStatus, Contact


REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


def get_email_stats(db: Session) -> dict:
    """Return aggregated email statistics."""
    total = db.query(EmailLog).count()
    sent = db.query(EmailLog).filter(EmailLog.status == EmailStatus.SENT).count()
    failed = db.query(EmailLog).filter(EmailLog.status == EmailStatus.FAILED).count()
    pending = db.query(EmailLog).filter(EmailLog.status == EmailStatus.PENDING).count()
    scheduled = db.query(EmailLog).filter(EmailLog.status == EmailStatus.SCHEDULED).count()
    contacts = db.query(Contact).filter(Contact.is_active == True).count()
    success_rate = round((sent / total * 100), 1) if total > 0 else 0

    return {
        "total_emails": total,
        "sent": sent,
        "failed": failed,
        "pending": pending,
        "scheduled": scheduled,
        "total_contacts": contacts,
        "success_rate": success_rate,
    }


def logs_to_dataframe(db: Session, status_filter: Optional[str] = None) -> pd.DataFrame:
    """Convert email logs to a pandas DataFrame."""
    query = db.query(EmailLog)
    if status_filter:
        query = query.filter(EmailLog.status == status_filter)
    logs = query.order_by(EmailLog.created_at.desc()).all()

    data = []
    for log in logs:
        data.append({
            "ID": log.id,
            "Recipient Name": log.recipient_name or "",
            "Recipient Email": log.recipient_email,
            "Subject": log.subject,
            "Status": log.status.value if log.status else "",
            "Sent At": log.sent_at.strftime("%Y-%m-%d %H:%M:%S") if log.sent_at else "",
            "Duration (ms)": log.send_duration_ms or "",
            "Retry Count": log.retry_count,
            "Error": log.error_message or "",
            "Has Attachment": "Yes" if log.has_attachment else "No",
            "Created At": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
        })

    return pd.DataFrame(data)


def export_to_csv(db: Session, status_filter: Optional[str] = None) -> bytes:
    """Export logs to CSV bytes."""
    df = logs_to_dataframe(db, status_filter)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def export_to_excel(db: Session, status_filter: Optional[str] = None) -> bytes:
    """Export logs to Excel bytes."""
    df = logs_to_dataframe(db, status_filter)
    stats = get_email_stats(db)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Email logs sheet
        df.to_excel(writer, sheet_name="Email Logs", index=False)
        workbook = writer.book
        ws = writer.sheets["Email Logs"]

        # Header format
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#1E3A5F",
            "font_color": "white", "border": 1,
        })
        for col_num, col_name in enumerate(df.columns):
            ws.write(0, col_num, col_name, header_fmt)
            ws.set_column(col_num, col_num, max(15, len(col_name) + 5))

        # Stats summary sheet
        stats_df = pd.DataFrame([stats])
        stats_df.to_excel(writer, sheet_name="Summary", index=False)

    return buffer.getvalue()


def export_to_pdf(db: Session) -> bytes:
    """Export a statistics summary report to PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    stats = get_email_stats(db)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("HR Email Agent — Report", styles["Title"]))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 20))

    # Stats table
    stats_data = [
        ["Metric", "Value"],
        ["Total Contacts", stats["total_contacts"]],
        ["Total Emails", stats["total_emails"]],
        ["Sent", stats["sent"]],
        ["Failed", stats["failed"]],
        ["Pending", stats["pending"]],
        ["Scheduled", stats["scheduled"]],
        ["Success Rate", f"{stats['success_rate']}%"],
    ]
    table = Table(stats_data, colWidths=[250, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2F7")]),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    doc.build(elements)
    return buffer.getvalue()
