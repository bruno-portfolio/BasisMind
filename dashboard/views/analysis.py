import plotly.graph_objects as go
import streamlit as st

from basismind.config import (
    SCORING_FISICO_FORTE,
    SCORING_FISICO_FRACO,
    SCORING_FISICO_MUITO_FORTE,
    SCORING_FISICO_MUITO_FRACO,
)
from basismind.scoring import (
    compute_component_scores,
    compute_score_fisico,
    score_cambio,
    score_competitiveness,
    score_demand,
    score_lineup,
    score_premium,
)
from ui import (
    ACTION_LABELS,
    AMBER,
    BG,
    BLUE,
    CLASS_COLORS,
    COMPONENT_WEIGHTS,
    GREEN,
    GREEN_DEEP,
    ORANGE,
    RED,
    note,
    plot,
)

st.title("Sensitivity")
st.caption(
    "How each signal maps into its 0–100 component score, and how the blended "
    "score behaves when the two heaviest signals move together."
)

tab_curves, tab_matrix, tab_zones = st.tabs(
    ["Component curves", "Line-up × Premium matrix", "Decision zones"]
)


def curve_fig(xs, ys, x_title, color):
    fig = go.Figure(
        go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=2.2))
    )
    fig.add_hrect(
        y0=SCORING_FISICO_FORTE,
        y1=100,
        fillcolor="rgba(47, 191, 113, 0.07)",
        line_width=0,
    )
    fig.add_hrect(
        y0=0,
        y1=SCORING_FISICO_FRACO,
        fillcolor="rgba(229, 72, 77, 0.07)",
        line_width=0,
    )
    fig.update_layout(
        height=260,
        xaxis_title=x_title,
        yaxis=dict(range=[-4, 104], title="score"),
        showlegend=False,
    )
    return fig


with tab_curves:
    note(
        "Every signal is linearly mapped between two calibrated bounds and clamped "
        "to 0–100, so no single day can blow up the blend. Green band = scores that "
        "push toward <i>increase</i>, red band = toward <i>reduce</i>."
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"##### Line-up — weight {COMPONENT_WEIGHTS['lineup']}%")
        xs = [x / 2 for x in range(-40, 41)]
        plot(curve_fig(xs, [score_lineup(x) for x in xs], "weekly variation (%)", BLUE))
        st.caption("Saturates at ±15%: beyond that, a drop is a drop.")
    with c2:
        st.markdown(f"##### Premium — weight {COMPONENT_WEIGHTS['premio']}%")
        xs = list(range(0, 101))
        plot(curve_fig(xs, [score_premium(float(x)) for x in xs], "percentile", AMBER))
        st.caption("Identity map: the percentile (vs same regime) is the score.")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(
            f"##### Competitiveness — weight {COMPONENT_WEIGHTS['competitividade']}%"
        )
        xs = [x / 2 for x in range(-50, 51)]
        plot(
            curve_fig(
                xs,
                [score_competitiveness(x) for x in xs],
                "adjusted spread (USD/ton)",
                GREEN,
            )
        )
        st.caption("Inverse: negative spread (Brazil cheap) scores high.")
    with c4:
        st.markdown(f"##### Demand — weight {COMPONENT_WEIGHTS['demanda']}%")
        xs = [x / 10 for x in range(-25, 26)]
        plot(curve_fig(xs, [score_demand(x) for x in xs], "pace z-score", ORANGE))
        st.caption("Saturates at ±1.5σ vs the 5-year same-week average.")

    c5, c6 = st.columns(2)
    with c5:
        st.markdown(f"##### FX — weight {COMPONENT_WEIGHTS['cambio']}%")
        xs = [x / 10 for x in range(-40, 41)]
        plot(
            curve_fig(
                xs, [score_cambio(x) for x in xs], "USD/BRL 5d variation (%)", RED
            )
        )
        st.caption(
            "Inverse: a strengthening real scores high — supply retention: "
            "farmers slow their selling."
        )
    with c6:
        st.markdown("##### Why linear maps?")
        st.markdown("""
- **Interpretable** — every point of score traces back to a signal level.
- **Robust** — clamping caps the influence of outliers and fat tails.
- **Tunable** — the bounds live in `config.py`, one constant per knob.

Missing signals degrade gracefully: a `None` input scores a neutral 50
instead of breaking the blend.
""")

