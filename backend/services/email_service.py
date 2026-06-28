"""
Email sending service.
Handles batch sending, retry logic, rate limiting, progress updates, and logging.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable

from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger

from backend.models.models import Contact, EmailLog, EmailStatus, GmailToken
from backend.gmail.gmail_service import send_email
from backend.core.config import settings



def render_template(template_str: str, context: dict) -> str:
    """Render template by replacing {{Key}} placeholders manually."""
    if not template_str:
        return ""
    result = str(template_str)
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
        result = result.replace("{{ " + key + " }}", str(value))
    return result

def contact_to_context(contact: Contact) -> dict:
    """Convert a Contact model to a Jinja2 template context dict."""
    return {
        # Double curly brace style keys (for simple string replace)
        "Name": contact.name,
        "Email": contact.email,
        "Department": contact.department or "",
        "Domain": contact.domain or "",
        "Position": contact.position or "",
        "Joining Date": contact.joining_date or "",
        "Joining_Date": contact.joining_date or "",
        "Company": contact.company or "",
        "Location": contact.location or "",
        # lowercase versions
        "name": contact.name,
        "email": contact.email,
        "department": contact.department or "",
        "domain": contact.domain or "",
        "position": contact.position or "",
        "joining_date": contact.joining_date or "",
        "company": contact.company or "",
        "location": contact.location or "",
    }


def get_active_token(db: Session) -> Optional[str]:
    """Retrieve the active Gmail token JSON from the database."""
    token_row = db.query(GmailToken).filter(GmailToken.is_active == True).first()
    if token_row:
        return token_row.token_json
    return None


def send_bulk_emails(
    db: Session,
    contact_ids: List[int],
    subject_template: str,
    body_template: str,
    sender_name: str,
    attachment_paths: Optional[List[Path]] = None,
    progress_callback: Optional[Callable[[dict], None]] = None,
    use_ai: bool = False,
    ai_tone: str = "Professional and Friendly",
) -> dict:
    """
    Send personalized emails to a list of contacts.

    Args:
        db: Database session
        contact_ids: List of contact IDs to email
        subject_template: Jinja2 subject template string
        body_template: Jinja2 HTML body template string
        sender_name: Display name for From field
        attachment_paths: Optional list of file paths to attach
        progress_callback: Optional callable(progress_dict) for live updates
        use_ai: If True, generate AI body instead of using template
        ai_tone: Tone instruction for AI generation

    Returns:
        Summary dict with sent/failed/skipped counts
    """
    token_json = get_active_token(db)
    if not token_json:
        raise ValueError("No Gmail account connected. Please connect Gmail first.")

    contacts = db.query(Contact).filter(Contact.id.in_(contact_ids)).all()
    total = len(contacts)
    sent = 0
    failed = 0
    skipped = 0

    rate_limit_delay = 60.0 / max(settings.MAX_EMAILS_PER_MINUTE, 1)

    for i, contact in enumerate(contacts):
        # Check for prior successful send (dedup safety)
        already_sent = db.query(EmailLog).filter(
            EmailLog.recipient_email == contact.email,
            EmailLog.status == EmailStatus.SENT,
        ).first()
        if already_sent:
            logger.warning(f"Skipping {contact.email} — already sent successfully.")
            skipped += 1
            _report_progress(progress_callback, i + 1, total, contact, "skipped", sent, failed, skipped)
            continue

        context = contact_to_context(contact)

        if use_ai:
            from backend.ai.ai_service import generate_personalized_email
            ai_result = generate_personalized_email(
                name=contact.name,
                email=contact.email,
                domain=contact.domain,
                position=contact.position,
                joining_date=contact.joining_date,
                company=contact.company,
                department=contact.department,
                location=contact.location,
                tone=ai_tone,
            )
            subject = ai_result["subject"]
            body_html = ai_result["body_html"]
        else:
            subject = render_template(subject_template, context) or "No Subject"
            body_html = render_template(body_template, context) or ""

        # Attempt send with retry
        result = _send_with_retry(
            token_json=token_json,
            to_email=contact.email,
            to_name=contact.name,
            subject=subject,
            body_html=body_html,
            sender_name=sender_name,
            attachments=attachment_paths,
        )

        status = EmailStatus.SENT if result["success"] else EmailStatus.FAILED
        if result["success"]:
            sent += 1
        else:
            failed += 1

        # Log to database
        log_entry = EmailLog(
            contact_id=contact.id,
            recipient_email=contact.email,
            recipient_name=contact.name,
            subject=subject,
            body_html=body_html,
            status=status,
            error_message=result.get("error"),
            sent_at=datetime.utcnow() if result["success"] else None,
            send_duration_ms=result.get("duration_ms"),
            has_attachment=bool(attachment_paths),
            attachment_names=json.dumps([p.name for p in attachment_paths]) if attachment_paths else None,
        )
        db.add(log_entry)
        db.commit()

        _report_progress(
            progress_callback, i + 1, total, contact,
            "sent" if result["success"] else "failed",
            sent, failed, skipped,
        )

        # Rate limiting
        if i < total - 1:
            time.sleep(rate_limit_delay)

    logger.info(f"Bulk send complete: {sent} sent, {failed} failed, {skipped} skipped")
    return {"total": total, "sent": sent, "failed": failed, "skipped": skipped}


@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def _send_with_retry(
    token_json: str,
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    sender_name: str,
    attachments: Optional[List[Path]] = None,
) -> dict:
    """Attempt to send an email with up to 3 retries."""
    return send_email(
        token_json=token_json,
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        body_html=body_html,
        sender_name=sender_name,
        attachments=attachments,
    )


def _report_progress(callback, current, total, contact, status, sent, failed, skipped):
    """Fire progress callback if provided."""
    if callback:
        remaining = total - current
        callback({
            "current": current,
            "total": total,
            "percent": round((current / total) * 100, 1),
            "current_recipient": contact.name,
            "current_email": contact.email,
            "status": status,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "remaining": remaining,
        })


def retry_failed_emails(db: Session, max_retries: int = 3) -> dict:
    """Re-attempt all failed emails that haven't exceeded max_retries."""
    token_json = get_active_token(db)
    if not token_json:
        raise ValueError("No Gmail account connected.")

    failed_logs = db.query(EmailLog).filter(
        EmailLog.status == EmailStatus.FAILED,
        EmailLog.retry_count < max_retries,
    ).all()

    retried = 0
    succeeded = 0

    for log in failed_logs:
        result = send_email(
            token_json=token_json,
            to_email=log.recipient_email,
            to_name=log.recipient_name or "",
            subject=log.subject,
            body_html=log.body_html or "",
            sender_name=settings.DEFAULT_SENDER_NAME,
        )
        log.retry_count += 1
        if result["success"]:
            log.status = EmailStatus.SENT
            log.sent_at = datetime.utcnow()
            log.error_message = None
            succeeded += 1
        else:
            log.error_message = result.get("error")
        db.commit()
        retried += 1

    return {"retried": retried, "succeeded": succeeded, "still_failed": retried - succeeded}
