"""Dashboard page — stats, charts, overview."""
import streamlit as st
import pandas as pd
from frontend.utils.api_client import api_get


def metric_card(label: str, value, color: str = "#2E86C1") -> str:
    return f"""
    <div class='metric-card' style='border-left-color:{color};'>
        <h3 style='color:{color} !important;'>{value}</h3>
        <p>{label}</p>
    </div>
    """


def show():
    st.title("📊 Dashboard")
    st.markdown("Real-time overview of your HR email campaigns.")

    stats = api_get("/reports/stats") or {}
    gmail = api_get("/gmail/status") or {}

    # Gmail connection banner
    if gmail.get("connected"):
        st.success(f"✅ Gmail connected: **{gmail['email']}**")
    else:
        st.warning("⚠️ Gmail not connected. Go to **Gmail Connect** to authenticate.")

    st.markdown("<br>", unsafe_allow_html=True)

    # KPI Cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    cards = [
        (col1, "Total Contacts",  stats.get("total_contacts", 0),  "#1E3A5F"),
        (col2, "Emails Sent",     stats.get("sent", 0),            "#27AE60"),
        (col3, "Pending",         stats.get("pending", 0),         "#F39C12"),
        (col4, "Failed",          stats.get("failed", 0),          "#E74C3C"),
        (col5, "Scheduled",       stats.get("scheduled", 0),       "#8E44AD"),
        (col6, "Success Rate",    f"{stats.get('success_rate', 0)}%", "#2E86C1"),
    ]
    for col, label, value, color in cards:
        with col:
            st.markdown(metric_card(label, value, color), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📬 Email Status Breakdown")
        sent = stats.get("sent", 0)
        failed = stats.get("failed", 0)
        pending = stats.get("pending", 0)
        scheduled = stats.get("scheduled", 0)
        if sent + failed + pending + scheduled > 0:
            chart_data = pd.DataFrame({
                "Status": ["Sent", "Failed", "Pending", "Scheduled"],
                "Count":  [sent, failed, pending, scheduled],
            })
            st.bar_chart(chart_data.set_index("Status"), color=["#2E86C1"])
        else:
            st.info("No email data yet.")

    with col_right:
        st.subheader("📋 Recent Activity")
        logs = api_get("/emails/logs", {"limit": 8}) or []
        if logs:
            for log in logs:
                status = log.get("status", "")
                icon = "✅" if status == "sent" else ("❌" if status == "failed" else "⏳")
                st.markdown(
                    f"{icon} **{log.get('recipient_name', log.get('recipient_email', ''))}** "
                    f"— {log.get('subject', '')[:40]}..."
                )
        else:
            st.info("No recent emails.")

    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("👥 Manage Contacts", use_container_width=True):
            st.session_state.current_page = "contacts"
            st.rerun()
    with q2:
        if st.button("📨 Send Emails", use_container_width=True):
            st.session_state.current_page = "send_email"
            st.rerun()
    with q3:
        if st.button("🤖 AI Assistant", use_container_width=True):
            st.session_state.current_page = "ai_assistant"
            st.rerun()
    with q4:
        if st.button("📈 View Reports", use_container_width=True):
            st.session_state.current_page = "reports"
            st.rerun()
