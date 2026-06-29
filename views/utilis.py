import requests
import streamlit as st

BASE_URL = "http://127.0.0.1:8000"


def get_auth_headers():
    headers = {}
    if "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    return headers


def resolve_complaint(complaint_text):
    response = requests.post(
        f"{BASE_URL}/api/resolve",
        json={"query": complaint_text},
        headers=get_auth_headers(),
    )

    if response.status_code == 200:
        return response.json()

    return {"error": response.text}


def get_complaints():
    response = requests.get(
        f"{BASE_URL}/api/all-complaints", headers=get_auth_headers()
    )
    if response.status_code == 200:
        return response.json()
    return []
