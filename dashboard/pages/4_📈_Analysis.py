import streamlit as st
import sys
from pathlib import Path
from datetime import date
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data"))

from engine import DecisionEngine, MarketInputs
from scoring import (
    score_lineup,
    score_premium,
    score_competitiveness,
    score_demand,
    score_cambio,
)

st.set_page_config(page_title="Analysis | BasisMind", page_icon="📈", layout="wide")

st.title("📈 Sensitivity Analysis")
st.markdown("Understand how each variable affects the engine's final score.")

tab1, tab2, tab3 = st.tabs(
    ["Individual Sensitivity", "Scenario Matrix", "Decision Zones"]
)

with tab1:
    st.markdown("### How each component responds to inputs")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Line-up")
        st.markdown("*Weight: 30%*")

        lineup_data = []
        for var in range(-20, 21, 2):
            s = score_lineup(float(var))
            lineup_data.append({"Variation (%)": var, "Score": s})

        df_lineup = pd.DataFrame(lineup_data)
        st.line_chart(df_lineup.set_index("Variation (%)"), height=250)

        st.caption(
            """
        - **< -15%**: Score 0 (Strong Drop)
        - **-15% to +15%**: Linear
        - **> +15%**: Score 100 (Strong Rise)
        """
        )

    with col2:
        st.markdown("#### Premium")
        st.markdown("*Weight: 25%*")

        premium_data = []
        for pct in range(0, 101, 5):
            s = score_premium(float(pct))
            premium_data.append({"Percentile": pct, "Score": s})

        df_premium = pd.DataFrame(premium_data)
        st.line_chart(df_premium.set_index("Percentile"), height=250)

        st.caption(
            """
        - Percentile is already [0-100]
        - Score = Percentile (1:1)
        - Normalized by regime (crop/off-season)
        """
        )

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Competitiveness")
        st.markdown("*Weight: 20%*")

        comp_data = []
        for spread in range(-25, 26, 2):
            s = score_competitiveness(float(spread))
            comp_data.append({"Spread (USD/ton)": spread, "Score": s})

        df_comp = pd.DataFrame(comp_data)
        st.line_chart(df_comp.set_index("Spread (USD/ton)"), height=250)

        st.caption(
            """
        - **< -20**: Score 100 (Brazil very cheap)
        - **> +20**: Score 0 (Brazil very expensive)
        - Inverse relationship: negative spread is good
        """
        )

    with col4:
        st.markdown("#### Demand")
        st.markdown("*Weight: 15%*")

        demand_data = []
        for z in [x / 10 for x in range(-20, 21, 2)]:
            s = score_demand(z)
            demand_data.append({"Z-Score": z, "Score": s})

        df_demand = pd.DataFrame(demand_data)
        st.line_chart(df_demand.set_index("Z-Score"), height=250)

        st.caption(
            """
        - **< -1.5**: Score 0 (Very weak demand)
        - **> +1.5**: Score 100 (Very strong demand)
        - Z-score of pace vs 5-year average
        """
        )

    st.markdown("#### FX Rate")
    st.markdown("*Weight: 10%*")

    cambio_data = []
    for var in [x / 10 for x in range(-40, 41, 4)]:
        s = score_cambio(var)
        cambio_data.append({"5d Variation (%)": var, "Score": s})

    df_cambio = pd.DataFrame(cambio_data)

    col_cambio, col_exp = st.columns([2, 1])
    with col_cambio:
        st.line_chart(df_cambio.set_index("5d Variation (%)"), height=200)
    with col_exp:
        st.caption(
            """
        - **Inverse relationship**
        - Strong real (negative) = High score
        - Weak real (positive) = Low score
        - USD margin improves with strong real
        """
        )


