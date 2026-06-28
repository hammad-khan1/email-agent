"""Gmail OAuth connection page."""
import streamlit as st
from frontend.utils.api_client import api_get, api_post


def show():
    st.title("🔗 Gmail Connection")

    status = api_get("/gmail/status") or {}

    if status.get("connected"):
        st.success(f"✅ Gmail is connected as: **{status['email']}**")
        st.markdown("Your emails will be sent from this Gmail account.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reconnect Gmail", use_container_width=True):
                _start_oauth()
        with col2:
            if st.button("❌ Disconnect Gmail", use_container_width=True, type="primary"):
                result = api_post("/gmail/disconnect", {})
                if result:
                    st.success("Gmail disconnected.")
                    st.rerun()
    else:
        st.warning("Gmail is not connected. Connect your Gmail account to start sending emails.")
        st.markdown("""
        ### How it works:
        1. Click **Connect Gmail** below
        2. You'll be redirected to Google's login page
        3. Grant the app permission to send emails
        4. You'll be redirected back automatically
        
        > 🔒 We use **OAuth 2.0** — your password is never stored.
        """)

        if st.button("🔗 Connect Gmail Account", type="primary", use_container_width=True):
            _start_oauth()

    st.markdown("---")
    st.subheader("📋 Gmail Setup Guide")
    with st.expander("How to set up Gmail API credentials"):
        st.markdown("""
        1. Go to [Google Cloud Console](https://console.cloud.google.com)
        2. Create a new project or select existing
        3. Enable **Gmail API** under APIs & Services → Library
        4. Go to **APIs & Services → Credentials**
        5. Create **OAuth 2.0 Client ID** (Web Application type)
        6. Add `http://localhost:8000/auth/gmail/callback` as Authorized Redirect URI
        7. Download credentials and copy `client_id` and `client_secret` to your `.env` file
        8. Restart the backend server
        """)


def _start_oauth():
    result = api_get("/gmail/auth-url")
    if result and result.get("auth_url"):
        st.markdown(f"[👉 Click here to authorize Gmail]({result['auth_url']})")
        st.info("After authorizing, come back and refresh this page.")
    else:
        st.error("Could not get auth URL. Make sure GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET are set in .env")
