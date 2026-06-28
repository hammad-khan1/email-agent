"""
SQLAlchemy ORM Models for AI HR Email Automation Agent.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, Float, ForeignKey, Enum
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    RETRY = "retry"


class Contact(Base):
    """Represents an HR contact / candidate."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    joining_date = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    email_logs = relationship("EmailLog", back_populates="contact")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "domain": self.domain,
            "position": self.position,
            "joining_date": self.joining_date,
            "company": self.company,
            "location": self.location,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailTemplate(Base):
    """Stores reusable email templates with Jinja2 placeholders."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    is_ai_generated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "is_ai_generated": self.is_ai_generated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EmailLog(Base):
    """Tracks every email sent, failed, or scheduled."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    send_duration_ms = Column(Float, nullable=True)
    has_attachment = Column(Boolean, default=False)
    attachment_names = Column(Text, nullable=True)  # JSON list
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="email_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "recipient_email": self.recipient_email,
            "recipient_name": self.recipient_name,
            "subject": self.subject,
            "status": self.status,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "send_duration_ms": self.send_duration_ms,
            "has_attachment": self.has_attachment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScheduledEmail(Base):
    """Stores emails queued for future delivery."""
    __tablename__ = "scheduled_emails"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    contact_ids = Column(Text, nullable=False)  # JSON list of contact IDs
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    timezone = Column(String(100), default="UTC")
    status = Column(String(50), default="pending")
    job_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("EmailTemplate")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "template_id": self.template_id,
            "contact_ids": self.contact_ids,
            "subject": self.subject,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timezone": self.timezone,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AppSettings(Base):
    """Stores application-wide settings."""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GmailToken(Base):
    """Stores Gmail OAuth tokens."""
    __tablename__ = "gmail_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    token_json = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
