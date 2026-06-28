"""Email Logs page — view, search, filter, retry."""
import streamlit as st
import pandas as pd
from frontend.utils.api_client import api_get, api_post


def show():
    st.title("📋 Email Logs")

    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search recipient or subject")
    with col2:
        status_filter = st.selectbox("Filter by status:", ["All", "sent", "failed", "pending", "scheduled"])
    with col3:
        limit = st.selectbox("Show:", [50, 100, 200, 500], index=1)

    params = {"limit": limit}
    if search:
        params["search"] = search
    if status_filter != "All":
        params["status"] = status_filter

    logs = api_get("/emails/logs", params) or []

    if logs:
        df = pd.DataFrame(logs)
        display_cols = ["id", "recipient_name", "recipient_email", "subject", "status", "sent_at", "retry_count", "error_message"]
        display_cols = [c for c in display_cols if c in df.columns]

        # Color status
        def color_status(val):
            colors = {"sent": "background-color: #d4edda", "failed": "background-color: #f8d7da", "pending": "background-color: #fff3cd"}
            return colors.get(val, "")

        styled = df[display_cols].style.applymap(color_status, subset=["status"])
        st.dataframe(styled, use_container_width=True, height=450)
        st.caption(f"Showing {len(logs)} log entries")
    else:
        st.info("No email logs found.")

    st.markdown("---")
    col_retry, col_export = st.columns(2)
    with col_retry:
        if st.button("🔄 Retry All Failed Emails", use_container_width=True):
            result = api_post("/emails/retry-failed", {})
            if result:
                st.success(f"Retried {result.get('retried', 0)} | Succeeded: {result.get('succeeded', 0)}")

    with col_export:
        st.download_button(
            label="📥 Export Logs as CSV",
            data=b"Use the Reports page to export",
            file_name="logs.csv",
            mime="text/csv",
        )
