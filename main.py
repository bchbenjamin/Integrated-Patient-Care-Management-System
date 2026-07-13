"""
main.py — IPCMS Entry Point
Handles routing, top navigation header, login/register, and global CSS.
"""

import __init__
import streamlit as st
import base64
import os
import datetime
from auth import login_user, register_patient, validate_password
from pages import admin_dashboard, doctor_dashboard, patient_dashboard, calendar_view

# --- Layout Configuration ---
st.set_page_config(
    page_title="Ease Health — Integrated Patient Care",
    page_icon="assets/ease_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Helper to load images as base64 ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return ""

ease_logo_b64 = get_base64_of_bin_file("assets/ease_logo.png")

# --- Inject Global CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Inter:wght@300;400;600&display=swap');

:root {
  --color-forest-ink: #0f3e17;
  --color-sage-mist: #b1dbb8;
  --color-keylime-wash: #e1f4df;
  --color-mint-veil: #cfe7d3;
  --color-slate-hush: #b6ced5;
  --color-cream-paper: #fffefc;
  --color-charcoal: #222222;
  --color-border-mist: #efeeeb;
  --color-forest-shadow: #0c2f10;
}

/* Base */
.stApp {
    background-color: var(--color-cream-paper) !important;
}
html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--color-charcoal) !important;
}

/* Hide default Streamlit header & hamburger */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Hide Streamlit sidebar collapse control if any */
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Typography */
h1, h2, h3 {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    color: var(--color-forest-ink) !important;
}
h1 {
    font-size: 48px !important;
    line-height: 1.2 !important;
    letter-spacing: -1.68px !important;
}
h2 {
    font-size: 36px !important;
    line-height: 1.35 !important;
    letter-spacing: -0.4px !important;
}

.eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-forest-ink);
    margin-bottom: 7px;
}

/* Login form */
div[data-testid="stForm"] {
    background-color: var(--color-keylime-wash);
    padding: 56px;
    border-radius: 14px;
    max-width: 500px;
    margin: 6vh auto 0 auto !important;
    box-shadow: none !important;
    border: none !important;
}


/* Inputs */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    border-radius: 7px !important;
    border: 1px solid var(--color-border-mist) !important;
    background-color: var(--color-cream-paper) !important;
    color: var(--color-charcoal) !important;
}

/* Metrics */
div[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 40px !important;
    font-weight: 300 !important;
    color: var(--color-forest-ink) !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 14px !important;
    color: var(--color-charcoal) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    border-bottom: 1px solid var(--color-border-mist);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 12px 18px !important;
    color: var(--color-charcoal) !important;
}
.stTabs [aria-selected="true"] {
    border-bottom: 2px solid var(--color-forest-ink) !important;
    font-weight: 600 !important;
    color: var(--color-forest-ink) !important;
}

/* Dataframe */
.stDataFrame {
    border-radius: 14px !important;
    overflow: hidden;
}

