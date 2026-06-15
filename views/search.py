import streamlit as st
import pandas as pd
import os

# --- Helper Functions ---
@st.cache_data
def load_full_dataset():
    paths = [
        "backend/consumer_complaints_clean_5000.csv",
        "consumer_complaints_clean_5000.csv",
        "../backend/consumer_complaints_clean_5000.csv"
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

# --- Search Section ---
st.subheader("Lookup Existing Complaint by ID")
complaint_id = st.text_input("Enter Complaint ID", placeholder="e.g., 1879220")

if st.button("Fetch Details"):
    df = load_full_dataset()
    
    if df.empty:
        st.error("Dataset could not be loaded. Please check file paths.")
    elif not complaint_id:
        st.warning("Please enter a Complaint ID.")
    else:
        # Filter by ID
        result = df[df['Complaint ID'].astype(str) == str(complaint_id)]
        
        if not result.empty:
            st.success("Record Found!")
            record = result.iloc[0]
            
            # --- Header ---
            st.subheader(f"Details for Complaint ID: {record['Complaint ID']}")
            st.divider() # Added divider for clean separation
            
            # --- Display Fields ---
            with st.container():
                record_dict = record.to_dict()
                
                # We separate the narrative from other fields for better visual flow
                narrative = record_dict.pop('Consumer complaint narrative', None)
                
                # 1. Show all other metadata first
                cols = st.columns(2)
                for i, (column, value) in enumerate(record_dict.items()):
                    if pd.notna(value):
                        with cols[i % 2]:
                            st.write(f"**{column}:** {value}")
                
                # 2. Add extra spacing before the narrative
                st.write("") 
                st.write("") 
                
                # 3. Show narrative with custom styling
                if narrative:
                    st.write("**Consumer complaint narrative:**")
                    st.markdown(
                        f"""
                        <div style="background-color: oklch(0.27 0.01 286); 
                                    color: #cccccc; 
                                    padding: 20px; 
                                    border-radius: 8px; 
                                    border-left: 6px solid #888888;
                                    line-height: 1.6;">
                            {narrative}
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
        else:
            st.error("No record found with that ID.")