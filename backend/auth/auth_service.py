"""
Simple HR authentication using JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac
import base64
import json

from loguru import logger
from backend.core.config import settings


def _hash_password(password: str) -> str:
    """Return SHA-256 hex digest of password."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(username: str, password: str) -> bool:
    """Verify HR login credentials against env config."""
    valid_user = username == settings.HR_USERNAME
    valid_pass = hmac.compare_digest(
        _hash_password(password),
        _hash_password(settings.HR_PASSWORD),
    )
    if valid_user and valid_pass:
        logger.info(f"Login successful for user: {username}")
        return True
    logger.warning(f"Failed login attempt for user: {username}")
    return False


def create_token(username: str, expires_minutes: int = 480) -> str:
    """Create a simple base64-encoded JWT-like token."""
    payload = {
        "sub": username,
        "exp": (datetime.utcnow() + timedelta(minutes=expires_minutes)).isoformat(),
        "iat": datetime.utcnow().isoformat(),
    }
    token_data = json.dumps(payload)
    signature = hmac.new(
        settings.APP_SECRET_KEY.encode(),
        token_data.encode(),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{base64.b64encode(token_data.encode()).decode()}.{signature}"
    return raw


def verify_token(token: str) -> Optional[str]:
    """Verify token and return username, or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        token_data = base64.b64decode(parts[0]).decode()
        expected_sig = hmac.new(
            settings.APP_SECRET_KEY.encode(),
            token_data.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(parts[1], expected_sig):
            return None
        payload = json.loads(token_data)
        if datetime.fromisoformat(payload["exp"]) < datetime.utcnow():
            return None
        return payload["sub"]
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None
