"""
AI HR Email Automation Agent — Streamlit Frontend
Main entry point with sidebar navigation and login gate.
"""

import streamlit as st

# Must be first Streamlit call
st.set_page_config(
    page_title="HR Email Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

from frontend.utils.api_client import api_post, api_get
from frontend.pages import (
    dashboard,
    contacts,
    send_email,
    templates,
    logs,
    reports,
    settings,
    ai_assistant,
    gmail_connect,
)


# ─────────────────────────────────────────────
# Global CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --primary: #1E3A5F;
        --accent:  #2E86C1;
        --light:   #EEF2F7;
        --success: #27AE60;
        --danger:  #E74C3C;
    }
    [data-testid="stSidebar"] {
        background: var(--primary) !important;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    .stButton > button {
        background: var(--accent);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.4rem 1.2rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: var(--primary);
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid var(--accent);
    }
    .metric-card h3 { color: var(--primary); font-size: 2rem; margin: 0; }
    .metric-card p  { color: #666; margin: 0; font-size: 0.9rem; }
    h1, h2, h3 { color: var(--primary) !important; }
    .status-sent    { color: var(--success); font-weight: bold; }
    .status-failed  { color: var(--danger); font-weight: bold; }
    .status-pending { color: #F39C12; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state defaults
# ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "token" not in st.session_state:
    st.session_state.token = ""
if "username" not in st.session_state:
    st.session_state.username = ""


# ─────────────────────────────────────────────
# Login Screen
# ─────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0;'>
            <h1 style='font-size:2.5rem;'>📧 HR Email Agent</h1>
            <p style='color:#666; font-size:1.1rem;'>AI-Powered Email Automation for HR Teams</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="admin")
            password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Login →", use_container_width=True)

        if submit:
            result = api_post("/auth/login", {"username": username, "password": password})
            if result and "access_token" in result:
                st.session_state.logged_in = True
                st.session_state.token = result["access_token"]
                st.session_state.username = result["username"]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown("""
        <div style='text-align:center; margin-top:1rem; color:#999; font-size:0.8rem;'>
            Default credentials: admin / admin123
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────
def show_sidebar() -> str:
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center; padding: 1rem 0;'>
            <h2 style='color:white !important; font-size:1.3rem;'>📧 HR Email Agent</h2>
            <p style='color:#ccc !important; font-size:0.85rem;'>Welcome, {st.session_state.username}</p>
        </div>
        <hr style='border-color:#ffffff33;'>
        """, unsafe_allow_html=True)

        pages = {
            "📊 Dashboard":       "dashboard",
            "👥 Contacts":        "contacts",
            "📨 Send Emails":     "send_email",
            "📝 Templates":       "templates",
            "🤖 AI Assistant":    "ai_assistant",
            "🔗 Gmail Connect":   "gmail_connect",
            "📋 Email Logs":      "logs",
            "📈 Reports":         "reports",
            "⚙️ Settings":        "settings",
        }

        if "current_page" not in st.session_state:
            st.session_state.current_page = "dashboard"

        for label, page_key in pages.items():
            is_active = st.session_state.current_page == page_key
            btn_style = "background:#2E86C1 !important;" if is_active else ""
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

        st.markdown("<hr style='border-color:#ffffff33;'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.token = ""
            st.rerun()

    return st.session_state.current_page


# ─────────────────────────────────────────────
# Page Router
# ─────────────────────────────────────────────
PAGE_MAP = {
    "dashboard":    dashboard.show,
    "contacts":     contacts.show,
    "send_email":   send_email.show,
    "templates":    templates.show,
    "ai_assistant": ai_assistant.show,
    "gmail_connect": gmail_connect.show,
    "logs":         logs.show,
    "reports":      reports.show,
    "settings":     settings.show,
}


def main():
    if not st.session_state.logged_in:
        show_login()
        return

    current_page = show_sidebar()
    page_fn = PAGE_MAP.get(current_page, dashboard.show)
    page_fn()


if __name__ == "__main__":
    main()
