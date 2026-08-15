"""Floating Prakriti AI Connect widget. Kept inside the chatbot package so Streamlit Cloud cannot confuse it with a third-party package named frontend."""
from __future__ import annotations
import streamlit as st

from chatbot.prakriti import stream_reply, save_message, load_history, clear_history

HEIGHT = 390

CSS = """
<style>
.st-key-prakriti_widget {
    position: fixed;
    right: 18px;
    bottom: 18px;
    width: min(390px, calc(100vw - 36px));
    z-index: 999990;
    background: rgba(7, 29, 36, .97);
    border: 1px solid rgba(52, 211, 153, .25);
    border-radius: 20px;
    padding: 10px;
    box-shadow: 0 18px 55px rgba(0,0,0,.45);
    backdrop-filter: blur(16px);
}
.st-key-prakriti_widget .stButton > button {
    border-radius: 14px;
}
.st-key-prakriti_widget [data-testid="stChatMessage"] {
    padding: 7px 10px;
    border-radius: 14px;
    margin-bottom: 5px;
}
.st-key-prakriti_widget [data-testid="stChatInput"] {
    background: rgba(255,255,255,.04);
}
@media (max-width: 520px) {
    .st-key-prakriti_widget {
        right: 10px; bottom: 10px;
        width: calc(100vw - 20px);
    }
}
</style>
"""


def _send(text: str, language: str):
    text = text.strip()
    if not text:
        return
    history = st.session_state["chat_history"]
    history.append({"role": "user", "content": text})
    user = st.session_state.get("user")
    session_id = st.session_state["chat_session_id"]
    if user:
        save_message(user["id"], session_id, "user", text, "hi" if language.startswith("Hindi") else "en")

    full = ""
    for chunk in stream_reply(history[:-1], text, language):
        full += chunk
    history.append({"role": "assistant", "content": full})
    if user:
        save_message(user["id"], session_id, "assistant", full, "hi" if language.startswith("Hindi") else "en")


def render_prakriti_widget():
    st.session_state.setdefault("chatbot_open", False)
    st.session_state.setdefault("chat_history", [])

    user = st.session_state.get("user")
    session_id = st.session_state["chat_session_id"]

    if user and not st.session_state.get("_prakriti_history_loaded"):
        try:
            saved = load_history(user["id"], session_id)
            if saved:
                st.session_state["chat_history"] = saved
        except Exception:
            pass
        st.session_state["_prakriti_history_loaded"] = True

    st.markdown(CSS, unsafe_allow_html=True)

    with st.container(key="prakriti_widget"):
        if not st.session_state["chatbot_open"]:
            if st.button("🌿 Prakriti AI", key="prakriti_launcher", help="Open Prakriti AI Connect"):
                st.session_state["chatbot_open"] = True
                st.rerun()
            return

        c1, c2 = st.columns([4,1])
        with c1:
            st.markdown("### 🌿 Prakriti AI Connect")
            st.caption("24×7 bilingual sustainability assistant")
        with c2:
            if st.button("✕", key="prakriti_close"):
                st.session_state["chatbot_open"] = False
                st.rerun()

        language = st.selectbox(
            "Language / भाषा",
            ["English", "Hindi / हिंदी"],
            key="prakriti_language",
            label_visibility="collapsed",
        )

        top1, top2 = st.columns([3,1])
        with top1:
            st.caption("Ask about waste, recycling, composting, e-waste or civic guidance.")
        with top2:
            if st.button("Clear", key="prakriti_clear"):
                st.session_state["chat_history"] = []
                if user:
                    try:
                        clear_history(user["id"], session_id)
                    except Exception:
                        pass
                st.rerun()

        with st.container(height=HEIGHT):
            if not st.session_state["chat_history"]:
                with st.chat_message("assistant", avatar="🌿"):
                    st.markdown("Namaste! I’m Prakriti AI Connect. How can I help with sustainability today?")
            for msg in st.session_state["chat_history"][-20:]:
                with st.chat_message(msg["role"], avatar="🌿" if msg["role"] == "assistant" else "🧑"):
                    st.markdown(msg["content"])

        prompt = st.chat_input("Ask Prakriti AI Connect...", key="prakriti_chat_input")
        if prompt:
            with st.spinner("🌿 Prakriti is thinking..."):
                _send(prompt, language)
            st.rerun()
