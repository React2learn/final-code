import streamlit as st
import pandas as pd
import os

# --- Helper Functions ---
@st.cache_data
def load_full_dataset():
    paths = [
        "backend/new_clean_dataset.csv",
         "new_clean_dataset.csv",
         "../backend/new_clean_dataset.csv"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return pd.read_csv(p)
            except Exception:
                continue
    return pd.DataFrame()

# --- Page Layout ---
st.title("Banking Complaint Management System")
st.subheader("Lookup Existing Complaint by ID")

# --- Search Section ---
col1, col2 = st.columns([3, 1])
with col1:
    complaint_id = st.text_input("Enter Complaint ID", placeholder="e.g., 1879220", label_visibility="collapsed")
with col2:
    fetch = st.button("Fetch Details", use_container_width=True)

if fetch:
    df = load_full_dataset()

    if df.empty:
        st.error("Dataset could not be loaded. Please check file paths.")
    elif not complaint_id:
        st.warning("Please enter a Complaint ID.")
    else:
        result = df[df['Complaint ID'].astype(str) == str(complaint_id)]

        if not result.empty:
            st.success("Record Found!")
            record = result.iloc[0]
            record_dict = record.to_dict()

            # Separate narrative
            narrative = record_dict.pop('Consumer complaint narrative', None)

            # Build metadata table
            table_data = [
                {"Field": k, "Value": str(v)}
                for k, v in record_dict.items()
                if pd.notna(v)
            ]
            st.divider()
            st.markdown(f"**Complaint ID:** {record['Complaint ID']}")
            st.table(pd.DataFrame(table_data).set_index("Field"))

            # Narrative below table
            if narrative and pd.notna(narrative):
                st.divider()
                st.markdown("**Consumer Complaint Narrative**")
                st.text_area("", value=narrative, height=200, disabled=True, label_visibility="collapsed")
        else:
            st.error("No record found with that ID.")
 