/* Expander */
.streamlit-expanderHeader {
    font-size: 14px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# --- Authentication State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'dashboard'


# ==========================================
# NOT LOGGED IN — LOGIN / REGISTER
# ==========================================
if not st.session_state['logged_in']:
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        login_tab, register_tab = st.tabs(["Sign In", "Register (Patient)"])

        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                if ease_logo_b64:
                    st.markdown(f"""
                    <div style="display:flex; flex-direction:column; align-items:center; margin-bottom: 24px;">
                        <img src="data:image/png;base64,{ease_logo_b64}" width="100" style="margin-bottom:14px;"/>
                        <div class="eyebrow" style="margin-bottom:0;">PORTAL ACCESS</div>
                        <h1 style="margin-top:0; text-align:center; font-size:40px !important;">Ease Health</h1>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("<div class='eyebrow'>PORTAL ACCESS</div>", unsafe_allow_html=True)
                    st.markdown("<h1 style='margin-top:0;'>Ease Health</h1>", unsafe_allow_html=True)

                email = st.text_input("Email")
                password = st.text_input("Password", type="password")

                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Sign In")

                if submitted:
                    if not email or not password:
                        st.error("Please enter your email and password.")
                    else:
                        user = login_user(email, password)
                        if user:
                            st.session_state['logged_in'] = True
                            st.session_state['user'] = user
                            st.session_state['page'] = 'dashboard'
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

        with register_tab:
            with st.form("register_form", clear_on_submit=False):
                st.markdown("<div class='eyebrow'>NEW PATIENT REGISTRATION</div>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin-top:0;'>Create Account</h2>", unsafe_allow_html=True)

                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_name = st.text_input("Full Name *")
                    r_email = st.text_input("Email *", key="reg_email")
                    r_password = st.text_input("Password *", type="password", key="reg_pass",
                                               help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
                with r_col2:
                    r_phone = st.text_input("Phone")
                    r_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                    r_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

                # Date of birth range updated from 1900 to today
                r_dob = st.date_input(
                    "Date of Birth",
                    value=datetime.date(2000, 1, 1),
                    min_value=datetime.date(1900, 1, 1),
                    max_value=datetime.date.today()
                )
                r_emergency = st.text_input("Emergency Contact")

                st.markdown("<br>", unsafe_allow_html=True)
                reg_submitted = st.form_submit_button("Register")

                if reg_submitted:
                    if not r_name or not r_email or not r_password:
                        st.error("Please fill in all required fields.")
                    else:
                        success, msg = register_patient(
                            email=r_email, password=r_password, full_name=r_name,
                            phone=r_phone, date_of_birth=r_dob.isoformat() if r_dob else None,
                            gender=r_gender, blood_group=r_blood, emergency_contact=r_emergency
                        )
                        if success:
                            st.success(msg)
                            # Automatically login the user after registration
                            user = login_user(r_email, r_password)
                            if user:
                                st.session_state['logged_in'] = True
                                st.session_state['user'] = user
                                st.session_state['page'] = 'dashboard'
                                st.rerun()
                        else:
                            st.error(msg)


# ==========================================
# LOGGED IN — SIDEBAR NAVIGATION + ROUTING
# ==========================================
else:
    user = st.session_state['user']
    role = user['role']
    page = st.session_state.get('page', 'dashboard')
    
    # --- Google Drive Style Sidebar ---
    with st.sidebar:
        if ease_logo_b64:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:11px; padding: 7px 0; margin-bottom: 24px;">
                <img src="data:image/png;base64,{ease_logo_b64}" width="40" style="border-radius:7px;"/>
                <div>
                    <div style="font-family:'Cormorant Garamond',serif; font-size:24px; font-weight:600; color:var(--color-forest-ink); line-height:1;">Ease Health</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='color:var(--color-forest-ink); font-weight:600;'>Ease Health</h2>", unsafe_allow_html=True)

        role_label = {'admin': 'Admin', 'doctor': 'Physician', 'patient': 'Patient'}.get(role, role.title())
        st.markdown(f"<p style='font-size: 13px; font-weight: 600; color: #71717a;'>Logged in as {user['full_name']} ({role_label})</p>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Dashboard", use_container_width=True):
            st.session_state['page'] = 'dashboard'
            st.rerun()
            
        if st.button("Calendar", use_container_width=True):
            st.session_state['page'] = 'calendar'
            st.rerun()

        if st.button("Settings", use_container_width=True):
            st.session_state['page'] = 'settings'
            st.rerun()

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        if st.button("Sign Out", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user'] = None
            st.session_state['page'] = 'dashboard'
            st.rerun()

    # --- Page Content Area ---
    if page == 'calendar':
        calendar_view.render(user)
    elif page == 'settings':
        st.markdown("<h2>Settings</h2>", unsafe_allow_html=True)
        st.markdown("<h4>Change Password</h4>", unsafe_allow_html=True)
        with st.form("change_password_form"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password", help="Min 8 chars, 1 uppercase, 1 number, 1 special char")
            if st.form_submit_button("Update Password"):
                if not old_pw or not new_pw:
                    st.error("Please fill in all fields.")
                else:
                    user_record = validate_password(user['email'], old_pw)
                    if user_record:
                        # Simple inline validation for new password
                        import re
                        if len(new_pw) < 8 or not re.search(r"[A-Z]", new_pw) or not re.search(r"\d", new_pw) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_pw):
                            st.error("Password must be at least 8 chars long and contain an uppercase letter, a number, and a special character.")
                        else:
                            import bcrypt
                            from db import execute_query
                            new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            execute_query("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user['id']))
                            st.success("Password updated successfully!")
                    else:
                        st.error("Incorrect current password.")
    elif page == 'dashboard':
        if role == 'admin':
            admin_dashboard.render(user)
        elif role == 'doctor':
            doctor_dashboard.render(user)
        else:
            patient_dashboard.render(user)

    # Footer
    st.markdown("<hr style='border: none; border-top: 1px solid var(--color-border-mist); margin: 64px 0 21px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--color-charcoal); font-size: 11px;'>Integrated Patient Care Management System</p>", unsafe_allow_html=True)