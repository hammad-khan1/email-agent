"""
Email scheduler using APScheduler.
Supports scheduling emails for a future date/time with timezone support.
"""

from datetime import datetime
from typing import List, Optional
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from loguru import logger

from backend.core.config import settings


_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> BackgroundScheduler:
    """Return the global scheduler instance (lazy init)."""
    global _scheduler
    if _scheduler is None:
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.DATABASE_URL),
        }
        executors = {"default": ThreadPoolExecutor(max_workers=5)}
        _scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone=settings.SCHEDULER_TIMEZONE,
        )
    return _scheduler


def start_scheduler() -> None:
    """Start the background scheduler."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started.")


def stop_scheduler() -> None:
    """Shutdown the scheduler gracefully."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")


def schedule_bulk_email(
    job_id: str,
    contact_ids: List[int],
    subject_template: str,
    body_template: str,
    sender_name: str,
    run_at: datetime,
    timezone_str: str = "UTC",
    use_ai: bool = False,
) -> str:
    """
    Schedule a bulk email job to run at a specific datetime.

    Args:
        job_id: Unique job identifier
        contact_ids: List of contact IDs to email
        subject_template: Email subject (Jinja2)
        body_template: Email body HTML (Jinja2)
        sender_name: From display name
        run_at: Naive or aware datetime to run the job
        timezone_str: IANA timezone string (e.g. 'Asia/Karachi')
        use_ai: Whether to use AI generation

    Returns:
        job_id string
    """
    scheduler = get_scheduler()

    tz = pytz.timezone(timezone_str)
    if run_at.tzinfo is None:
        run_at = tz.localize(run_at)

    scheduler.add_job(
        func=_run_scheduled_email,
        trigger="date",
        run_date=run_at,
        id=job_id,
        replace_existing=True,
        kwargs={
            "contact_ids": contact_ids,
            "subject_template": subject_template,
            "body_template": body_template,
            "sender_name": sender_name,
            "use_ai": use_ai,
        },
    )

    logger.info(f"Scheduled email job '{job_id}' at {run_at} ({timezone_str})")
    return job_id


def _run_scheduled_email(
    contact_ids: List[int],
    subject_template: str,
    body_template: str,
    sender_name: str,
    use_ai: bool = False,
) -> None:
    """Internal function executed by the scheduler."""
    from backend.database.database import SessionLocal
    from backend.services.email_service import send_bulk_emails

    db = SessionLocal()
    try:
        result = send_bulk_emails(
            db=db,
            contact_ids=contact_ids,
            subject_template=subject_template,
            body_template=body_template,
            sender_name=sender_name,
            use_ai=use_ai,
        )
        logger.info(f"Scheduled email completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled email failed: {e}")
    finally:
        db.close()


def cancel_job(job_id: str) -> bool:
    """Cancel a scheduled job by ID."""
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled scheduled job: {job_id}")
        return True
    except Exception as e:
        logger.warning(f"Could not cancel job {job_id}: {e}")
        return False


def list_scheduled_jobs() -> list:
    """Return a list of all pending scheduled jobs."""
    scheduler = get_scheduler()
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run_time": str(job.next_run_time),
            "name": job.name,
        })
    return jobs
