"""Settings page — theme, sender, rate limits, signature."""
import streamlit as st
from frontend.utils.api_client import api_get, api_post


def show():
    st.title("⚙️ Settings")

    current = api_get("/settings/") or {}

    with st.form("settings_form"):
        st.subheader("📧 Email Settings")
        sender_name = st.text_input(
            "Default Sender Name",
            value=current.get("default_sender_name", "HR Team"),
        )
        max_per_min = st.slider(
            "Maximum Emails Per Minute",
            min_value=1, max_value=60,
            value=int(current.get("max_emails_per_minute", 10)),
        )

        st.subheader("✍️ Default Signature")
        signature = st.text_area(
            "HTML Signature",
            value=current.get("default_signature", "<p>Best regards,<br><strong>HR Team</strong></p>"),
            height=120,
        )

        st.subheader("🎨 Theme")
        theme = st.selectbox(
            "Color Theme",
            ["Blue (Default)", "Dark", "Light"],
            index=["Blue (Default)", "Dark", "Light"].index(
                current.get("theme", "Blue (Default)")
            ),
        )

        st.subheader("🤖 AI Settings")
        ai_tone = st.selectbox(
            "Default AI Tone",
            ["Professional and Friendly", "Formal", "Warm and Encouraging", "Concise and Direct"],
            index=0,
        )

        submit = st.form_submit_button("💾 Save Settings", use_container_width=True)

    if submit:
        settings_to_save = {
            "default_sender_name": sender_name,
            "max_emails_per_minute": str(max_per_min),
            "default_signature": signature,
            "theme": theme,
            "default_ai_tone": ai_tone,
        }
        for key, value in settings_to_save.items():
            api_post("/settings/", {"key": key, "value": value})
        st.success("✅ Settings saved successfully!")
