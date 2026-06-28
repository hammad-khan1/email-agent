"""Email Templates management page."""
import streamlit as st
from frontend.utils.api_client import api_get, api_post, api_put, api_delete


def show():
    st.title("📝 Email Templates")

    tab1, tab2 = st.tabs(["📋 My Templates", "➕ Create Template"])

    with tab1:
        templates = api_get("/templates/") or []
        if not templates:
            st.info("No templates yet. Create one in the next tab.")
            return

        for tmpl in templates:
            with st.expander(f"📄 {tmpl['name']} — {tmpl['subject'][:60]}"):
                st.markdown(f"**Subject:** {tmpl['subject']}")
                st.markdown("**Body:**")
                st.html(tmpl["body_html"][:500] + ("..." if len(tmpl["body_html"]) > 500 else ""))

                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("📋 Duplicate", key=f"dup_{tmpl['id']}"):
                        api_post(f"/templates/{tmpl['id']}/duplicate", {})
                        st.success("Duplicated!")
                        st.rerun()
                with c2:
                    if st.button("✏️ Edit", key=f"edit_{tmpl['id']}"):
                        st.session_state[f"editing_{tmpl['id']}"] = True

                    if st.session_state.get(f"editing_{tmpl['id']}"):
                        new_name    = st.text_input("Name:", tmpl["name"],    key=f"n_{tmpl['id']}")
                        new_subject = st.text_input("Subject:", tmpl["subject"], key=f"s_{tmpl['id']}")
                        new_body    = st.text_area("Body HTML:", tmpl["body_html"], height=200, key=f"b_{tmpl['id']}")
                        if st.button("💾 Save", key=f"save_{tmpl['id']}"):
                            api_put(f"/templates/{tmpl['id']}", {
                                "name": new_name,
                                "subject": new_subject,
                                "body_html": new_body,
                            })
                            st.session_state[f"editing_{tmpl['id']}"] = False
                            st.success("Saved!")
                            st.rerun()
                with c3:
                    if st.button("🗑️ Delete", key=f"del_{tmpl['id']}"):
                        api_delete(f"/templates/{tmpl['id']}")
                        st.success("Deleted!")
                        st.rerun()

    with tab2:
        st.markdown("Use **{{Name}}**, **{{Domain}}**, **{{Company}}**, etc. as placeholders.")
        with st.form("create_template"):
            name    = st.text_input("Template Name")
            subject = st.text_input("Subject")
            body    = st.text_area("Body HTML", height=300, value="""<p>Dear <strong>{{Name}}</strong>,</p>
<p>Congratulations on your <strong>{{Domain}}</strong> internship at <strong>{{Company}}</strong>!</p>
<p>Reporting Date: <strong>{{Joining Date}}</strong></p>
<br>
<p>Best regards,<br><strong>HR Team</strong></p>""")
            submit  = st.form_submit_button("💾 Save Template", use_container_width=True)

        if submit:
            if not name or not subject:
                st.error("Name and subject are required.")
            else:
                result = api_post("/templates/", {"name": name, "subject": subject, "body_html": body})
                if result:
                    st.success(f"Template '{name}' saved!")