with tab_matrix:
    note(
        "The blended score with everything else held neutral. The diagonal "
        "structure shows the two demand signals reinforcing each other — and the "
        "flat red row at the bottom is the <b>Joint Drop / Premium Trap</b> "
        "territory where overrides take over regardless of the blend."
    )

    lineup_vals = tuple(range(-20, 21, 2))
    premium_vals = tuple(range(0, 101, 5))

    @st.cache_data
    def heatmap_scores(lineups: tuple, premiums: tuple) -> list[list[float]]:
        return [
            [
                compute_score_fisico(
                    compute_component_scores(
                        var_semanal_lineup=float(lineup),
                        percentil_premium=float(premium),
                        spread_adjusted=0.0,
                        z_pace=0.0,
                        var_cambio_5d=0.0,
                    )
                )
                for premium in premiums
            ]
            for lineup in lineups
        ]

    fig = go.Figure(
        go.Heatmap(
            z=heatmap_scores(lineup_vals, premium_vals),
            x=premium_vals,
            y=lineup_vals,
            colorscale=[
                [0, RED],
                [0.35, ORANGE],
                [0.5, AMBER],
                [0.65, GREEN],
                [1, GREEN_DEEP],
            ],
            zmin=0,
            zmax=100,
            colorbar=dict(title="score", outlinewidth=0),
            hovertemplate="premium P%{x} · line-up %{y}%<br>score %{z:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=520,
        xaxis_title="premium percentile",
        yaxis_title="line-up weekly variation (%)",
    )
    plot(fig)

with tab_zones:
    note(
        "The final mapping from score to action. The asymmetric middle band "
        "(35–65) is deliberate: a decision engine that flips on every wobble "
        "is worse than no engine at all."
    )

    zones = [
        (SCORING_FISICO_MUITO_FORTE, 100, "muito_forte", "aumentar_forte", "+25%"),
        (SCORING_FISICO_FORTE, SCORING_FISICO_MUITO_FORTE, "forte", "aumentar", "+15%"),
        (SCORING_FISICO_FRACO, SCORING_FISICO_FORTE, "neutro", "manter", "0%"),
        (SCORING_FISICO_MUITO_FRACO, SCORING_FISICO_FRACO, "fraco", "reduzir", "-15%"),
        (0, SCORING_FISICO_MUITO_FRACO, "muito_fraco", "reduzir_forte", "-25%"),
    ]

    fig = go.Figure()
    for lo, hi, cls, acao, sizing in zones:
        label = ACTION_LABELS[acao]
        fig.add_trace(
            go.Bar(
                x=[hi - lo],
                y=["score"],
                base=lo,
                orientation="h",
                marker=dict(color=CLASS_COLORS[cls]),
                text=f"{label} ({sizing})",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=12, color=BG),
                hovertemplate=f"{label}: score {lo:.0f}–{hi:.0f} · sizing {sizing}<extra></extra>",
            )
        )
    fig.update_layout(
        height=140,
        barmode="stack",
        showlegend=False,
        xaxis=dict(range=[0, 100], title=None),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=10, b=30),
    )
    plot(fig)

    st.markdown("##### Override rules — when the score stops mattering")
    st.markdown("""
| Priority | Override | Condition | Forced action |
|---------:|----------|-----------|---------------|
| 1 | **Logistics** | flag active (strike, congestion, loading collapse) | STRONG REDUCE (−30%) |
| 2 | **Joint Drop** | line-up < −10% **and** premium < P40 | REDUCE (−20%) |
| 3 | **Premium Trap** | premium > P80 **and** line-up < −10% | STRONG REDUCE (−25%) |
| 4 | **Competitiveness** | adjusted spread > +15 USD/ton | REDUCE (−15%) |
| 5 | **Chicago Spike** | >5% in 5d without confirmed narrative | HOLD physical, hedge +20pp |

Lower priority number wins when several fire — the most conservative reading
of the market prevails.
""")

    st.markdown("##### Hedge axis — driven by Chicago percentile")
    st.markdown("""
| Chicago percentile | Recommendation | Delta vs target |
|--------------------|----------------|-----------------|
| ≥ 80 | STRONG INCREASE | +20pp |
| 65 – 80 | INCREASE | +10pp |
| 50 – 65 with spike | INCREASE | +10pp |
| 35 – 65 | HOLD | 0pp |
| 20 – 35 | REDUCE | −10pp |
| < 20 | STRONG REDUCE | −20pp |
""")
