import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import os
import base64
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import pandas as pd
import time

# --- Layout Configuration ---
st.set_page_config(
    page_title="Ease Health — Integrated Care",
    page_icon="🌿",
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

ease_product_b64 = get_base64_of_bin_file("assets/ease_product_mockup.png")
ease_illustration_b64 = get_base64_of_bin_file("assets/ease_medical_illustration.png")
ease_logo_b64 = get_base64_of_bin_file("assets/ease_logo.png")

# --- Inject Custom CSS ---
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400&family=Inter:wght@300;400;600&display=swap');

:root {{
  --color-forest-ink: #0f3e17;
  --color-sage-mist: #b1dbb8;
  --color-keylime-wash: #e1f4df;
  --color-mint-veil: #cfe7d3;
  --color-slate-hush: #b6ced5;
  --color-cream-paper: #fffefc;
  --color-charcoal: #222222;
  --color-border-mist: #efeeeb;
}}

/* Base Body Styles */
.stApp {{
    background-color: var(--color-cream-paper) !important;
}}

html, body, [class*="st-"] {{
    font-family: 'Inter', sans-serif !important;
    color: var(--color-charcoal) !important;
}}

/* Hide Default Streamlit Header & Hamburger Menu */
header[data-testid="stHeader"] {{
    display: none !important;
}}

/* Typography Overrides */
h1, h2, h3, .serif-text {{
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 300 !important;
    color: var(--color-forest-ink) !important;
}}
h1 {{
    font-size: 56px !important;
    line-height: 1.2 !important;
    letter-spacing: -1.68px !important;
}}
h2 {{
    font-size: 40px !important;
    line-height: 1.35 !important;
    letter-spacing: -0.4px !important;
}}

.eyebrow {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-forest-ink);
    margin-bottom: 7px;
}}

/* JS On-Scroll Animation Classes */
.hidden-scroll {{
    opacity: 0;
    transform: translateY(40px);
    transition: opacity 0.8s cubic-bezier(0.16, 1, 0.3, 1), transform 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}}
.hidden-scroll.visible {{
    opacity: 1;
    transform: translateY(0);
}}

/* Login Screen Container Fix using stForm */
div[data-testid="stForm"] {{
    background-color: var(--color-keylime-wash);
    padding: 56px;
    border-radius: 14px;
    max-width: 500px;
    margin: 10vh auto 0 auto !important;
    box-shadow: none !important;
    border: none !important;
}}

