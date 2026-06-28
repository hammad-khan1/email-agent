"""
Contact management service.
Handles Excel/CSV upload, validation, deduplication, CRUD.
"""

import json
from io import BytesIO
from typing import Optional
import pandas as pd
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import Session
from loguru import logger

from backend.models.models import Contact


REQUIRED_COLUMNS = ["name", "email"]
OPTIONAL_COLUMNS = ["department", "domain", "position", "joining_date", "company", "location"]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def validate_contacts_df(df: pd.DataFrame) -> dict:
    """
    Validate a contacts DataFrame.

    Returns:
        dict with keys: valid_rows, invalid_rows, duplicate_emails,
        missing_email_rows, invalid_email_rows, missing_required_fields
    """
    df = normalize_columns(df)

    # Check required columns exist
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        return {
            "error": f"Missing required columns: {missing_cols}",
            "valid": False,
        }

    results = {
        "total": len(df),
        "valid_rows": [],
        "invalid_rows": [],
        "duplicate_emails": [],
        "missing_email_rows": [],
        "invalid_email_rows": [],
        "missing_name_rows": [],
        "valid": True,
    }

    seen_emails = set()

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed + header
        issues = []

        # Check name
        name = str(row.get("name", "")).strip()
        if not name or name.lower() == "nan":
            issues.append("missing_name")
            results["missing_name_rows"].append(row_num)

        # Check email
        email_raw = str(row.get("email", "")).strip()
        if not email_raw or email_raw.lower() == "nan":
            issues.append("missing_email")
            results["missing_email_rows"].append(row_num)
        else:
            try:
                valid = validate_email(email_raw, check_deliverability=False)
                email = valid.email
            except EmailNotValidError:
                issues.append("invalid_email")
                results["invalid_email_rows"].append(row_num)
                email = email_raw

            if email in seen_emails:
                issues.append("duplicate_email")
                results["duplicate_emails"].append(email)
            else:
                seen_emails.add(email)

        if issues:
            results["invalid_rows"].append({
                "row": row_num,
                "name": name,
                "email": email_raw,
                "issues": issues,
            })
        else:
            clean_row = {col: str(row.get(col, "")).strip() for col in ALL_COLUMNS if col in df.columns}
            results["valid_rows"].append(clean_row)

    return results


def parse_file_to_df(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse uploaded Excel or CSV file into a DataFrame."""
    filename_lower = filename.lower()
    if filename_lower.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
    elif filename_lower.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        raise ValueError(f"Unsupported file format: {filename}")
    return df


def import_contacts_to_db(valid_rows: list, db: Session, skip_duplicates: bool = True) -> dict:
    """
    Save validated contact rows to the database.

    Returns:
        dict with imported, skipped, and failed counts.
    """
    imported = 0
    skipped = 0
    failed = 0

    for row in valid_rows:
        email = row.get("email", "").strip()
        try:
            existing = db.query(Contact).filter(Contact.email == email).first()
            if existing and skip_duplicates:
                skipped += 1
                continue
            if existing:
                # Update existing
                for col in OPTIONAL_COLUMNS:
                    val = row.get(col)
                    if val:
                        setattr(existing, col, val)
                existing.name = row.get("name", existing.name)
                db.commit()
                imported += 1
            else:
                contact = Contact(
                    name=row.get("name", ""),
                    email=email,
                    department=row.get("department"),
                    domain=row.get("domain"),
                    position=row.get("position"),
                    joining_date=row.get("joining_date"),
                    company=row.get("company"),
                    location=row.get("location"),
                )
                db.add(contact)
                db.commit()
                imported += 1
        except Exception as e:
            logger.error(f"Failed to import contact {email}: {e}")
            db.rollback()
            failed += 1

    logger.info(f"Import complete: {imported} imported, {skipped} skipped, {failed} failed")
    return {"imported": imported, "skipped": skipped, "failed": failed}


def search_contacts(
    db: Session,
    query: Optional[str] = None,
    department: Optional[str] = None,
    company: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list:
    """Search/filter contacts."""
    q = db.query(Contact).filter(Contact.is_active == True)
    if query:
        q = q.filter(
            (Contact.name.ilike(f"%{query}%")) |
            (Contact.email.ilike(f"%{query}%"))
        )
    if department:
        q = q.filter(Contact.department.ilike(f"%{department}%"))
    if company:
        q = q.filter(Contact.company.ilike(f"%{company}%"))
    return q.offset(skip).limit(limit).all()


def get_contact_stats(db: Session) -> dict:
    """Return total active and inactive contact counts."""
    total = db.query(Contact).filter(Contact.is_active == True).count()
    return {"total_contacts": total}
