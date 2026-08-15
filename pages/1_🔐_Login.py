import streamlit as st
from backend.auth import login_user, get_security_question, reset_password, sync_google_user
from utils.helpers import load_css, init_session_state, toast

st.set_page_config(page_title="Login | EcoVision AI", page_icon="🔐", layout="centered")
init_session_state()

# If Google just redirected back to this page, sync the account.
try:
    if getattr(st.user, "is_logged_in", False):
        st.session_state["user"] = sync_google_user()
        st.success("Google sign-in successful. Redirecting to your dashboard…")
        st.switch_page("pages/3_🏠_Citizen_Dashboard.py")
except Exception:
    pass

load_css(show_sidebar=False, show_chat=True)

st.markdown(
    '<div class="eco-hero"><div style="font-size:3rem">🌿🔐</div>'
    '<h1>Welcome to EcoVision AI</h1>'
    '<p>Continue securely with Google or your EcoVision email account.</p></div>',
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
with c1:
    if st.button("🌐 Continue with Google", use_container_width=True, type="primary"):
        try:
            st.login("google")
        except Exception as exc:
            st.error("Google sign-in is not configured in Streamlit Cloud Secrets.")
            st.caption(str(exc))
with c2:
    if st.button("✉️ Create account", use_container_width=True):
        st.switch_page("pages/2_📝_Register.py")

st.markdown("---")
tab_login, tab_forgot = st.tabs(["✉️ Email Login", "🔑 Forgot Password"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            ok, result = login_user(email, password)
            if ok:
                st.session_state["user"] = result
                st.session_state["sidebar_open"] = True
                st.session_state["active_nav"] = {
                    "citizen": "📊 My Dashboard",
                    "officer": "🧑‍💼 Officer Dashboard",
                    "admin": "🛡️ Admin Panel",
                }.get(result["role"], "📊 My Dashboard")
                toast(f"Welcome back, {result['full_name']}!")
                target = {
                    "citizen": "pages/3_🏠_Citizen_Dashboard.py",
                    "officer": "pages/7_🧑‍💼_Officer_Dashboard.py",
                    "admin": "pages/8_🛠️_Admin_Dashboard.py",
                }[result["role"]]
                st.switch_page(target)
            else:
                st.error(result)

    st.markdown("New to EcoVision AI?")
    if st.button("🚀 Register with Email", use_container_width=True):
        st.switch_page("pages/2_📝_Register.py")

with tab_forgot:
    st.write("Reset your email-account password using your registered security answer.")
    fp_email = st.text_input("Registered Email", key="fp_email")
    if fp_email:
        q = get_security_question(fp_email)
        if q:
            st.write(f"**Security question:** {q}")
            with st.form("reset_form"):
                answer = st.text_input("Your Answer")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                reset_submit = st.form_submit_button("Reset Password", use_container_width=True)
            if reset_submit:
                if new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = reset_password(fp_email, answer, new_pw)
                    st.success(msg) if ok else st.error(msg)
        else:
            st.warning("No security question found. If you use Google sign-in, continue with Google.")
