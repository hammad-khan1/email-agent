"""AI Assistant page — chat interface for HR email help."""
import streamlit as st
from frontend.utils.api_client import api_post


QUICK_PROMPTS = [
    "Write an internship offer email",
    "Write a rejection email politely",
    "Write a welcome email for a new joiner",
    "Generate an invitation for HR interview",
    "Rewrite this email more professionally",
    "Translate this email to Urdu",
    "Make this email shorter",
]


def show():
    st.title("🤖 AI Email Assistant")
    st.markdown("Ask the AI to **write, rewrite, shorten, translate, or improve** any HR email.")

    if "ai_chat_history" not in st.session_state:
        st.session_state.ai_chat_history = []

    # Quick prompts
    st.subheader("⚡ Quick Actions")
    cols = st.columns(4)
    for i, prompt in enumerate(QUICK_PROMPTS):
        with cols[i % 4]:
            if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                st.session_state.ai_pending_prompt = prompt

    st.markdown("---")

    # Chat display
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    # Input
    pending = st.session_state.pop("ai_pending_prompt", None)
    user_input = st.chat_input("Ask the AI (e.g. 'Write an internship email for Ali')") or pending

    if user_input:
        st.session_state.ai_chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI is writing..."):
                result = api_post("/ai/assistant", {"message": user_input})
                if result:
                    response = result.get("response", "Sorry, something went wrong.")
                else:
                    response = "⚠️ Could not connect to AI. Check your Gemini API key in .env"
                st.markdown(response, unsafe_allow_html=True)
                st.session_state.ai_chat_history.append({"role": "assistant", "content": response})

    if st.session_state.ai_chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.ai_chat_history = []
            st.rerun()
