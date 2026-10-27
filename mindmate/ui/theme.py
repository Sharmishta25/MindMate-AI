"""Shared local-only design tokens. Never interpolate private content into CSS."""
import streamlit as st

PAGES = ["Welcome", "Mood tracker", "Journal", "Dashboard", "Wellness activities", "Weekly reports", "Get support", "Privacy & data", "Timeline", "Lifestyle", "Weekly plan", "Data portability", "Reminders"]
CSS = """
<style>
:root { --mm-ink:#203e34; --mm-muted:#4c6159; --mm-green:#27634f; --mm-line:#d8e0d9; }
.stApp { background:#f7f8f4; }
[data-testid="stMainBlockContainer"] { max-width:1160px; padding-top:2.5rem; padding-bottom:4rem; }
[data-testid="stSidebar"] { background:#edf1e9; border-right:1px solid var(--mm-line); }
[data-testid="stSidebar"] h1 { font-size:1.6rem; }
h1,h2,h3 { color:var(--mm-ink); letter-spacing:-.025em; }
h1 { font-family:Georgia,'Times New Roman',serif; font-weight:500; font-size:3.25rem; line-height:1.12; }
h2 { font-size:1.65rem; } h3 { font-size:1.18rem; }
p, label, li { line-height:1.65; }
[data-testid="stCaptionContainer"] { color:var(--mm-muted); font-size:.9rem; line-height:1.6; }
[data-testid="stVerticalBlockBorderWrapper"]>div { border-radius:16px; }
[data-testid="stForm"] { background:#fff; border:1px solid var(--mm-line); border-radius:18px; padding:1.5rem; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--mm-line); border-radius:14px; padding:1rem 1.1rem; }
[data-testid="stMetricValue"] { color:var(--mm-ink); font-size:2rem; }
[data-testid="stAlert"] { border-radius:12px; }
.stButton button, .stDownloadButton button { border-radius:10px; min-height:44px; font-weight:600; }
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="radio"]:focus-visible { outline:3px solid #27634f !important; outline-offset:3px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap:.25rem; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding:.35rem .5rem; border-radius:8px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#dde7dc; }
[data-testid="stExpander"] { background:#fff; border-radius:12px; }
.mm-eyebrow { color:#355e4d; letter-spacing:.14em; font-size:.76rem; font-weight:700; margin-bottom:.75rem; }
.mm-intro { color:#4c6159; font-size:1.15rem; max-width:42rem; line-height:1.7; }
.mm-note { background:#e7eee3; border:1px solid #cbd9ca; border-radius:18px; padding:1.4rem; color:#203e34; }
.mm-note p { margin-bottom:.7rem; }
.mm-footer { border-top:1px solid #d8e0d9; padding-top:1rem; margin-top:1.5rem; color:#4c6159; font-size:.85rem; }
@media (max-width:760px) {
 [data-testid="stMainBlockContainer"] { padding:1.4rem 1rem 3rem; }
 h1 { font-size:2.35rem; }
 [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.8rem; }
 [data-testid="stColumn"] { flex:1 1 100%; min-width:0; }
 [data-testid="stForm"] { padding:1rem; }
}
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { scroll-behavior:auto !important; animation:none !important; transition:none !important; } }
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def navigate(page):
    if page not in PAGES:
        raise ValueError("Unknown page")
    st.session_state["navigation"] = page


def page_intro(title, description):
    st.header(title)
    st.write(description)


def chart_style(fig):
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                      font=dict(family="Arial, sans-serif", color="#203e34", size=13),
                      title=dict(font=dict(size=18)), margin=dict(l=20,r=20,t=65,b=35),
                      hovermode="x unified", showlegend=False, height=350)
    fig.update_traces(line_color="#27634f", line_width=3, marker_size=8)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e2e8df", zeroline=False)
    return fig
