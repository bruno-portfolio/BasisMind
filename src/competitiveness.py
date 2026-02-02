import logging
from datetime import date
from dataclasses import dataclass
from enum import Enum
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class CompetitivenessClass(Enum):
    BRASIL_MUITO_BARATO = "brasil_muito_barato"
    BRASIL_BARATO = "brasil_barato"
    NEUTRO = "neutro"
    BRASIL_CARO = "brasil_caro"
    BRASIL_MUITO_CARO = "brasil_muito_caro"


@dataclass(frozen=True)
class CompetitivenessResult:
    date: date
    fob_paranagua: float
    fob_us_gulf: float
    spread_fob: float
    freight_adjustment: float
    spread_adjusted: float
    classification: CompetitivenessClass
    freight_is_abnormal: bool
    weight_modifier: float


FREIGHT_DIFFERENTIAL_MONTHLY: dict[int, float] = {
    1: -8.0,
    2: -10.0,
    3: -12.0,
    4: -10.0,
    5: -6.0,
    6: -2.0,
    7: 2.0,
    8: 5.0,
    9: 8.0,
    10: 10.0,
    11: 6.0,
    12: 0.0,
}

COMPETITIVENESS_THRESHOLDS: dict[CompetitivenessClass, tuple[float, float]] = {
    CompetitivenessClass.BRASIL_MUITO_BARATO: (float("-inf"), -20),
    CompetitivenessClass.BRASIL_BARATO: (-20, -10),
    CompetitivenessClass.NEUTRO: (-10, 10),
    CompetitivenessClass.BRASIL_CARO: (10, 20),
    CompetitivenessClass.BRASIL_MUITO_CARO: (20, float("inf")),
}

CRITICAL_SPREAD_THRESHOLD: float = 15.0

FREIGHT_ABNORMAL_STD: float = 2.0


def get_freight_adjustment(month: int) -> float:
    return FREIGHT_DIFFERENTIAL_MONTHLY.get(month, 0.0)


def calculate_spread_fob(fob_paranagua: float, fob_us_gulf: float) -> float:
    return round(fob_paranagua - fob_us_gulf, 2)


def calculate_spread_adjusted(spread_fob: float, freight_adjustment: float) -> float:
    return round(spread_fob + freight_adjustment, 2)


def classify_competitiveness(spread_adjusted: float) -> CompetitivenessClass:
    for classification, (lower, upper) in COMPETITIVENESS_THRESHOLDS.items():
        if lower <= spread_adjusted < upper:
            return classification
    return CompetitivenessClass.BRASIL_MUITO_CARO


def is_freight_abnormal(
    current_freight: float, historical_freight: list[float]
) -> bool:
    if len(historical_freight) < 10:
        return False
    avg = mean(historical_freight)
    std = stdev(historical_freight) if len(historical_freight) > 1 else 0
    if std == 0:
        return False
    z_score = abs(current_freight - avg) / std
    return z_score > FREIGHT_ABNORMAL_STD


def compute_competitiveness(
    dt: date,
    fob_paranagua: float,
    fob_us_gulf: float,
    current_freight: float | None = None,
    historical_freight: list[float] | None = None,
) -> CompetitivenessResult:
    spread_fob = calculate_spread_fob(fob_paranagua, fob_us_gulf)
    freight_adjustment = get_freight_adjustment(dt.month)
    spread_adjusted = calculate_spread_adjusted(spread_fob, freight_adjustment)
    classification = classify_competitiveness(spread_adjusted)

    freight_abnormal = False
    weight_modifier = 1.0
    if current_freight is not None and historical_freight:
        freight_abnormal = is_freight_abnormal(current_freight, historical_freight)
        if freight_abnormal:
            weight_modifier = 0.5
            logger.warning(
                "Frete anormal detectado para %s: peso reduzido para 50%%", dt
            )

    return CompetitivenessResult(
        date=dt,
        fob_paranagua=fob_paranagua,
        fob_us_gulf=fob_us_gulf,
        spread_fob=spread_fob,
        freight_adjustment=freight_adjustment,
        spread_adjusted=spread_adjusted,
        classification=classification,
        freight_is_abnormal=freight_abnormal,
        weight_modifier=weight_modifier,
    )


def is_brazil_not_competitive(spread_adjusted: float) -> bool:
    return spread_adjusted > CRITICAL_SPREAD_THRESHOLD
