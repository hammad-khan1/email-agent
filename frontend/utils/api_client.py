"""
HTTP client for communicating with the FastAPI backend.
All frontend pages use this module to make API calls.
"""

import streamlit as st
import httpx
from typing import Optional, Any

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0


def get_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, params: Optional[dict] = None) -> Optional[Any]:
    try:
        r = httpx.get(f"{BASE_URL}{path}", headers=get_headers(), params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_post(path: str, data: dict = None, files=None) -> Optional[Any]:
    try:
        if files:
            r = httpx.post(f"{BASE_URL}{path}", headers=get_headers(), files=files, timeout=TIMEOUT)
        else:
            r = httpx.post(f"{BASE_URL}{path}", headers=get_headers(), json=data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_put(path: str, data: dict) -> Optional[Any]:
    try:
        r = httpx.put(f"{BASE_URL}{path}", headers=get_headers(), json=data, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_delete(path: str) -> Optional[Any]:
    try:
        r = httpx.delete(f"{BASE_URL}{path}", headers=get_headers(), timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_download(path: str) -> Optional[bytes]:
    try:
        r = httpx.get(f"{BASE_URL}{path}", headers=get_headers(), timeout=60.0)
        r.raise_for_status()
        return r.content
    except Exception as e:
        st.error(f"Download error: {e}")
        return None
