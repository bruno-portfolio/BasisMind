import streamlit as st

st.set_page_config(
    page_title="BasisMind | Grain Trading Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #2d5a87;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .arch-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .feature-card {
        background: #1a1a2e;
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        height: 100%;
        border-top: 3px solid #2d5a87;
    }

    .feature-card h4 {
        color: white;
        margin-top: 0.5rem;
    }

    .feature-card p {
        color: #a0aec0;
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    [data-testid="stSidebar"] {
        background: #1a1a2e;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }

    [data-testid="stSidebar"] a {
        color: #a0aec0 !important;
    }

    [data-testid="stSidebar"] a:hover {
        color: white !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
<div style="text-align: center; padding: 1rem 0 2rem 0;">
    <h1 style="color: white; margin: 0; font-size: 1.8rem;">🌾 BasisMind</h1>
    <p style="color: #a0aec0; margin: 0.3rem 0 0 0; font-size: 0.85rem;">Grain Trading Intelligence</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
    <h1>🌾 BasisMind</h1>
    <p>Decision Intelligence for Physical Grain Trading</p>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-label">Components</div>
        <div class="metric-value">5</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-label">Overrides</div>
        <div class="metric-value">5</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-label">Modules</div>
        <div class="metric-value">12</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
    <div class="metric-card">
        <div class="metric-label">Accuracy</div>
        <div class="metric-value">100%</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("## Overview")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        """
    **BasisMind** transforms scattered market signals into **consistent** and
    **auditable** recommendations for physical soybean trading operations.

    ### What does it do?

    The system answers two objective questions:

    | Axis | Question |
    |------|----------|
    | **Physical** | Accelerate sales, hold position, or reduce exposure? |
    | **Hedge** | Increase Chicago hedge, hold, or reduce? |

    Every recommendation includes a **traceable justification** showing which signals drove the decision.
    """
    )

with col2:
    st.markdown(
        """
    ### Principles

    - Consistency over intuition
    - Full traceability
    - Explicit rules
    - No price prediction
    - Complements human judgment
    """
    )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("## System Architecture")

st.markdown(
    """
<div class="arch-box">
""",
    unsafe_allow_html=True,
)

st.code(
    """
┌─────────────────────────────────────────────────────────────────────┐
│                          MARKET INPUTS                              │
│   Premium │ Lineup │ Competitiveness │ FX Rate │ Demand │ Chicago  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SCORING ENGINE                               │
│                                                                     │
│   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│   │ Lineup │ │Premium │ │ Compet │ │ Demand │ │   FX   │           │
│   │  30%   │ │  25%   │ │  20%   │ │  15%   │ │  10%   │           │
│   └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘           │
│       └──────────┴──────────┴──────────┴──────────┘                 │
│                             │                                       │
│                    Aggregate Score [0-100]                          │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        OVERRIDE RULES                               │
│  Logistics │ Joint Drop │ Premium Trap │ Competitiveness │ Spike   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       BOOK MODULATION                               │
│         Exposure Limits │ Hedge Target │ Sizing                     │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DECISION OUTPUT                               │
│      Physical Recommendation │ Hedge Recommendation │ Justification │
└─────────────────────────────────────────────────────────────────────┘
""",
    language=None,
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("## Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h4>Weighted Scoring</h4>
        <p>Combines 5 market indicators into a single [0-100]
        score with calibrated weights.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <h4>Override Rules</h4>
        <p>5 rules that dominate scoring in critical
        market situations.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">📈</div>
        <h4>Book Modulation</h4>
        <p>Adjusts recommendations based on current
        position and exposure limits.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <h4>Full Traceability</h4>
        <p>Every decision includes detailed justification
        with the signals that drove it.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">🌡️</div>
        <h4>Seasonality</h4>
        <p>Premium normalization by regime (crop vs off-season)
        eliminates incorrect comparisons.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
    <div class="feature-card">
        <div class="feature-icon">🎛️</div>
        <h4>Simulator</h4>
        <p>Test custom scenarios and see how the engine
        responds in real-time.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("## Navigation")

st.info(
    """
Use the **sidebar** to navigate between pages:

- **Market Data** - View simulated historical data
- **Decision Engine** - See the engine in action with real scenarios
- **Simulator** - Create your own scenarios and test the engine
- **Analysis** - Sensitivity analysis and components
- **Documentation** - Complete technical documentation
"""
)

st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Built as a portfolio project | Python - Streamlit - Data Engineering - Trading Systems</p>
</div>
""",
    unsafe_allow_html=True,
)
