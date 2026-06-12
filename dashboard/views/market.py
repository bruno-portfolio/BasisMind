import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from basismind.auxiliaries import calculate_var_percent
from basismind.config import CRITICAL_SPREAD_THRESHOLD, SAFRA_MONTHS
from data import load_history
from ui import AMBER, BLUE, GREEN, MUTED, ORANGE, RED, SURFACE, note, plot

st.title("Market Data")
st.caption(
    "Three years of synthetic daily data with realistic seasonality, correlations "
    "and volatility events — the same series that feeds the live decision on the "
    "Overview page."
)


@st.cache_data
def load_df() -> pd.DataFrame:
    history = load_history()
    frame = pd.DataFrame(
        {
            "date": [d.date for d in history],
            "premium": [d.premium_paranagua for d in history],
            "chicago": [d.chicago_front for d in history],
            "usd_brl": [d.usd_brl for d in history],
            "fob_pnq": [d.fob_paranagua for d in history],
            "fob_gulf": [d.fob_us_gulf for d in history],
            "lineup_gross": [d.lineup_bruto for d in history],
            "lineup_net": [d.lineup_liquido for d in history],
            "cancellations": [d.cancelamentos_7d for d in history],
            "exports": [d.exports_weekly_tons for d in history],
        }
    )
    frame["spread"] = frame["fob_pnq"] - frame["fob_gulf"]
    return frame


df = load_df()

k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Premium",
    f"{df.premium.iloc[-1]:.0f} ¢/bu",
    f"{df.premium.iloc[-1] - df.premium.iloc[-6]:+.1f} 5d",
)
k2.metric(
    "Net line-up",
    f"{df.lineup_net.iloc[-1]:.0f} ships",
    f"{df.lineup_net.iloc[-1] - df.lineup_net.iloc[-6]:+.0f} 5d",
)
k3.metric(
    "Chicago",
    f"{df.chicago.iloc[-1]:.0f} ¢/bu",
    f"{calculate_var_percent(df.chicago.iloc[-1], df.chicago.iloc[-6]):+.1f}% 5d",
)
k4.metric(
    "USD/BRL",
    f"{df.usd_brl.iloc[-1]:.2f}",
    f"{calculate_var_percent(df.usd_brl.iloc[-1], df.usd_brl.iloc[-6]):+.1f}% 5d",
)


def add_crop_season_bands(fig: go.Figure) -> None:
    for year in sorted({d.year for d in df.date}):
        fig.add_vrect(
            x0=f"{year}-{min(SAFRA_MONTHS):02d}-01",
            x1=f"{year}-{max(SAFRA_MONTHS) + 1:02d}-01",
            fillcolor="rgba(47, 191, 113, 0.05)",
            line_width=0,
        )


tab_premium, tab_lineup, tab_prices, tab_stats = st.tabs(
    ["Premium", "Line-up", "Chicago, FX & FOB", "Statistics"]
)

with tab_premium:
    note(
        "<b>Premium (basis)</b> is what buyers pay over the Chicago reference for "
        "physical beans at Paranaguá. The engine never reads its absolute level — "
        "it ranks today against 3 years of the <i>same regime</i> "
        "(green bands = crop season, Mar–Jul), because a premium that is cheap in "
        "August can be expensive in April."
    )
    fig = go.Figure()
    add_crop_season_bands(fig)
    fig.add_scatter(
        x=df.date,
        y=df.premium,
        mode="lines",
        name="Premium",
        line=dict(color=AMBER, width=1.6),
    )
    fig.update_layout(height=380, yaxis_title="¢/bu", showlegend=False)
    plot(fig)

    crop = df[df.date.map(lambda d: d.month in SAFRA_MONTHS)]
    off = df[df.date.map(lambda d: d.month not in SAFRA_MONTHS)]
    c1, c2 = st.columns(2)
    c1.metric(
        "Crop season average (Mar–Jul)",
        f"{crop.premium.mean():.1f} ¢/bu",
        f"range {crop.premium.min():.0f}–{crop.premium.max():.0f}",
        delta_color="off",
    )
    c2.metric(
        "Off-season average (Aug–Feb)",
        f"{off.premium.mean():.1f} ¢/bu",
        f"range {off.premium.min():.0f}–{off.premium.max():.0f}",
        delta_color="off",
    )

