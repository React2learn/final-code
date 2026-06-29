import streamlit as st
import pandas as pd
import os
import requests

#  Config 
API_BASE = st.session_state.get("api_base", "http://127.0.0.1:8000")


#  Helper Functions 
@st.cache_data
def load_full_dataset():
    paths = [
        "backend/new_clean_dataset.csv",
        "new_clean_dataset.csv",
        "../backend/new_clean_dataset.csv",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return pd.read_csv(p)
            except Exception:
                continue
    return pd.DataFrame()


def get_auth_headers():
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def fetch_resolution(complaint_id: str):
    """Call /api/resolve and return the response dict or raise on error."""
    headers = get_auth_headers()
    payload = {"query": str(complaint_id)}
    resp = requests.post(f"{API_BASE}/api/resolve", json=payload, headers=headers, timeout=300)
    resp.raise_for_status()
    return resp.json()


# Page Layout 
st.title("Banking Complaint Management System")
st.subheader("Lookup Existing Complaint by ID")

#  Search Section 
col1, col2 = st.columns([3, 1])
with col1:
    complaint_id = st.text_input(
        "Enter Complaint ID", placeholder="e.g., 1879220", label_visibility="collapsed"
    )
with col2:
    fetch = st.button("Fetch Details", use_container_width=True)

if fetch:
    df = load_full_dataset()
    if df.empty:
        st.error("Dataset could not be loaded. Please check file paths.")
    elif not complaint_id:
        st.warning("Please enter a Complaint ID.")
    else:
        result = df[df["Complaint ID"].astype(str) == str(complaint_id)]
        if not result.empty:
            # Store the found record in session state so it persists across reruns
            record_dict = result.iloc[0].to_dict()
            st.session_state["fetched_record"] = record_dict
            st.session_state["fetched_complaint_id"] = complaint_id
            # Clear any old resolution when fetching a new complaint
            st.session_state.pop("last_resolution", None)
        else:
            st.session_state.pop("fetched_record", None)
            st.session_state.pop("fetched_complaint_id", None)
            st.error("No record found with that ID.")

# Display fetched record (persists across reruns) 
if "fetched_record" in st.session_state:
    record_dict = st.session_state["fetched_record"].copy()
    fetched_id = st.session_state["fetched_complaint_id"]

    st.success("Record Found!")

    # Separate narrative
    narrative = record_dict.pop("Consumer complaint narrative", None)

    # Build metadata table
    table_data = [
        {"Field": k, "Value": str(v)}
        for k, v in record_dict.items()
        if pd.notna(v)
    ]

    st.divider()
    st.markdown(f"**Complaint ID:** {fetched_id}")
    st.table(pd.DataFrame(table_data).set_index("Field"))

    # Narrative below table
    if narrative and pd.notna(narrative):
        st.divider()
        st.markdown("**Consumer Complaint Narrative**")
        st.text_area(
            "",
            value=narrative,
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )

    #  Get Resolution Button
    st.divider()
    if st.button("🔍 Get AI Resolution", type="primary", use_container_width=True):
        with st.spinner("Generating resolution... this may take a moment."):
            try:
                data = fetch_resolution(fetched_id)
                st.session_state["last_resolution"] = data
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    st.error("Session expired. Please log in again.")
                elif e.response.status_code == 404:
                    st.error(f"Complaint ID {fetched_id} not found in the resolution database.")
                else:
                    st.error(f"API error: {e.response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend. Make sure the server is running.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

# --- Display Resolution if available ---
if "last_resolution" in st.session_state:
    res = st.session_state["last_resolution"]
    # st.divider()
    # st.subheader("🤖 AI-Generated Resolution")

    # Metadata summary
    # meta_cols = st.columns(3)
    # with meta_cols[0]:
    #     st.metric("Company", res.get("matched_company", "—"))
    # with meta_cols[1]:
    #     st.metric("Product", res.get("matched_product", "—"))
    # with meta_cols[2]:
    #     st.metric("Company Response", res.get("company_response", "—"))

    # extra_cols = st.columns(3)
    # with extra_cols[0]:
    #     st.metric("State", res.get("state", "—"))
    # with extra_cols[1]:
    #     st.metric("Timely Response", res.get("timely_response", "—"))
    # with extra_cols[2]:
    #     st.metric("Consumer Disputed", res.get("consumer_disputed", "—"))

    st.divider()
    st.markdown(res.get("resolution_markdown", "No resolution text returned."))

    # Clear button
    if st.button("Clear Resolution", type="secondary"):
        del st.session_state["last_resolution"]
        st.rerun()