with tab2:
    st.markdown("### Scenario Matrix: Lineup × Premium")
    st.markdown("Final score varying the two main components.")

    engine = DecisionEngine()

    lineup_vals = [-15, -10, -5, 0, 5, 10, 15]
    premium_vals = [20, 35, 50, 65, 80]

    matrix_data = []
    for lineup in lineup_vals:
        row = {"Lineup (%)": lineup}
        for premium in premium_vals:
            inputs = MarketInputs(
                dt=date.today(),
                var_semanal_lineup=float(lineup),
                percentil_premium=float(premium),
                spread_adjusted=0.0,
                z_pace=0.0,
                var_cambio_5d=0.0,
                chicago_percentile=50.0,
                chicago_is_spike=False,
                logistics_flag_active=False,
                logistics_reason=None,
            )
            report = engine.run(inputs)
            row[f"P{premium}"] = report.score_fisico
        matrix_data.append(row)

    df_matrix = pd.DataFrame(matrix_data)
    df_matrix.set_index("Lineup (%)", inplace=True)

    def color_score(val):
        if val >= 65:
            return "background-color: #28a745; color: white; font-weight: bold"
        elif val <= 35:
            return "background-color: #dc3545; color: white; font-weight: bold"
        else:
            return "background-color: #ffc107; color: black; font-weight: bold"

    st.dataframe(
        df_matrix.style.applymap(color_score).format("{:.0f}"), use_container_width=True
    )

    st.caption("Columns: Premium Percentile | Rows: Weekly Lineup Variation")

    st.markdown(
        """
    **Legend:**
    - Green: Score >= 65 (Strong Physical)
    - Yellow: Score 35-65 (Neutral)
    - Red: Score <= 35 (Weak Physical)
    """
    )


with tab3:
    st.markdown("### Decision Zones")
    st.markdown("Score → Recommendation Mapping")

    zonas_data = {
        "Score Range": ["80 - 100", "65 - 80", "35 - 65", "20 - 35", "0 - 20"],
        "Classification": ["Very Strong", "Strong", "Neutral", "Weak", "Very Weak"],
        "Physical Recommendation": [
            "STRONG INCREASE",
            "INCREASE",
            "HOLD",
            "REDUCE",
            "STRONG REDUCE",
        ],
        "Sizing": ["+25%", "+15%", "0%", "-15%", "-25%"],
        "Intensity": ["Strong", "Moderate", "Neutral", "Moderate", "Strong"],
    }

    df_zonas = pd.DataFrame(zonas_data)

    def style_zona(row):
        if row["Classification"] in ["Very Strong", "Strong"]:
            return ["background-color: #28a745; color: white"] * len(row)
        elif row["Classification"] in ["Very Weak", "Weak"]:
            return ["background-color: #dc3545; color: white"] * len(row)
        else:
            return ["background-color: #ffc107; color: black"] * len(row)

    st.dataframe(
        df_zonas.style.apply(style_zona, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    st.markdown("### Override Rules")
    st.markdown("Conditions that **dominate** scoring when activated:")

    overrides_data = {
        "Priority": [1, 2, 3, 4, 5],
        "Override": [
            "Logistics",
            "Joint Drop",
            "Premium Trap",
            "Critical Competitiveness",
            "Speculative Chicago",
        ],
        "Condition": [
            "Logistics flag active (strike, congestion)",
            "Lineup < -10% AND Premium < Percentile 40",
            "Premium > Percentile 80 AND Lineup < -10%",
            "Adjusted spread > +15 USD/ton",
            "Chicago spike > 5% without confirmed narrative",
        ],
        "Action": [
            "STRONG REDUCE (-30%)",
            "REDUCE (-20%)",
            "STRONG REDUCE (-25%)",
            "REDUCE (-15%)",
            "HOLD physical + STRONG HEDGE",
        ],
    }

    df_overrides = pd.DataFrame(overrides_data)
    st.dataframe(df_overrides, use_container_width=True, hide_index=True)

    st.info(
        """
    **Hierarchy:** When multiple overrides are active, the one with **highest priority** is applied
    (lower number = more conservative).
    """
    )

    st.markdown("---")

    st.markdown("### Hedge: Based on Chicago")

    hedge_data = {
        "Chicago Percentile": [
            ">= 80",
            "65 - 80",
            "50 - 65 (with spike)",
            "35 - 65",
            "20 - 35",
            "< 20",
        ],
        "Recommendation": [
            "STRONG INCREASE",
            "INCREASE",
            "INCREASE",
            "HOLD",
            "REDUCE",
            "STRONG REDUCE",
        ],
        "Delta vs Target": ["+20pp", "+10pp", "+10pp", "0pp", "-10pp", "-20pp"],
    }

    df_hedge = pd.DataFrame(hedge_data)

    def style_hedge(row):
        if "INCREASE" in row["Recommendation"]:
            return ["background-color: #28a745; color: white"] * len(row)
        elif "REDUCE" in row["Recommendation"]:
            return ["background-color: #dc3545; color: white"] * len(row)
        else:
            return ["background-color: #ffc107; color: black"] * len(row)

    st.dataframe(
        df_hedge.style.apply(style_hedge, axis=1),
        use_container_width=True,
        hide_index=True,
    )
