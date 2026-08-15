"""Shared UI/session helpers for EcoVision AI."""
import streamlit as st
from pathlib import Path
from datetime import datetime

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def hide_streamlit_navigation():
    """Hide Streamlit's generated multipage list; our role-aware sidebar owns navigation."""
    st.markdown(
        """<style>
        section[data-testid="stSidebarNav"] { display: none !important; }
        div[data-testid="stToolbarActions"] { display: none !important; }
        .stAppDeployButton { display: none !important; }
        div[data-testid="stSidebarCollapseButton"],
        div[data-testid="collapsedControl"] { display: none !important; }
        </style>""",
        unsafe_allow_html=True,
    )


def load_css(show_sidebar=None, show_chat=True):
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

    hide_streamlit_navigation()
    if show_sidebar is None:
        show_sidebar = bool(st.session_state.get("user"))

    if show_sidebar:
        from frontend.custom_sidebar import render_custom_sidebar_controls
        render_custom_sidebar_controls()
    else:
        st.markdown(
            """<style>
            section[data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-top: 2rem !important; }
            </style>""",
            unsafe_allow_html=True,
        )

    if show_chat:
        from frontend.prakriti_widget import render_prakriti_widget
        render_prakriti_widget()


def init_session_state():
    defaults = {
        "user": None,
        "theme": "dark",
        "chat_history": [],
        "chat_session_id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
        "chatbot_open": False,
        "show_chat": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Supabase health check/seed happens once per browser session.
    if not st.session_state.get("_db_initialized"):
        try:
            from database.db import init_db
            init_db()
            st.session_state["_db_initialized"] = True
            st.session_state["_db_error"] = None
        except Exception as exc:
            st.session_state["_db_initialized"] = True
            st.session_state["_db_error"] = str(exc)


def require_login(allowed_roles=None):
    init_session_state()
    if not st.session_state.get("user"):
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/1_🔐_Login.py", label="Go to Login", icon="🔐")
        st.stop()
    if allowed_roles and st.session_state["user"]["role"] not in allowed_roles:
        st.error("⛔ You don't have permission to view this page.")
        st.stop()


def logout():
    st.session_state["user"] = None
    st.session_state["chat_history"] = []
    st.session_state["chatbot_open"] = False
    # Clear the OIDC session too, when present.
    try:
        if getattr(st.user, "is_logged_in", False):
            st.logout()
    except Exception:
        pass


def status_badge(status: str) -> str:
    colors = {
        "Submitted": "#64748b", "Under Review": "#f59e0b", "Assigned": "#3b82f6",
        "In Progress": "#8b5cf6", "Resolved": "#10b981", "Rejected": "#ef4444",
    }
    color = colors.get(status, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em;border:1px solid {color}55;">{status}</span>'


def priority_badge(priority: str) -> str:
    colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    color = colors.get(priority, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em;border:1px solid {color}55;">{priority}</span>'


def toast(message: str, icon: str = "✅"):
    st.toast(message, icon=icon)


def format_datetime(dt_str):
    if not dt_str:
        return "-"
    try:
        normalized = str(dt_str).replace("Z", "").replace("+00:00", "")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(dt_str)
