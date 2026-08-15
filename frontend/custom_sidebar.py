"""Role-aware, collapsible EcoVision AI sidebar."""
from __future__ import annotations
import streamlit as st

DRAWER_WIDTH = "20rem"
DRAWER_WIDTH_MOBILE = "min(20rem,86vw)"

USER_NAV = {
    "citizen": [
        ("🏠 Home", "app.py"),
        ("📊 My Dashboard", "pages/3_🏠_Citizen_Dashboard.py"),
        ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
        ("📜 Complaint History", "pages/5_📜_Complaint_History.py"),
        ("🏆 Rewards", "pages/6_🏆_Rewards.py"),
        ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
        ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
        ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
        ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
        ("🌱 Awareness Hub", "pages/14_🌱_Awareness_Hub.py"),
        ("🎓 Certifications & Jobs", "pages/15_🎓_Certifications_and_Jobs.py"),
        ("📄 Reports", "pages/16_📄_Reports.py"),
        ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
    ],
    "officer": [
        ("🏠 Home", "app.py"),
        ("🧑‍💼 Officer Dashboard", "pages/7_🧑‍💼_Officer_Dashboard.py"),
        ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
        ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
        ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
        ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
        ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
        ("🌱 Awareness Hub", "pages/14_🌱_Awareness_Hub.py"),
        ("🎓 Certifications & Jobs", "pages/15_🎓_Certifications_and_Jobs.py"),
        ("📄 Reports", "pages/16_📄_Reports.py"),
        ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
    ],
    "admin": [
        ("🏠 Home", "app.py"),
        ("🛡️ Admin Panel", "pages/8_🛠️_Admin_Dashboard.py"),
        ("🧑‍💼 Officer Dashboard", "pages/7_🧑‍💼_Officer_Dashboard.py"),
        ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
        ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
        ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
        ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
        ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
        ("📄 Reports", "pages/16_📄_Reports.py"),
        ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
    ],
}


def render_custom_sidebar_controls():
    user = st.session_state.get("user")
    if not user:
        return

    st.session_state.setdefault("sidebar_open", True)
    is_open = st.session_state["sidebar_open"]

    with st.container(key="eco_sidebar_toggle"):
        if st.button("✕" if is_open else "☰", key="eco_sidebar_toggle_btn",
                     help="Open / close navigation"):
            st.session_state["sidebar_open"] = not is_open
            st.rerun()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="eco-sidebar-brand">
              <div class="eco-sidebar-logo">🌿</div>
              <div>
                <div class="eco-sidebar-title">EcoVision AI</div>
                <div class="eco-sidebar-sub">Smart City Platform</div>
              </div>
            </div>
            <div class="eco-user-card">
              <div class="eco-user-name">👋 {user.get('full_name','').split()[0]}</div>
              <div class="eco-user-role">{user.get('role','citizen').title()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        options = USER_NAV.get(user.get("role"), USER_NAV["citizen"])
        labels = [x[0] for x in options]
        paths = dict(options)
        current = st.session_state.get("active_nav")
        if current not in labels:
            current = labels[1] if len(labels) > 1 else labels[0]

        selected = st.radio(
            "Navigation", labels, index=labels.index(current),
            label_visibility="collapsed", key="eco_role_nav",
        )
        if selected != current:
            st.session_state["active_nav"] = selected
            st.switch_page(paths[selected])

        st.divider()
        if st.button("🤖 Open Prakriti AI", use_container_width=True):
            st.session_state["chatbot_open"] = True
            st.rerun()

        if user.get("role") == "admin":
            st.caption("🛡️ Admin access enabled")

        if st.button("🚪 Logout", use_container_width=True):
            from utils.helpers import logout
            logout()
            st.session_state["sidebar_open"] = False
            st.rerun()

    transform = "translateX(0)" if is_open else "translateX(-105%)"
    margin = DRAWER_WIDTH if is_open else "0"
    st.markdown(
        f"""
        <style>
        div[class*="st-key-eco_sidebar_toggle"] {{
            position:fixed; left:12px; top:12px; z-index:1000000;
        }}
        div[class*="st-key-eco_sidebar_toggle_btn"] button {{
            width:42px; height:42px; border-radius:12px; padding:0;
            font-size:1.1rem; box-shadow:0 8px 24px rgba(120,200,60,.20);
        }}
        section[data-testid="stSidebar"] {{
            position:fixed !important; left:0 !important; top:0 !important;
            height:100vh !important; z-index:999998 !important;
            width:{DRAWER_WIDTH} !important; min-width:{DRAWER_WIDTH} !important;
            max-width:{DRAWER_WIDTH} !important;
            transform:{transform} !important;
            transition:transform .28s ease !important;
            background:#ffffff !important;
            border-right:1px solid #e3eadc !important; box-shadow:10px 0 35px rgba(45,70,40,.05) !important;
            overflow-y:auto !important;
        }}
        section[data-testid="stSidebarNav"] {{ display:none !important; }}
        section[data-testid="stSidebar"] > div:first-child {{ padding-top:.7rem; }}
        .eco-sidebar-brand {{ display:flex; gap:.8rem; align-items:center; padding:.5rem .25rem 1rem; }}
        .eco-sidebar-logo {{ font-size:2rem; }}
        .eco-sidebar-title {{ font-size:1.15rem; font-weight:800; color:#1d2b24; }}
        .eco-sidebar-sub {{ color:#718078; font-size:.75rem; }}
        .eco-user-card {{
            background:#f4f8ef; border:1px solid #e3eadc;
            border-radius:14px; padding:.8rem; margin:.3rem 0 1rem;
        }}
        .eco-user-name {{ font-weight:700; color:#1d2b24; }}
        .eco-user-role {{ color:#3d6f2a; font-size:.78rem; margin-top:.2rem; }}
        section[data-testid="stSidebar"] [data-testid="stRadio"] label {{
            border-radius:10px; padding:.38rem .45rem; margin:.1rem 0;
        }}
        section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
            background:#eef7e7;
        }}
        @media (min-width:641px) {{
          section[data-testid="stMain"] {{
            margin-left:{margin} !important;
            width:calc(100% - {margin}) !important;
            max-width:calc(100% - {margin}) !important;
            box-sizing:border-box;
            transition:margin-left .28s ease,width .28s ease;
          }}
        }}
        html, body, .stApp {{ overflow-x:hidden !important; }}
        @media (max-width:640px) {{
          section[data-testid="stSidebar"] {{
            width:{DRAWER_WIDTH_MOBILE} !important;
            min-width:{DRAWER_WIDTH_MOBILE} !important;
            max-width:{DRAWER_WIDTH_MOBILE} !important;
          }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
