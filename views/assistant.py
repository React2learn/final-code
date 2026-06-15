import streamlit as st
import requests
from views.utilis import get_auth_headers

st.title("🤖 AI Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about the last resolution..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Analyzing report..."):
        try:
            # Call the new FastAPI chat endpoint
            response = requests.post(
                "http://127.0.0.1:8000/api/chat", 
                json={"query": prompt},
                headers=get_auth_headers()
            )
            
            if response.status_code == 200:
                answer = response.json()["resolution_markdown"]
            else:
                answer = "Error: Could not retrieve an answer. Ensure a complaint has been resolved first."
        
        except Exception as e:
            answer = f"Error: {str(e)}"

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(answer)

    # Append assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})