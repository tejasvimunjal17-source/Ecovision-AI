import streamlit as st
import pandas as pd
from datetime import datetime
from backend.complaints import get_user_complaints
from utils.helpers import load_css, require_login, status_badge, priority_badge, format_datetime

st.set_page_config(page_title="My Dashboard | EcoVision AI", page_icon="🌿", layout="wide")
require_login(allowed_roles=["citizen"])
load_css()

user = st.session_state["user"]
first = user.get("full_name", "Citizen").split()[0]
complaints = get_user_complaints(user["id"])
df = pd.DataFrame(complaints) if complaints else pd.DataFrame()
resolved = int((df["status"] == "Resolved").sum()) if not df.empty and "status" in df else 0
pending = max(len(df) - resolved, 0)
points = int(user.get("reward_points") or 0)

st.markdown(f'''
<div class="eco-greeting">
  <div class="eyebrow">EcoVision AI · Personal workspace</div>
  <h1>Your city, made cleaner, {first}.</h1>
  <p>A little improvement today creates a better neighbourhood tomorrow.</p>
</div>
''', unsafe_allow_html=True)

# Weekly strip inspired by the reference SaaS dashboard.
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
today = datetime.now().strftime("%a")
week_html = '<div class="eco-week">'
for d in days:
    cls = "eco-day active" if d == today else "eco-day"
    week_html += f'<div class="{cls}">{d}<strong>{datetime.now().day if d == today else "·"}</strong></div>'
week_html += '</div>'
st.markdown(week_html, unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
metrics = [(len(df), "Waste reports"), (resolved, "Resolved"), (pending, "In progress"), (points, "Green points")]
for col, (value, label) in zip([k1, k2, k3, k4], metrics):
    with col:
        st.markdown(f'<div class="eco-stat"><div class="num">{value:,}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="eco-section-title">Today\'s impact</div>', unsafe_allow_html=True)
left, right = st.columns([1.45, 1])
with left:
    st.markdown('''
    <div class="eco-card" style="min-height:245px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><h3 style="margin:.1rem 0">Your activity</h3><div class="muted">A quick view of your contribution this week.</div></div>
        <span class="eco-pill">Live</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:28px">
        <div><div style="font-size:1.8rem;font-weight:850">♻️</div><b>Segregate</b><div class="muted">At source</div></div>
        <div><div style="font-size:1.8rem;font-weight:850">📢</div><b>Report</b><div class="muted">Civic issue</div></div>
        <div><div style="font-size:1.8rem;font-weight:850">🌍</div><b>Reduce</b><div class="muted">Your footprint</div></div>
      </div>
    </div>
    ''', unsafe_allow_html=True)
with right:
    st.markdown(f'''
    <div class="eco-impact">
      <div style="font-size:1.5rem">🌱</div>
      <h3>Your personal impact</h3>
      <p>Keep reporting responsibly and use the Recycling Guide to increase your impact.</p>
      <div style="font-size:1.7rem;font-weight:850">{points:,} points</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('<div class="eco-section-title">Quick actions</div>', unsafe_allow_html=True)
a1, a2, a3, a4 = st.columns(4)
for col, page, label in [
    (a1, "pages/4_📢_Report_Waste.py", "📢 Report Waste"),
    (a2, "pages/5_📜_Complaint_History.py", "📜 Complaint History"),
    (a3, "pages/10_♻️_Recycling_Guide.py", "♻️ Recycling Guide"),
    (a4, "pages/11_🌍_Carbon_Calculator.py", "🌍 Carbon Calculator"),
]:
    with col:
        st.page_link(page, label=label, use_container_width=True)

st.markdown('<div class="eco-section-title">Your recent reports</div>', unsafe_allow_html=True)
if df.empty:
    st.markdown('''<div class="eco-card"><h3>No reports yet</h3><div class="muted">Your first waste report will appear here. Use Report Waste to get started.</div></div>''', unsafe_allow_html=True)
else:
    for _, row in df.head(5).iterrows():
        with st.container():
            c1, c2, c3 = st.columns([4, 1.2, 1.2])
            with c1:
                desc = str(row.get("description") or "No description")
                st.markdown(f"**#{row['id']} · {row['category']}** — {desc[:90]}{'...' if len(desc) > 90 else ''}")
                st.caption(f"📍 {row.get('ward') or 'N/A'} · 🕒 {format_datetime(row.get('created_at'))}")
            with c2:
                st.markdown(status_badge(row.get("status", "Submitted")), unsafe_allow_html=True)
            with c3:
                st.markdown(priority_badge(row.get("priority", "Medium")), unsafe_allow_html=True)
            st.divider()
