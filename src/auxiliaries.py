import logging
from datetime import date
from dataclasses import dataclass
from enum import Enum
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class CambioSignal(Enum):
    FORTE_ALTA = "forte_alta"
    ALTA = "alta"
    NEUTRO = "neutro"
    QUEDA = "queda"
    FORTE_QUEDA = "forte_queda"


@dataclass(frozen=True)
class CambioMetrics:
    date: date
    usd_brl: float
    var_5d: float | None
    var_20d: float | None
    signal: CambioSignal | None
    modulation: float


CAMBIO_THRESHOLDS: dict[CambioSignal, tuple[float, float]] = {
    CambioSignal.FORTE_QUEDA: (float("-inf"), -3.0),
    CambioSignal.QUEDA: (-3.0, -1.0),
    CambioSignal.NEUTRO: (-1.0, 1.0),
    CambioSignal.ALTA: (1.0, 3.0),
    CambioSignal.FORTE_ALTA: (3.0, float("inf")),
}


def calculate_var_percent(current: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def classify_cambio_signal(var_5d: float | None) -> CambioSignal | None:
    if var_5d is None:
        return None
    for signal, (lower, upper) in CAMBIO_THRESHOLDS.items():
        if lower <= var_5d < upper:
            return signal
    return CambioSignal.FORTE_ALTA


def get_cambio_modulation(signal: CambioSignal | None) -> float:
    if signal is None:
        return 1.0
    modulations = {
        CambioSignal.FORTE_ALTA: 1.2,
        CambioSignal.ALTA: 1.1,
        CambioSignal.NEUTRO: 1.0,
        CambioSignal.QUEDA: 0.9,
        CambioSignal.FORTE_QUEDA: 0.8,
    }
    return modulations.get(signal, 1.0)


def compute_cambio_metrics(
    dt: date,
    usd_brl: float,
    usd_brl_5d_ago: float | None = None,
    usd_brl_20d_ago: float | None = None,
) -> CambioMetrics:
    var_5d = calculate_var_percent(usd_brl, usd_brl_5d_ago)
    var_20d = calculate_var_percent(usd_brl, usd_brl_20d_ago)
    signal = classify_cambio_signal(var_5d)
    modulation = get_cambio_modulation(signal)

    return CambioMetrics(
        date=dt,
        usd_brl=usd_brl,
        var_5d=var_5d,
        var_20d=var_20d,
        signal=signal,
        modulation=modulation,
    )


class DemandSignal(Enum):
    MUITO_FRACA = "muito_fraca"
    FRACA = "fraca"
    NORMAL = "normal"
    FORTE = "forte"
    MUITO_FORTE = "muito_forte"


@dataclass(frozen=True)
class DemandMetrics:
    date: date
    exports_weekly: float
    mean_5y: float | None
    std_5y: float | None
    z_pace: float | None
    signal: DemandSignal | None


DEMAND_Z_THRESHOLDS: dict[DemandSignal, tuple[float, float]] = {
    DemandSignal.MUITO_FRACA: (float("-inf"), -1.5),
    DemandSignal.FRACA: (-1.5, -0.5),
    DemandSignal.NORMAL: (-0.5, 0.5),
    DemandSignal.FORTE: (0.5, 1.5),
    DemandSignal.MUITO_FORTE: (1.5, float("inf")),
}


def calculate_z_pace(
    exports_weekly: float, historical_same_week: list[float]
) -> tuple[float | None, float | None, float | None]:
    if len(historical_same_week) < 3:
        return None, None, None

    avg = mean(historical_same_week)
    std = stdev(historical_same_week) if len(historical_same_week) > 1 else 0

    if std == 0:
        return avg, std, 0.0

    z = (exports_weekly - avg) / std
    return avg, std, round(z, 2)


def classify_demand_signal(z_pace: float | None) -> DemandSignal | None:
    if z_pace is None:
        return None
    for signal, (lower, upper) in DEMAND_Z_THRESHOLDS.items():
        if lower <= z_pace < upper:
            return signal
    return DemandSignal.MUITO_FORTE


def compute_demand_metrics(
    dt: date, exports_weekly: float, historical_same_week_5y: list[float]
) -> DemandMetrics:
    avg, std, z_pace = calculate_z_pace(exports_weekly, historical_same_week_5y)
    signal = classify_demand_signal(z_pace)

    return DemandMetrics(
        date=dt,
        exports_weekly=exports_weekly,
        mean_5y=avg,
        std_5y=std,
        z_pace=z_pace,
        signal=signal,
    )


@dataclass(frozen=True)
class LogisticsFlag:
    is_active: bool
    reason: str | None
    manual_event: str | None


WAIT_TIME_THRESHOLD_DAYS: int = 15
WAIT_TIME_CONSECUTIVE_WEEKS: int = 2
LOADING_RATE_THRESHOLD: float = 0.70


def compute_logistics_flag(
    wait_time_days: float | None = None,
    wait_time_weeks_above: int = 0,
    loading_rate: float | None = None,
    manual_event: str | None = None,
) -> LogisticsFlag:
    reasons = []

    if (
        wait_time_days is not None
        and wait_time_days > WAIT_TIME_THRESHOLD_DAYS
        and wait_time_weeks_above >= WAIT_TIME_CONSECUTIVE_WEEKS
    ):
        reasons.append(
            f"espera_navios>{WAIT_TIME_THRESHOLD_DAYS}d_por_{wait_time_weeks_above}sem"
        )

    if loading_rate is not None and loading_rate < LOADING_RATE_THRESHOLD:
        reasons.append(f"taxa_embarque={loading_rate*100:.0f}%<70%")

    if manual_event:
        reasons.append(f"evento_manual:{manual_event}")

    is_active = len(reasons) > 0

    return LogisticsFlag(
        is_active=is_active,
        reason="; ".join(reasons) if reasons else None,
        manual_event=manual_event,
    )


class ChicagoSignal(Enum):
    MUITO_BAIXO = "muito_baixo"
    BAIXO = "baixo"
    NEUTRO = "neutro"
    ALTO = "alto"
    MUITO_ALTO = "muito_alto"


@dataclass(frozen=True)
class ChicagoMetrics:
    date: date
    chicago_front: float
    percentile: float
    signal: ChicagoSignal
    var_5d: float | None
    is_speculative_spike: bool


CHICAGO_PERCENTILE_THRESHOLDS: dict[ChicagoSignal, tuple[float, float]] = {
    ChicagoSignal.MUITO_BAIXO: (0, 20),
    ChicagoSignal.BAIXO: (20, 40),
    ChicagoSignal.NEUTRO: (40, 60),
    ChicagoSignal.ALTO: (60, 80),
    ChicagoSignal.MUITO_ALTO: (80, 100),
}

CHICAGO_SPECULATIVE_SPIKE_THRESHOLD: float = 5.0


def calculate_percentile(value: float, historical: list[float]) -> float:
    if not historical:
        return 50.0
    count_below = sum(1 for h in historical if h < value)
    count_equal = sum(1 for h in historical if h == value)
    percentile = (count_below + 0.5 * count_equal) / len(historical) * 100
    return round(percentile, 2)


def classify_chicago_signal(percentile: float) -> ChicagoSignal:
    for signal, (lower, upper) in CHICAGO_PERCENTILE_THRESHOLDS.items():
        if lower <= percentile < upper:
            return signal
    return ChicagoSignal.MUITO_ALTO


def compute_chicago_metrics(
    dt: date,
    chicago_front: float,
    historical_180d: list[float],
    chicago_5d_ago: float | None = None,
) -> ChicagoMetrics:
    percentile = calculate_percentile(chicago_front, historical_180d)
    signal = classify_chicago_signal(percentile)
    var_5d = calculate_var_percent(chicago_front, chicago_5d_ago)

    is_speculative = False
    if var_5d is not None and var_5d > CHICAGO_SPECULATIVE_SPIKE_THRESHOLD:
        is_speculative = True
        logger.warning("Spike especulativo detectado em Chicago: +%.1f%% em 5d", var_5d)

    return ChicagoMetrics(
        date=dt,
        chicago_front=chicago_front,
        percentile=percentile,
        signal=signal,
        var_5d=var_5d,
        is_speculative_spike=is_speculative,
    )
