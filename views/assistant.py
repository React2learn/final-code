import streamlit as st
import requests
from views.utilis import get_auth_headers

col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🤖 AI Assistant")
with col_btn:
    st.write("")  # spacing
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_complaint_id = None
        st.rerun()

# Initialize chat history and active complaint tracking
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_complaint_id" not in st.session_state:
    st.session_state.active_complaint_id = None

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Show active complaint context
if st.session_state.active_complaint_id:
    st.caption(f"🔍 Active complaint: `{st.session_state.active_complaint_id}`")

# Chat input
if prompt := st.chat_input("Ask about a complaint or type a Complaint ID..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Analyzing report..."):
        try:
            # Always send the active complaint_id so follow-up questions stay in context
            payload = {"query": prompt}
            if st.session_state.active_complaint_id:
                payload["complaint_id"] = st.session_state.active_complaint_id

            response = requests.post(
                "http://127.0.0.1:8000/api/chat",
                json=payload,
                headers=get_auth_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("resolution_markdown", "No answer returned.")
                # Update active complaint if the response resolved a new one
                if data.get("complaint_id"):
                    st.session_state.active_complaint_id = data["complaint_id"]
            else:
                answer = "Error: Could not retrieve an answer. Ensure a complaint has been resolved first."

        except Exception as e:
            answer = f"Error: {str(e)}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Append assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})
