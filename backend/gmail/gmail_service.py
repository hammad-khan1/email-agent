"""
Gmail API integration using OAuth 2.0.
Handles connect, disconnect, token refresh, and sending emails.
"""

import base64
import json
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

from backend.core.config import settings


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def get_oauth_flow() -> Flow:
    """Build the Google OAuth flow from settings."""
    client_config = {
        "web": {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GMAIL_REDIRECT_URI],
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = settings.GMAIL_REDIRECT_URI
    return flow


def get_auth_url() -> str:
    """Return the Google OAuth consent screen URL."""
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    flow = get_oauth_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else [],
    }
    return token_data


def get_credentials_from_token(token_json: str) -> Optional[Credentials]:
    """Rebuild Credentials object from stored token JSON."""
    try:
        token_data = json.loads(token_json)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", settings.GMAIL_CLIENT_ID),
            client_secret=token_data.get("client_secret", settings.GMAIL_CLIENT_SECRET),
            scopes=token_data.get("scopes", SCOPES),
        )
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("Gmail token refreshed successfully.")
        return creds
    except Exception as e:
        logger.error(f"Failed to build credentials: {e}")
        return None


def get_gmail_service(token_json: str):
    """Build and return the Gmail API service."""
    creds = get_credentials_from_token(token_json)
    if not creds:
        raise ValueError("Invalid or expired Gmail credentials.")
    return build("gmail", "v1", credentials=creds)


def get_connected_email(token_json: str) -> Optional[str]:
    """Return the Gmail address tied to the token."""
    try:
        service = get_gmail_service(token_json)
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception as e:
        logger.error(f"Failed to get connected email: {e}")
        return None


def build_mime_message(
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    sender_name: str,
    from_email: str,
    attachments: Optional[List[Path]] = None,
) -> MIMEMultipart:
    """Construct a MIME email message."""
    msg = MIMEMultipart("mixed")
    msg["To"] = f"{to_name} <{to_email}>"
    msg["From"] = f"{sender_name} <{from_email}>"
    msg["Subject"] = subject

    # HTML body
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_html, "html", "utf-8"))
    msg.attach(alt)

    # Attachments
    if attachments:
        for file_path in attachments:
            if not file_path.exists():
                logger.warning(f"Attachment not found: {file_path}")
                continue
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{file_path.name}"',
            )
            msg.attach(part)

    return msg


def send_email(
    token_json: str,
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    sender_name: str,
    attachments: Optional[List[Path]] = None,
) -> dict:
    """
    Send a single email via Gmail API.
    Returns dict with success status and metadata.
    """
    start = time.time()
    try:
        service = get_gmail_service(token_json)
        profile = service.users().getProfile(userId="me").execute()
        from_email = profile.get("emailAddress", "")

        mime_msg = build_mime_message(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body_html=body_html,
            sender_name=sender_name,
            from_email=from_email,
            attachments=attachments,
        )

        raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
        service.users().messages().send(
            userId="me",
            body={"raw": raw},
        ).execute()

        duration_ms = (time.time() - start) * 1000
        logger.success(f"Email sent to {to_email} in {duration_ms:.0f}ms")
        return {"success": True, "duration_ms": duration_ms, "from_email": from_email}

    except HttpError as e:
        logger.error(f"Gmail API error sending to {to_email}: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error sending to {to_email}: {e}")
        return {"success": False, "error": str(e)}
