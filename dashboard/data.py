import streamlit as st

from basismind.auxiliaries import (
    calculate_var_percent,
    calculate_z_pace,
    compute_chicago_metrics,
)
from basismind.competitiveness import compute_competitiveness
from basismind.engine import MarketInputs
from basismind.lineup import calculate_var_semanal
from basismind.mock_generator import MockMarketData, generate_3y_history
from basismind.premium import calculate_percentile, get_regime, get_regime_months


@st.cache_data
def load_history() -> list[MockMarketData]:
    return generate_3y_history(seed=42)


def derive_market_inputs(history: list[MockMarketData]) -> MarketInputs:
    current = history[-1]
    week_ago = history[-6]
    dt = current.date

    var_lineup = calculate_var_semanal(current.lineup_liquido, week_ago.lineup_liquido)

    regime_months = get_regime_months(get_regime(dt))
    premium_history = [
        d.premium_paranagua for d in history[:-1] if d.date.month in regime_months
    ]
    percentil = calculate_percentile(current.premium_paranagua, premium_history)

    competitiveness = compute_competitiveness(
        dt, current.fob_paranagua, current.fob_us_gulf
    )

    week_number = dt.isocalendar()[1]
    same_week_prior_years = [
        d.exports_weekly_tons
        for d in history[:-1]
        if d.date.isocalendar()[1] == week_number and d.date.year < dt.year
    ]
    _, _, z_pace = calculate_z_pace(current.exports_weekly_tons, same_week_prior_years)

    var_cambio = calculate_var_percent(current.usd_brl, week_ago.usd_brl)

    chicago = compute_chicago_metrics(
        dt,
        current.chicago_front,
        [d.chicago_front for d in history[-181:-1]],
        week_ago.chicago_front,
    )

    return MarketInputs(
        dt=dt,
        var_semanal_lineup=var_lineup,
        percentil_premium=percentil,
        spread_adjusted=competitiveness.spread_adjusted,
        z_pace=z_pace,
        var_cambio_5d=var_cambio,
        chicago_percentile=chicago.percentile,
        chicago_is_spike=chicago.is_speculative_spike,
        logistics_flag_active=False,
        logistics_reason=None,
    )


SCENARIO_VALUES = {
    "Export boom": dict(
        var_semanal_lineup=15.0,
        percentil_premium=82.0,
        spread_adjusted=-18.0,
        z_pace=1.2,
        var_cambio_5d=-2.0,
        chicago_percentile=70.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
    ),
    "Joint drop": dict(
        var_semanal_lineup=-15.0,
        percentil_premium=25.0,
        spread_adjusted=5.0,
        z_pace=-0.8,
        var_cambio_5d=1.5,
        chicago_percentile=40.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
    ),
    "Premium trap": dict(
        var_semanal_lineup=-12.0,
        percentil_premium=88.0,
        spread_adjusted=-3.0,
        z_pace=0.3,
        var_cambio_5d=-0.5,
        chicago_percentile=55.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
    ),
    "Logistics crisis": dict(
        var_semanal_lineup=5.0,
        percentil_premium=70.0,
        spread_adjusted=-8.0,
        z_pace=0.8,
        var_cambio_5d=0.2,
        chicago_percentile=55.0,
        chicago_is_spike=False,
        logistics_flag_active=True,
    ),
    "Chicago spike": dict(
        var_semanal_lineup=3.0,
        percentil_premium=55.0,
        spread_adjusted=2.0,
        z_pace=0.1,
        var_cambio_5d=0.3,
        chicago_percentile=78.0,
        chicago_is_spike=True,
        logistics_flag_active=False,
    ),
}
