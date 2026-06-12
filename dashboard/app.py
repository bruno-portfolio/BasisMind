import streamlit as st

from ui import AMBER, MUTED, inject_css, sidebar_brand

st.set_page_config(
    page_title="BasisMind — Grain Trading Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
sidebar_brand()

nav = st.navigation(
    {
        "": [
            st.Page(
                "views/home.py", title="Overview", icon=":material/home:", default=True
            ),
        ],
        "Decide": [
            st.Page(
                "views/engine.py", title="Decision Engine", icon=":material/psychology:"
            ),
            st.Page("views/simulator.py", title="Simulator", icon=":material/tune:"),
        ],
        "Explore": [
            st.Page(
                "views/market.py", title="Market Data", icon=":material/monitoring:"
            ),
            st.Page(
                "views/analysis.py", title="Sensitivity", icon=":material/query_stats:"
            ),
        ],
        "Learn": [
            st.Page("views/docs.py", title="Methodology", icon=":material/menu_book:"),
        ],
    }
)

st.sidebar.markdown(
    f'<div style="margin-top: 1rem; font-size: 0.72rem; color: {MUTED};">'
    "Synthetic data · Portfolio project<br>"
    f'<a href="https://github.com/bruno-portfolio/BasisMind" style="color: {AMBER};">github.com/bruno-portfolio/BasisMind</a>'
    "</div>",
    unsafe_allow_html=True,
)

nav.run()
