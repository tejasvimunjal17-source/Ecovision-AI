"""
EcoVision AI — upgraded main entry point.

Flow:
1. Public landing page: no sidebar, no Streamlit/GitHub navigation chrome.
2. "Continue with Google" or "Continue with Email".
3. After authentication, the role-aware sidebar appears.
4. Citizen / officer / admin dashboards are separate routes.
5. Prakriti AI floats bottom-right on the landing and authenticated pages.
"""
import streamlit as st

from config import settings
from utils.helpers import load_css, init_session_state, logout

st.set_page_config(
    page_title="EcoVision AI | Smart Waste Management",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state()

# Streamlit OIDC callback: if Google has just authenticated, mirror the
# identity into the same Supabase users table used by email login.
if not st.session_state.get("user"):
    try:
        from backend.auth import sync_google_user
        if getattr(st.user, "is_logged_in", False):
            st.session_state["user"] = sync_google_user()
    except Exception:
        pass

authenticated = bool(st.session_state.get("user"))
load_css(show_sidebar=authenticated, show_chat=True)


def _google_login():
    try:
        st.login("google")
    except Exception as exc:
        st.error(
            "Google sign-in is not configured yet. Add Streamlit OIDC settings "
            "under `[auth]` in Streamlit Cloud Secrets. Email sign-in remains available."
        )
        st.caption(f"Configuration detail: {exc}")


# ----------------------------------------------------------------------
# Public landing / auth CTA
# ----------------------------------------------------------------------
if not authenticated:
    st.markdown(
        """
        <div class="eco-topbar-public">
          <div class="eco-brand">🌿 EcoVision <span>AI</span></div>
          <div class="eco-brand-tag">Smart Waste • Recycling • Citizen Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="eco-hero eco-landing-hero">
          <div class="eco-float" style="font-size:3.2rem;">🌍♻️🌱</div>
          <div class="eco-kicker">AI-POWERED SMART CITY PLATFORM</div>
          <h1>Smart Waste Management & Recycling in Indian Cities</h1>
          <p>
            Report waste, classify it with AI, track civic complaints, discover
            recycling guidance and get instant sustainability help from Prakriti AI Connect.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    a, b, c = st.columns([1, 1.4, 1])
    with b:
        st.markdown(
            '<div class="eco-auth-card"><h3>Start your cleaner-city journey</h3>'
            '<p>Use Google for one-tap access, or continue with your EcoVision email account.</p></div>',
            unsafe_allow_html=True,
        )
        g1, g2 = st.columns(2)
        with g1:
            if st.button("🌐 Continue with Google", use_container_width=True, type="primary"):
                _google_login()
        with g2:
            if st.button("✉️ Continue with Email", use_container_width=True):
                st.switch_page("pages/1_🔐_Login.py")
        if st.button("🚀 Create a new account", use_container_width=True):
            st.switch_page("pages/2_📝_Register.py")

    st.markdown("---")

    st.markdown('<div class="eco-section-title">🌱 Platform Features</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="eco-section-sub">Everything a Smart City needs for sustainable waste management, in one platform.</div>',
        unsafe_allow_html=True,
    )

    features = [
        ("📢", "AI Waste Reporting", "Report waste issues with photo, location and AI-assisted descriptions."),
        ("🤖", "AI Waste Classification", "Upload a photo and let a vision-capable model identify the waste category."),
        ("♻️", "Recycling Guide", "Category-wise disposal and recycling guidance tailored for Indian households."),
        ("📍", "Complaint Tracking", "Track every complaint from submission to resolution."),
        ("🌿", "Prakriti AI Connect", "A bilingual English/Hindi sustainability assistant that floats on every page."),
        ("📊", "Dashboard Generator", "Upload CSV/Excel data and generate KPI cards, charts and insights."),
        ("📈", "Smart Analytics", "Ward-wise, category-wise and time-series analytics for officers and admins."),
        ("🏆", "Green Rewards", "Earn points for responsible reporting and climb the city leaderboard."),
        ("📄", "AI Reports", "Generate citizen, officer and municipality reports."),
        ("🗺️", "Recycling Centre Locator", "Find registered recycling and e-waste centres."),
        ("🌍", "Carbon Calculator", "Estimate your footprint and receive reduction tips."),
        ("🧑‍💼", "Officer Dashboard", "Complaint management, worker assignment and performance analytics."),
    ]
    for row_start in range(0, len(features), 4):
        cols = st.columns(4)
        for col, (icon, title, desc) in zip(cols, features[row_start:row_start+4]):
            with col:
                st.markdown(
                    f'<div class="eco-card"><div style="font-size:2rem">{icon}</div>'
                    f'<div style="font-weight:700;margin:.35rem 0">{title}</div>'
                    f'<div style="color:#718078;font-size:.88rem">{desc}</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="eco-section-title">💡 Why Choose EcoVision AI</div>', unsafe_allow_html=True)
    for i, item in enumerate([
        "AI Powered", "Fast Complaint Resolution", "Interactive Dashboards",
        "Supabase Cloud Data", "Citizen Engagement", "Role-based Access",
        "Secure Admin Panel", "OpenRouter AI", "Cloud Hosted"
    ]):
        st.markdown(f'<span class="eco-pill">✔ {item}</span>', unsafe_allow_html=True)

    st.markdown('<div class="eco-section-title">🌎 Supporting the UN Sustainable Development Goals</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, title, text in [
        (c1, "🏙️ SDG 11", "Sustainable Cities & Communities"),
        (c2, "♻️ SDG 12", "Responsible Consumption & Production"),
        (c3, "🌡️ SDG 13", "Climate Action"),
    ]:
        with col:
            st.markdown(
                f'<div class="eco-card"><h3>{title}</h3><p style="color:#52635a">{text}</p>'
                f'<p style="color:#718078">Cleaner neighbourhoods, better segregation and measurable environmental impact.</p></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="eco-section-title">📊 Platform Impact</div>', unsafe_allow_html=True)
    stats = [("10,000+", "Complaints Managed"), ("95%", "AI Classification Accuracy"),
             ("50+", "Recycling Centres"), ("24×7", "AI Assistant"), ("10×", "Faster Analytics")]
    cols = st.columns(len(stats))
    for col, (num, label) in zip(cols, stats):
        with col:
            st.markdown(f'<div class="eco-stat"><div class="num">{num}</div><div class="label">{label}</div></div>',
                        unsafe_allow_html=True)

    st.markdown('<div class="eco-section-title">🤖 Meet Prakriti AI Connect</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="eco-card"><b>Floating assistant:</b> tap <b>🌿 Prakriti AI</b> in the bottom-right corner. '
        'The original English/Hindi prompt logic remains intact.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="eco-section-title">❓ Frequently Asked Questions</div>', unsafe_allow_html=True)
    faqs = [
        ("How do I report waste?", "Log in as a citizen, open Report Waste, upload media and submit the complaint."),
        ("How does AI classify waste?", "OpenRouter vision models analyze the uploaded image and return a category and confidence."),
        ("Where is my data stored?", "Application data is stored in Supabase PostgreSQL; Streamlit Cloud is not used as a database."),
        ("Is Prakriti AI bilingual?", "Yes. The original English/Hindi Prakriti AI Connect flow is preserved."),
        ("What can admins do?", "Admins have a separate role-protected Admin Panel for users, complaints, categories and analytics."),
    ]
    for q, ans in faqs:
        with st.expander(q):
            st.write(ans)

    st.markdown(
        '<div class="eco-footer">🌿 <b>EcoVision AI</b> — Designed for Smart Sustainable Cities<br>'
        'Python · Streamlit · OpenRouter AI · Supabase PostgreSQL</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ----------------------------------------------------------------------
# Authenticated Home
# ----------------------------------------------------------------------
user = st.session_state["user"]
nav1, nav2 = st.columns([4, 1])
with nav1:
    st.markdown(f"### 🌿 EcoVision AI")
    st.caption(f"Welcome back, {user.get('full_name','').split()[0]} · {user.get('role','').title()}")
with nav2:
    if st.button("Logout", use_container_width=True):
        logout()
        st.rerun()

st.markdown(
    f"""
    <div class="eco-greeting">
      <div class="eyebrow">EcoVision AI · Smart city workspace</div>
      <h1>Your city, made cleaner.</h1>
      <p>Welcome back, {user.get('full_name','').split()[0]}. Your role-specific tools, reports and sustainability insights are ready.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

role = user.get("role")

# Product-style summary cards inspired by the supplied reference UI.
summary = {
    "citizen": [("📢", "My reports", "Report waste and follow every update."), ("♻️", "Recycle better", "Get category-specific disposal guidance."), ("🌿", "Ask Prakriti", "Get bilingual sustainability help.")],
    "officer": [("📋", "Work queue", "Review and resolve assigned complaints."), ("📈", "Analytics", "Monitor ward and category trends."), ("🌿", "Ask Prakriti", "Get sustainability assistance.")],
    "admin": [("🛡️", "Admin control", "Manage users, complaints and platform data."), ("📊", "City analytics", "See operational trends and KPIs."), ("🌿", "Ask Prakriti", "Get sustainability assistance.")],
}
cols = st.columns(3)
for col, (icon, title, text) in zip(cols, summary.get(role, summary["citizen"])):
    with col:
        st.markdown(f'<div class="eco-card"><div style="font-size:1.6rem">{icon}</div><h3 style="margin:.35rem 0">{title}</h3><div style="color:#718078;font-size:.85rem">{text}</div></div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    if role == "citizen":
        st.page_link("pages/3_🏠_Citizen_Dashboard.py", label="📊 Open My Dashboard", use_container_width=True)
    elif role == "officer":
        st.page_link("pages/7_🧑‍💼_Officer_Dashboard.py", label="🧑‍💼 Open Officer Dashboard", use_container_width=True)
    else:
        st.page_link("pages/8_🛠️_Admin_Dashboard.py", label="🛡️ Open Admin Panel", use_container_width=True)
with c2:
    st.page_link("pages/9_🤖_Prakriti_AI_Connect.py", label="🌿 Open Prakriti AI", use_container_width=True)
with c3:
    st.page_link("pages/4_📢_Report_Waste.py", label="📢 Report Waste", use_container_width=True)

st.markdown("---")
st.markdown('<div class="eco-section-title">⚡ Quick Access</div>', unsafe_allow_html=True)
quick = [
    ("📢", "Report Waste", "pages/4_📢_Report_Waste.py"),
    ("📜", "Complaint History", "pages/5_📜_Complaint_History.py"),
    ("🏆", "Rewards", "pages/6_🏆_Rewards.py"),
    ("♻️", "Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
]
cols = st.columns(4)
for col, (icon, label, path) in zip(cols, quick):
    with col:
        st.page_link(path, label=f"{icon} {label}", use_container_width=True)