/* Top Navigation Bar Fix */
div[data-testid="stVerticalBlock"]:has(.nav-wrapper-marker) {{
    border-bottom: 1px solid var(--color-border-mist);
    padding: 14px 0;
    margin-bottom: 64px;
    margin-top: 14px;
}}
div[data-testid="stVerticalBlock"]:has(.nav-wrapper-marker) div[data-testid="column"] {{
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

/* Panels using :has() */
div[data-testid="stVerticalBlock"]:has(.panel-keylime-marker) {{
    background-color: var(--color-keylime-wash);
    border-radius: 14px;
    padding: 42px;
    height: 100%;
}}
div[data-testid="stVerticalBlock"]:has(.panel-slate-marker) {{
    background-color: var(--color-slate-hush);
    border-radius: 14px;
    padding: 42px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}}
div[data-testid="stVerticalBlock"]:has(.panel-sage-marker) {{
    background-color: var(--color-sage-mist);
    border-radius: 14px;
    padding: 42px;
}}

/* Dashboard Metrics */
div[data-testid="stMetricValue"] {{
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 40px !important;
    font-weight: 300 !important;
    color: var(--color-forest-ink) !important;
}}
div[data-testid="stMetricLabel"] {{
    font-size: 14px !important;
    color: var(--color-charcoal) !important;
}}

/* Badges / Tags */
.pill-badge {{
    background-color: var(--color-cream-paper);
    color: var(--color-forest-ink);
    border-radius: 999px;
    padding: 9px 14px;
    font-size: 14px;
    display: inline-block;
    margin-top: 14px;
}}

/* Streamlit Native Button Overrides */
.stButton > button, .stFormSubmitButton > button {{
    background-color: var(--color-forest-ink) !important;
    color: var(--color-cream-paper) !important;
    border-radius: 14px !important;
    border: none !important;
    font-weight: 400 !important;
    padding: 14px 21px !important;
    transition: background-color 0.2s ease !important;
    box-shadow: none !important; /* NO SHADOWS */
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
    background-color: #0c2f10 !important;
    color: var(--color-cream-paper) !important;
}}
.stButton > button p, .stFormSubmitButton > button p {{
    font-size: 14px !important;
    color: var(--color-cream-paper) !important; /* FIX FOR FLOATING BUTTON TEXT */
}}

/* Right aligned sign out button */
.sign-out-col div[data-testid="stButton"] {{
    display: flex;
    justify-content: flex-end;
}}

/* Input Styling */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {{
    border-radius: 7px !important;
    border: 1px solid var(--color-border-mist) !important;
    background-color: var(--color-cream-paper) !important;
    color: var(--color-charcoal) !important;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Inject JS for IntersectionObserver Scroll Animations ---
js_code = """
<script>
    const doc = window.parent.document;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    // Find all anim-markers, then observe their parent stVerticalBlock
    const markers = doc.querySelectorAll('.anim-marker');
    markers.forEach(marker => {
        const parentBlock = marker.closest('div[data-testid="stVerticalBlock"]');
        if (parentBlock) {
            parentBlock.classList.add('hidden-scroll');
            observer.observe(parentBlock);
        }
    });
</script>
"""
components.html(js_code, height=0, width=0)

# --- Authentication State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# ==========================================
# LOGIN PAGE
# ==========================================
if not st.session_state['logged_in']:
    _, col, _ = st.columns([1, 1.2, 1])
    
    with col:
        # Wrap everything securely in a form so the inputs are forced into the styled Keylime block!
        with st.form("login_form", clear_on_submit=False):
            st.markdown(f"""
            <div style="display:flex; flex-direction:column; align-items:center; margin-bottom: 24px;">
                <img src="data:image/png;base64,{ease_logo_b64}" width="120" style="margin-bottom:14px;"/>
                <div class="eyebrow" style="margin-bottom:0;">PORTAL ACCESS</div>
                <h1 style="margin-top:0; text-align:center;">Ease Health</h1>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Physician ID (Hint: admin)")
            password = st.text_input("Passcode (Hint: password)", type="password")
            
            # Empty container for spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Access Portal &rsaquo;")
            if submitted:
                if username == 'admin' and password == 'password':
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid ID or Passcode.")

# ==========================================
# MAIN DASHBOARD
# ==========================================
else:
    # Top Navigation Bar (Fixed Layout)
    with st.container():
        st.markdown("<div class='nav-wrapper-marker'></div>", unsafe_allow_html=True)
        # Using [4, 1] keeps logo far left and button far right neatly
        nav_col1, nav_col2 = st.columns([5, 1])
        with nav_col1:
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap: 14px;'>
                <img src="data:image/png;base64,{ease_logo_b64}" width="40" style="border-radius:7px;"/>
                <span style='font-family: "Cormorant Garamond", serif; font-size: 28px; color: var(--color-forest-ink);'>Ease Health</span>
            </div>
            """, unsafe_allow_html=True)
        with nav_col2:
            st.markdown("<div class='sign-out-col'></div>", unsafe_allow_html=True)
            if st.button("Sign Out"):
                st.session_state['logged_in'] = False
                st.rerun()

    # --- Hero Section (Keylime + Slate Hush Split) ---
    with st.container():
        st.markdown("<div class='anim-marker'></div>", unsafe_allow_html=True)
        hero_col1, hero_col2 = st.columns([1.2, 1])
        
        with hero_col1:
            with st.container():
                st.markdown("<div class='panel-keylime-marker'></div>", unsafe_allow_html=True)
                st.markdown("""
                <div class="eyebrow">CLINICAL OVERVIEW</div>
                <h1>Integrated Care Workspace</h1>
                <p style="font-size: 18px; line-height: 1.3;">A serene, botanical environment for tracking telemetry, patient queries, and admission flows. Focus on care, not clutter.</p>
                <span class="pill-badge">System Active</span>
                """, unsafe_allow_html=True)
            
        with hero_col2:
            with st.container():
                st.markdown("<div class='panel-slate-marker'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                <img src="data:image/png;base64,{ease_product_b64}" style="max-width: 100%; border-radius: 14px;" />
                """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Metrics & Telemetry (Sage Mist Feature Panel) ---
    with st.container():
        st.markdown("<div class='anim-marker panel-sage-marker'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="eyebrow">WARD STATUS</div>
        <h2 style="margin-top:0; margin-bottom: 28px;">Vitals & Admissions</h2>
        """, unsafe_allow_html=True)
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Active Admissions", "1,204", "+12 today")
        m_col2.metric("Critical Alerts", "14", "-3 since last hour")
        m_col3.metric("Available Doctors", "89", "On duty")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        mock_data = {
            "Patient ID": ["P-1092", "P-2034", "P-3921", "P-4402", "P-5199"],
            "Name": ["John Doe", "Jane Smith", "Alice Johnson", "Bob Brown", "Charlie Davis"],
            "Heart Rate": [72, 110, 68, 95, 80],
            "SpO2": ["98%", "92%", "99%", "94%", "97%"],
            "Status": ["Stable", "Review", "Stable", "Review", "Stable"]
        }
        df = pd.DataFrame(mock_data)

        def highlight_botanical(row):
            color = 'rgba(15, 62, 23, 0.1)' if row['Status'] == 'Review' else 'transparent'
            return ['background-color: {}'.format(color)] * len(row)

        st.dataframe(df.style.apply(highlight_botanical, axis=1), use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- AI Assistant Section ---
    with st.container():
        st.markdown("<div class='anim-marker'></div>", unsafe_allow_html=True)
        ai_col1, ai_col2 = st.columns([1, 1.5])
        
        with ai_col1:
            st.markdown(f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{ease_illustration_b64}" style="max-width: 80%;" />
            </div>
            """, unsafe_allow_html=True)
            
        with ai_col2:
            st.markdown("<div class='eyebrow'>INTELLIGENT QUERY</div>", unsafe_allow_html=True)
            st.markdown("<h2 style='margin-top:0;'>Clinical Assistant</h2>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 14px; color: #222222; margin-bottom: 21px;'>Powered by Groq & Langchain.</p>", unsafe_allow_html=True)

            load_dotenv()
            api_key = os.getenv("GROQ_API_KEY")

            user_input = st.text_area(
                "Query Patient Records or Medical Protocol:",
                value="Summarize the common telemetry warnings for patients with an SpO2 below 93%."
            )

            if st.button("Submit Query"):
                if not user_input.strip():
                    st.warning("Please enter a query.")
                else:
                    with st.spinner("Analyzing..."):
                        time.sleep(1.5)
                        if api_key:
                            try:
                                llm = ChatGroq(
                                    model="llama-3.1-8b-instant",
                                    temperature=0.2,
                                    api_key=api_key
                                )
                                response = llm.invoke([HumanMessage(content=user_input)])
                                st.success("Analysis Complete")
                                st.write(response.content)
                            except Exception as e:
                                st.error(f"Error calling Groq API: {e}")
                        else:
                            st.info("⚠️ No API key found. Using Botanical Mock Fallback.")
                            st.markdown("""
                            <div style="background-color: var(--color-cream-paper); padding: 28px; border-radius: 14px; border: 1px solid var(--color-border-mist);">
                                <p style="font-family: 'Cormorant Garamond', serif; font-size: 23px; color: var(--color-forest-ink); margin-bottom: 14px;">Analysis Complete</p>
                                <p style="font-size: 14px; line-height: 1.5;">Patients exhibiting an SpO2 level below 93% and elevated heart rates (>100 bpm) are currently tagged under 'Review' status. Standard protocol indicates immediate supplemental oxygen therapy and a secondary respiratory assessment. The most common correlation in the current ward is postoperative recovery anomalies.</p>
                            </div>
                            """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border: none; border-top: 1px solid var(--color-border-mist); margin: 64px 0 21px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--color-charcoal); font-size: 11px;'>Integrated Patient Care Management System</p>", unsafe_allow_html=True)