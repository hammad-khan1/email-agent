"""Reports page — stats, charts, export."""
import streamlit as st
import pandas as pd
from frontend.utils.api_client import api_get, api_download


def show():
    st.title("📈 Reports & Analytics")

    stats = api_get("/reports/stats") or {}

    # Stats overview
    cols = st.columns(4)
    metrics = [
        ("Total Emails", stats.get("total_emails", 0)),
        ("Sent",         stats.get("sent", 0)),
        ("Failed",       stats.get("failed", 0)),
        ("Success Rate", f"{stats.get('success_rate', 0)}%"),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)

    st.markdown("---")

    # Charts
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📊 Status Distribution")
        data = {
            "Sent":      stats.get("sent", 0),
            "Failed":    stats.get("failed", 0),
            "Pending":   stats.get("pending", 0),
            "Scheduled": stats.get("scheduled", 0),
        }
        if sum(data.values()) > 0:
            df = pd.DataFrame(list(data.items()), columns=["Status", "Count"])
            st.bar_chart(df.set_index("Status"))
        else:
            st.info("No data yet.")

    with col_right:
        st.subheader("📬 Email Summary")
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | Total Contacts | {stats.get('total_contacts', 0)} |
        | Total Emails Logged | {stats.get('total_emails', 0)} |
        | Successfully Sent | {stats.get('sent', 0)} |
        | Failed | {stats.get('failed', 0)} |
        | Pending | {stats.get('pending', 0)} |
        | Scheduled | {stats.get('scheduled', 0)} |
        | **Success Rate** | **{stats.get('success_rate', 0)}%** |
        """)

    # Export
    st.markdown("---")
    st.subheader("📥 Export Reports")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Download Excel Report", use_container_width=True):
            data = api_download("/reports/export/excel")
            if data:
                st.download_button(
                    "💾 Save Excel",
                    data=data,
                    file_name="hr_email_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    with col2:
        if st.button("📄 Download CSV Report", use_container_width=True):
            data = api_download("/reports/export/csv")
            if data:
                st.download_button("💾 Save CSV", data=data, file_name="hr_email_report.csv", mime="text/csv")

    with col3:
        if st.button("📑 Download PDF Report", use_container_width=True):
            data = api_download("/reports/export/pdf")
            if data:
                st.download_button("💾 Save PDF", data=data, file_name="hr_email_report.pdf", mime="application/pdf")
