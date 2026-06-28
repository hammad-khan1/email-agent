"""
Unit tests for the contact service.
Run with: pytest tests/ -v
"""

import pytest
import pandas as pd
from io import BytesIO
from backend.services.contact_service import validate_contacts_df, normalize_columns


class TestValidateContactsDf:

    def _make_df(self, rows: list) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def test_valid_contacts(self):
        df = self._make_df([
            {"name": "Ali Hassan", "email": "ali@example.com", "company": "TechCorp"},
            {"name": "Sara Khan",  "email": "sara@example.com"},
        ])
        result = validate_contacts_df(df)
        assert result["valid"] is True
        assert len(result["valid_rows"]) == 2
        assert len(result["invalid_rows"]) == 0

    def test_missing_email_column(self):
        df = self._make_df([{"name": "Ali Hassan"}])
        result = validate_contacts_df(df)
        assert "error" in result
        assert "email" in result["error"]

    def test_missing_name_column(self):
        df = self._make_df([{"email": "ali@example.com"}])
        result = validate_contacts_df(df)
        assert "error" in result
        assert "name" in result["error"]

    def test_invalid_email(self):
        df = self._make_df([{"name": "Ali", "email": "not-an-email"}])
        result = validate_contacts_df(df)
        assert len(result["invalid_email_rows"]) == 1

    def test_duplicate_email(self):
        df = self._make_df([
            {"name": "Ali",  "email": "ali@example.com"},
            {"name": "Ali2", "email": "ali@example.com"},
        ])
        result = validate_contacts_df(df)
        assert len(result["duplicate_emails"]) == 1

    def test_missing_email_value(self):
        df = self._make_df([
            {"name": "Ali",  "email": ""},
            {"name": "Sara", "email": "sara@example.com"},
        ])
        result = validate_contacts_df(df)
        assert len(result["missing_email_rows"]) == 1

    def test_mixed_valid_invalid(self):
        df = self._make_df([
            {"name": "Ali",  "email": "ali@example.com"},
            {"name": "Sara", "email": "not-valid"},
            {"name": "Raza", "email": "raza@example.com"},
        ])
        result = validate_contacts_df(df)
        assert len(result["valid_rows"]) == 2
        assert len(result["invalid_rows"]) == 1

    def test_column_normalization(self):
        df = pd.DataFrame([{"Name": "Ali", "Email": "ali@example.com"}])
        df = normalize_columns(df)
        assert "name" in df.columns
        assert "email" in df.columns

    def test_column_with_spaces(self):
        df = pd.DataFrame([{"Full Name": "Ali", "Email Address": "ali@example.com"}])
        df = normalize_columns(df)
        assert "full_name" in df.columns
        assert "email_address" in df.columns
