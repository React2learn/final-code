import streamlit as st
import requests

st.set_page_config(page_title="Customer Intelligence", layout="wide")

# CSS Styling for Premium Banking Look
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main { background-color: #0f1117; }
.auth-header {
    background: linear-gradient(135deg, #1a1d2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px; padding: 2.5rem; margin-bottom: 2rem;
    border: 1px solid #ffffff10;
    text-align: center;
}
.auth-header h1 { color: #fff; font-size: 2.2rem; font-weight: 700; margin: 0; }
.auth-header p { color: #94a3b8; margin-top: 0.5rem; font-size: 1rem; }
.auth-card {
    background: #1e2235; border: 1px solid #ffffff10;
    border-radius: 14px; padding: 2.5rem; max-width: 450px; margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

BASE_URL = "http://127.0.0.1:8000"

# Initialize auth state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

def show_login_page():
    st.markdown("""
    <div class="auth-header">
      <h1>🔒 Customer Intelligence Platform</h1>
      <p>Secure Banking Portal Login</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Simple centered container
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.subheader("Login to your account")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Sign In", use_container_width=True):
            if login_username and login_password:
                try:
                    res = requests.post(
                        f"{BASE_URL}/api/login",
                        json={"username": login_username, "password": login_password}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.authenticated = True
                        st.session_state.token = data["access_token"]
                        st.session_state.username = data["username"]
                        st.session_state.role = data.get("role")
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error(res.json().get("detail", "Incorrect username or password"))
                except Exception as e:
                    st.error(f"Could not connect to authentication server: {e}")
            else:
                st.warning("Please fill in both fields.")

# Routing based on auth state using st.navigation
if not st.session_state.authenticated:
    login_page = st.Page(show_login_page, title="Login", icon="🔒")
    pg = st.navigation([login_page], position="hidden")
else:
    pages = [
        st.Page("views/dashboard.py", title="dashboard", icon="📊"),
        st.Page("views/Search.py", title=" search", icon="🔍"),
        st.Page("views/assistant.py", title=" assistant", icon="🤖"),
    ]
    if st.session_state.get("role") == "admin":
        pages.append(st.Page("views/admin.py", title=" admin panel", icon="⚙️"))
    pg = st.navigation(pages)

pg.run()