with tab_lineup:
    note(
        "<b>Line-up</b> is the vessel queue scheduled to load in the 2–6 week "
        "window — demand you can physically count. The engine watches the "
        "<i>weekly variation of the net line-up</i> (gross minus cancellations): "
        "a queue shrinking faster than -10%/week arms the most defensive overrides."
    )
    fig = go.Figure()
    fig.add_scatter(
        x=df.date,
        y=df.lineup_gross,
        mode="lines",
        name="Gross",
        line=dict(color=MUTED, width=1.2),
    )
    fig.add_scatter(
        x=df.date,
        y=df.lineup_net,
        mode="lines",
        name="Net",
        line=dict(color=BLUE, width=1.6),
        fill="tonexty",
        fillcolor="rgba(76, 154, 255, 0.08)",
    )
    fig.update_layout(height=340, yaxis_title="ships")
    plot(fig)

    rate = (df.cancellations / df.lineup_gross.where(df.lineup_gross > 0)) * 100
    fig2 = go.Figure(
        go.Scatter(
            x=df.date,
            y=rate,
            mode="lines",
            name="Cancellation rate",
            line=dict(color=ORANGE, width=1.4),
            fill="tozeroy",
            fillcolor="rgba(242, 145, 61, 0.10)",
        )
    )
    fig2.update_layout(height=220, yaxis_title="% of gross", showlegend=False)
    plot(fig2)

with tab_prices:
    note(
        "<b>Chicago</b> drives the hedge axis (high percentile = lock prices in). "
        "<b>USD/BRL</b> modulates the exporter's margin. The <b>FOB spread</b> "
        "(Paranaguá − US Gulf) is the competitiveness signal: above "
        f"+{CRITICAL_SPREAD_THRESHOLD:.0f} USD/ton, buyers have a cheaper origin "
        "and the Competitiveness override fires."
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(
            go.Scatter(
                x=df.date,
                y=df.chicago,
                mode="lines",
                line=dict(color=AMBER, width=1.5),
            )
        )
        fig.update_layout(height=280, title="CBOT front month (¢/bu)", showlegend=False)
        plot(fig)
    with c2:
        fig = go.Figure(
            go.Scatter(
                x=df.date,
                y=df.usd_brl,
                mode="lines",
                line=dict(color=BLUE, width=1.5),
            )
        )
        fig.update_layout(height=280, title="USD/BRL", showlegend=False)
        plot(fig)

    fig = go.Figure()
    fig.add_scatter(
        x=df.date,
        y=df.fob_pnq,
        mode="lines",
        name="FOB Paranaguá",
        line=dict(color=GREEN, width=1.4),
    )
    fig.add_scatter(
        x=df.date,
        y=df.fob_gulf,
        mode="lines",
        name="FOB US Gulf",
        line=dict(color=MUTED, width=1.4),
    )
    fig.update_layout(height=300, title="FOB comparison (USD/ton)")
    plot(fig)

    fig = go.Figure(
        go.Scatter(
            x=df.date,
            y=df.spread,
            mode="lines",
            name="Spread",
            line=dict(color=ORANGE, width=1.4),
        )
    )
    fig.add_hline(
        y=CRITICAL_SPREAD_THRESHOLD, line=dict(color=RED, width=1, dash="dash")
    )
    fig.add_hrect(
        y0=CRITICAL_SPREAD_THRESHOLD,
        y1=max(CRITICAL_SPREAD_THRESHOLD * 2, float(df.spread.max()) + 5),
        fillcolor="rgba(229, 72, 77, 0.08)",
        line_width=0,
        annotation_text="override zone",
        annotation_font_color=RED,
    )
    fig.update_layout(
        height=280,
        title="FOB spread (USD/ton) — positive = Brazil expensive",
        showlegend=False,
    )
    plot(fig)

with tab_stats:
    note(
        "Descriptive statistics and correlations computed from the series itself. "
        "Premium and line-up move together (both are demand), while USD/BRL is "
        "mildly inverse — exactly the structure the synthetic generator embeds."
    )
    pretty = {
        "premium": "Premium (¢/bu)",
        "chicago": "Chicago (¢/bu)",
        "usd_brl": "USD/BRL",
        "fob_pnq": "FOB Paranaguá",
        "fob_gulf": "FOB US Gulf",
        "spread": "FOB spread",
        "lineup_gross": "Line-up gross",
        "lineup_net": "Line-up net",
        "exports": "Exports (t/week)",
    }
    stats = (
        df[list(pretty)]
        .describe()
        .loc[["min", "max", "mean", "std"]]
        .T.rename(index=pretty)
        .round(2)
    )
    stats.columns = ["Min", "Max", "Mean", "Std"]
    st.dataframe(stats, use_container_width=True)

    corr_cols = ["premium", "chicago", "usd_brl", "lineup_net", "exports", "spread"]
    corr = df[corr_cols].corr().round(2)
    labels = [pretty[c] for c in corr_cols]
    fig = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            colorscale=[[0, RED], [0.5, SURFACE], [1, GREEN]],
            text=corr.values,
            texttemplate="%{text:.2f}",
            textfont=dict(family="JetBrains Mono, monospace", size=11),
            showscale=False,
        )
    )
    fig.update_layout(height=420, title="Correlation matrix (computed, not assumed)")
    plot(fig)
