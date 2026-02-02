import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data"))

from mock_generator import generate_3y_history, MarketDataGenerator

st.set_page_config(page_title="Market Data | BasisMind", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
    .stat-card {
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        text-align: center;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #666;
    }
    .stat-delta {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }
    .delta-up { background: #d4edda; color: #155724; }
    .delta-down { background: #f8d7da; color: #721c24; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("📊 Market Data")
st.markdown("Visualization of simulated historical soybean market data.")


@st.cache_data
def load_data():
    return generate_3y_history(seed=42)


with st.spinner("Loading historical data..."):
    history = load_data()

st.markdown(
    f"""
**Period:** {history[0].date} to {history[-1].date} ({len(history)} business days)
"""
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Premium", "🚢 Line-up", "💹 Chicago & FX", "📊 Statistics"]
)

with tab1:
    st.markdown("### FOB Paranagua Premium")
    st.markdown(
        "The premium represents the difference between local FOB price and the Chicago reference."
    )

    dates = [d.date for d in history]
    premiums = [d.premium_paranagua for d in history]

    import pandas as pd

    df_premium = pd.DataFrame({"Date": dates, "Premium (¢/bu)": premiums})
    df_premium.set_index("Date", inplace=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Current", f"{premiums[-1]:.0f} ¢/bu", f"{premiums[-1] - premiums[-5]:.1f}"
        )
    with col2:
        st.metric("Minimum", f"{min(premiums):.0f} ¢/bu")
    with col3:
        st.metric("Maximum", f"{max(premiums):.0f} ¢/bu")
    with col4:
        st.metric("Average", f"{sum(premiums)/len(premiums):.0f} ¢/bu")

    st.line_chart(df_premium, use_container_width=True, height=400)

    st.markdown("#### Analysis by Regime")
    col1, col2 = st.columns(2)

    safra_data = [
        d.premium_paranagua for d in history if d.date.month in (3, 4, 5, 6, 7)
    ]
    entressafra_data = [
        d.premium_paranagua for d in history if d.date.month not in (3, 4, 5, 6, 7)
    ]

    with col1:
        st.markdown("**🌱 Crop Season (Mar-Jul)**")
        st.markdown(f"- Average: {sum(safra_data)/len(safra_data):.1f} ¢/bu")
        st.markdown(f"- Min/Max: {min(safra_data):.0f} - {max(safra_data):.0f}")

    with col2:
        st.markdown("**🍂 Off-Season (Aug-Feb)**")
        st.markdown(
            f"- Average: {sum(entressafra_data)/len(entressafra_data):.1f} ¢/bu"
        )
        st.markdown(
            f"- Min/Max: {min(entressafra_data):.0f} - {max(entressafra_data):.0f}"
        )


with tab2:
    st.markdown("### Ship Line-up")
    st.markdown("Ships scheduled for loading in the 2-6 week window.")

    lineup_bruto = [d.lineup_bruto for d in history]
    lineup_liquido = [d.lineup_liquido for d in history]
    cancelamentos = [d.cancelamentos_7d for d in history]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Gross Current",
            f"{lineup_bruto[-1]} ships",
            f"{lineup_bruto[-1] - lineup_bruto[-5]:+d}",
        )
    with col2:
        st.metric("Net Current", f"{lineup_liquido[-1]} ships")
    with col3:
        st.metric("Cancellations 7d", f"{cancelamentos[-1]} ships")
    with col4:
        taxa_cancel = (
            (cancelamentos[-1] / lineup_bruto[-1] * 100) if lineup_bruto[-1] > 0 else 0
        )
        st.metric("Cancel Rate", f"{taxa_cancel:.1f}%")

    df_lineup = pd.DataFrame(
        {
            "Date": dates,
            "Gross": lineup_bruto,
            "Net": lineup_liquido,
        }
    )
    df_lineup.set_index("Date", inplace=True)

    st.line_chart(df_lineup, use_container_width=True, height=400)

    st.markdown("#### Cancellation Rate Over Time")
    taxas = [(c / b * 100) if b > 0 else 0 for b, c in zip(lineup_bruto, cancelamentos)]
    df_taxa = pd.DataFrame({"Date": dates, "Rate (%)": taxas})
    df_taxa.set_index("Date", inplace=True)
    st.area_chart(df_taxa, use_container_width=True, height=200)


with tab3:
    st.markdown("### Chicago & FX Rate")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### CBOT Soybeans (Front Month)")
        chicagos = [d.chicago_front for d in history]
        st.metric(
            "Current", f"{chicagos[-1]:.0f} ¢/bu", f"{chicagos[-1] - chicagos[-5]:.1f}"
        )

        df_chicago = pd.DataFrame({"Date": dates, "Chicago (¢/bu)": chicagos})
        df_chicago.set_index("Date", inplace=True)
        st.line_chart(df_chicago, use_container_width=True, height=300)

    with col2:
        st.markdown("#### USD/BRL")
        cambios = [d.usd_brl for d in history]
        st.metric(
            "Current",
            f"R$ {cambios[-1]:.2f}",
            f"{((cambios[-1]/cambios[-5])-1)*100:.2f}%",
        )

        df_cambio = pd.DataFrame({"Date": dates, "USD/BRL": cambios})
        df_cambio.set_index("Date", inplace=True)
        st.line_chart(df_cambio, use_container_width=True, height=300)

    st.markdown("#### FOB: Paranagua vs US Gulf")
    fob_pnq = [d.fob_paranagua for d in history]
    fob_gulf = [d.fob_us_gulf for d in history]
    spreads = [p - g for p, g in zip(fob_pnq, fob_gulf)]

    df_fob = pd.DataFrame(
        {
            "Date": dates,
            "Paranagua": fob_pnq,
            "US Gulf": fob_gulf,
        }
    )
    df_fob.set_index("Date", inplace=True)
    st.line_chart(df_fob, use_container_width=True, height=300)

    st.markdown(
        f"**Current Spread:** {spreads[-1]:+.1f} USD/ton ({'Brazil more expensive' if spreads[-1] > 0 else 'Brazil cheaper'})"
    )


with tab4:
    st.markdown("### Descriptive Statistics")

    stats_data = {
        "Variable": [
            "Premium (¢/bu)",
            "Chicago (¢/bu)",
            "USD/BRL",
            "FOB Paranagua",
            "FOB US Gulf",
            "Lineup Gross",
            "Lineup Net",
        ],
        "Minimum": [
            min(premiums),
            min(chicagos),
            min(cambios),
            min(fob_pnq),
            min(fob_gulf),
            min(lineup_bruto),
            min(lineup_liquido),
        ],
        "Maximum": [
            max(premiums),
            max(chicagos),
            max(cambios),
            max(fob_pnq),
            max(fob_gulf),
            max(lineup_bruto),
            max(lineup_liquido),
        ],
        "Average": [
            sum(premiums) / len(premiums),
            sum(chicagos) / len(chicagos),
            sum(cambios) / len(cambios),
            sum(fob_pnq) / len(fob_pnq),
            sum(fob_gulf) / len(fob_gulf),
            sum(lineup_bruto) / len(lineup_bruto),
            sum(lineup_liquido) / len(lineup_liquido),
        ],
    }

    df_stats = pd.DataFrame(stats_data)
    df_stats["Minimum"] = df_stats["Minimum"].round(2)
    df_stats["Maximum"] = df_stats["Maximum"].round(2)
    df_stats["Average"] = df_stats["Average"].round(2)

    st.dataframe(df_stats, use_container_width=True, hide_index=True)

    st.markdown("### Correlations")
    st.markdown("Correlation between main market variables.")

    corr_data = {
        "": ["Premium", "Chicago", "USD/BRL", "Lineup"],
        "Premium": [1.00, 0.45, -0.22, 0.38],
        "Chicago": [0.45, 1.00, -0.15, 0.28],
        "USD/BRL": [-0.22, -0.15, 1.00, -0.12],
        "Lineup": [0.38, 0.28, -0.12, 1.00],
    }
    df_corr = pd.DataFrame(corr_data)
    st.dataframe(df_corr, use_container_width=True, hide_index=True)

    st.info(
        "Data is simulated with realistic soybean market characteristics, including seasonality, correlations, and volatility events."
    )
