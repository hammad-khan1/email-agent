"""Contacts management page."""
import streamlit as st
import pandas as pd
from frontend.utils.api_client import api_get, api_post, api_put, api_delete


def show():
    st.title("👥 Contact Manager")

    tab1, tab2, tab3 = st.tabs(["📋 All Contacts", "➕ Add Contact", "📤 Import File"])

    # ── Tab 1: List & Search ──────────────────────────────────
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("🔍 Search name or email", "")
        with col2:
            dept_filter = st.text_input("🏢 Filter by department", "")
        with col3:
            company_filter = st.text_input("🏭 Filter by company", "")

        params = {}
        if search:
            params["q"] = search
        if dept_filter:
            params["department"] = dept_filter
        if company_filter:
            params["company"] = company_filter

        contacts = api_get("/contacts/", params) or []

        if contacts:
            df = pd.DataFrame(contacts)
            display_cols = ["name", "email", "department", "domain", "company", "position", "joining_date"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, height=400)
            st.caption(f"Showing {len(contacts)} contacts")

            # Delete
            if st.session_state.get("show_delete"):
                contact_options = {f"{c['name']} ({c['email']})": c['id'] for c in contacts}
                selected = st.selectbox("Select contact to delete:", list(contact_options.keys()))
                if st.button("🗑️ Confirm Delete", type="primary"):
                    result = api_delete(f"/contacts/{contact_options[selected]}")
                    if result:
                        st.success("Contact deleted!")
                        st.session_state.show_delete = False
                        st.rerun()
            else:
                if st.button("🗑️ Delete a Contact"):
                    st.session_state.show_delete = True
                    st.rerun()
        else:
            st.info("No contacts found. Import or add contacts to get started.")

    # ── Tab 2: Add Contact ────────────────────────────────────
    with tab2:
        with st.form("add_contact_form"):
            c1, c2 = st.columns(2)
            name          = c1.text_input("Full Name *")
            email         = c2.text_input("Email Address *")
            department    = c1.text_input("Department")
            domain        = c2.text_input("Domain / Internship Area")
            position      = c1.text_input("Position")
            joining_date  = c2.text_input("Joining Date (e.g. July 15, 2026)")
            company       = c1.text_input("Company")
            location      = c2.text_input("Location")
            submit        = st.form_submit_button("➕ Add Contact", use_container_width=True)

        if submit:
            if not name or not email:
                st.error("Name and Email are required.")
            else:
                result = api_post("/contacts/", {
                    "name": name, "email": email, "department": department,
                    "domain": domain, "position": position, "joining_date": joining_date,
                    "company": company, "location": location,
                })
                if result:
                    st.success(f"Contact '{name}' added successfully!")

    # ── Tab 3: Import File ────────────────────────────────────
    with tab3:
        st.markdown("Upload an **Excel (.xlsx)** or **CSV** file with your contacts.")
        st.markdown("""
        **Required columns:** `name`, `email`
        
        **Optional columns:** `department`, `domain`, `position`, `joining_date`, `company`, `location`
        """)

        uploaded = st.file_uploader("Choose file", type=["xlsx", "xls", "csv"])
        skip_dupes = st.checkbox("Skip duplicate emails", value=True)

        if uploaded:
            # Validate first
            if st.button("🔍 Validate File"):
                result = api_post(
                    "/contacts/upload/validate",
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                )
                if result:
                    st.json(result)
                    if result.get("valid_rows"):
                        st.success(f"✅ {len(result['valid_rows'])} valid rows found")
                    if result.get("invalid_rows"):
                        st.warning(f"⚠️ {len(result['invalid_rows'])} rows have issues")

            if st.button("📥 Import Contacts", type="primary"):
                uploaded.seek(0)
                result = api_post(
                    f"/contacts/upload/import?skip_duplicates={str(skip_dupes).lower()}",
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                )
                if result:
                    st.success(
                        f"Import done! ✅ {result.get('imported', 0)} imported | "
                        f"⏩ {result.get('skipped', 0)} skipped | "
                        f"❌ {result.get('failed', 0)} failed"
                    )
