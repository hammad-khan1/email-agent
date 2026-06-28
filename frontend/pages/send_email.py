cat > /Users/apple/Desktop/email-agent/frontend/pages/send_email.py << 'ENDOFFILE'
"""Send Email page."""
import streamlit as st
from datetime import datetime, timedelta
from frontend.utils.api_client import api_get, api_post

DEFAULT_SUBJECT = "Congratulations on Your Internship at {{Company}}"
DEFAULT_BODY = """<p>Dear <strong>{{Name}}</strong>,</p>

<p>Congratulations! You have been selected for the 
<strong>{{Domain}}</strong> internship at <strong>{{Company}}</strong>.</p>

<p>Reporting Date: {{Joining Date}}<br>
Location: {{Location}}<br>
Department: {{Department}}</p>

<p>Please confirm your acceptance by replying to this email.</p>
<br>
<p>Best regards,<br><strong>HR Team</strong></p>"""


def show():
    st.title("📨 Send Emails")

    gmail = api_get("/gmail/status") or {}
    if not gmail.get("connected"):
        st.error("Gmail not connected! Go to Gmail Connect first.")
        return

    st.success(f"Sending from: {gmail.get('email')}")

    contacts = api_get("/contacts/") or []
    if not contacts:
        st.warning("No contacts found.")
        return

    contact_map = {f"{c['name']} ({c['email']})": c['id'] for c in contacts}

    st.subheader("1. Select Contacts")
    select_all = st.checkbox("Select all contacts")
    if select_all:
        selected_ids = list(contact_map.values())
        st.info(f"{len(selected_ids)} contacts selected.")
    else:
        selected_labels = st.multiselect("Pick contacts:", list(contact_map.keys()))
        selected_ids = [contact_map[l] for l in selected_labels]

    st.subheader("2. Compose Email")
    sender_name = st.text_input("Sender Name:", value="HR Team")
    subject_input = st.text_input("Subject:", value=DEFAULT_SUBJECT)
    body_input = st.text_area("Body (HTML):", value=DEFAULT_BODY, height=280)

    if selected_ids:
        first = next((c for c in contacts if c['id'] == selected_ids[0]), None)
        if first and st.button("👁️ Preview"):
            preview = body_input
            replacements = {
                "{{Name}}": first.get("name",""),
                "{{Domain}}": first.get("domain",""),
                "{{Company}}": first.get("company",""),
                "{{Joining Date}}": first.get("joining_date",""),
                "{{Location}}": first.get("location",""),
                "{{Department}}": first.get("department",""),
            }
            for k, v in replacements.items():
                preview = preview.replace(k, v)
            st.markdown("**Preview:**")
            st.html(preview)

    st.subheader("3. Send")
    st.info(f"Will send to {len(selected_ids)} recipient(s)")

    if st.button("🚀 Send Emails Now", type="primary", use_container_width=True):
        if not selected_ids:
            st.error("Select at least one contact.")
        elif not subject_input.strip():
            st.error("Subject cannot be empty.")
        elif not body_input.strip():
            st.error("Body cannot be empty.")
        else:
            with st.spinner("Sending..."):
                result = api_post("/emails/send", {
                    "contact_ids": selected_ids,
                    "subject_template": subject_input,
                    "body_template": body_input,
                    "sender_name": sender_name,
                    "use_ai": False,
                })
                if result:
                    st.success(f"Done! {result.get('sent',0)} sent | {result.get('failed',0)} failed")
ENDOFFILE