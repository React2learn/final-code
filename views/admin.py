import streamlit as st
import requests
from views.utilis import get_auth_headers

st.title("⚙️ Admin Control Panel")
st.markdown("---")

st.subheader("📝 Register a New Administrator")
st.write("Use this form to add another admin to the database. Only logged-in administrators have access to this page.")

BASE_URL = "http://127.0.0.1:8000"

with st.form("admin_registration_form"):
    new_username = st.text_input("Username", placeholder="e.g. admin2")
    new_email = st.text_input("Email Address", placeholder="e.g. admin2@bank.internal")
    new_password = st.text_input("Password", type="password")
    new_confirm = st.text_input("Confirm Password", type="password")
    
    submit_button = st.form_submit_button("Register Administrator", use_container_width=True)

if submit_button:
    if not new_username or not new_password:
        st.warning("⚠️ Username and password are required.")
    elif new_password != new_confirm:
        st.error("❌ Passwords do not match.")
    else:
        with st.spinner("Creating account..."):
            try:
                headers = get_auth_headers()
                res = requests.post(
                    f"{BASE_URL}/api/register",
                    json={
                        "username": new_username.strip(),
                        "password": new_password,
                        "email": new_email.strip()
                    },
                    headers=headers
                )
                
                if res.status_code == 200:
                    st.success(f"🎉 New administrator **{new_username}** registered successfully!")
                    st.rerun()
                else:
                    err_detail = res.json().get("detail", "Failed to register administrator.")
                    st.error(f"❌ Error: {err_detail}")
            except Exception as e:
                st.error(f"❌ Connection error: {e}")

st.markdown("---")
st.subheader("👥 Current Administrators")

# Fetch all users
headers = get_auth_headers()
try:
    res = requests.get(f"{BASE_URL}/api/users", headers=headers)
    if res.status_code == 200:
        users_list = res.json()
        
        if users_list:
            for user in users_list:
                cols = st.columns([2, 3, 1, 1])
                cols[0].write(f"👤 **{user['username']}**")
                cols[1].write(f"📧 {user['email'] or 'N/A'}")
                cols[2].write(f"`{user['role']}`")
                
                is_self = user['username'] == st.session_state.get('username')
                if is_self:
                    cols[3].button("🗑️ Delete", key=f"del_{user['username']}", disabled=True, help="You cannot delete yourself")
                else:
                    if cols[3].button("🗑️ Delete", key=f"del_{user['username']}", type="secondary"):
                        try:
                            del_res = requests.delete(f"{BASE_URL}/api/users/{user['username']}", headers=headers)
                            if del_res.status_code == 200:
                                st.success(f"Deleted user {user['username']} successfully!")
                                st.rerun()
                            else:
                                err = del_res.json().get("detail", "Failed to delete user.")
                                st.error(f"Error: {err}")
                        except Exception as e:
                            st.error(f"Error connecting to server: {e}")
        else:
            st.info("No admin accounts found.")
    else:
        st.error("Could not fetch user list.")
except Exception as e:
    st.error(f"Error connecting to backend: {e}")
