import logging
from datetime import date
from enum import Enum
from dataclasses import dataclass
from typing import Literal

from config import SAFRA_MONTHS, ENTRESSAFRA_MONTHS

logger = logging.getLogger(__name__)

Regime = Literal["safra", "entressafra"]


class PremiumClassification(Enum):
    MUITO_BAIXO = "muito_baixo"
    BAIXO = "baixo"
    NEUTRO = "neutro"
    ALTO = "alto"
    MUITO_ALTO = "muito_alto"


@dataclass(frozen=True)
class PremiumResult:
    date: date
    premium_raw: float
    regime: Regime
    percentile: float
    classification: PremiumClassification
    historical_count: int


CLASSIFICATION_THRESHOLDS: dict[PremiumClassification, tuple[float, float]] = {
    PremiumClassification.MUITO_BAIXO: (0, 20),
    PremiumClassification.BAIXO: (20, 40),
    PremiumClassification.NEUTRO: (40, 60),
    PremiumClassification.ALTO: (60, 80),
    PremiumClassification.MUITO_ALTO: (80, 100),
}

MIN_HISTORICAL_SAMPLES = 30


def get_regime(dt: date) -> Regime:
    if dt.month in SAFRA_MONTHS:
        return "safra"
    return "entressafra"


def calculate_percentile(value: float, historical: list[float]) -> float:
    if not historical:
        raise ValueError("Histórico vazio para cálculo de percentil")

    count_below = sum(1 for h in historical if h < value)
    count_equal = sum(1 for h in historical if h == value)

    percentile = (count_below + 0.5 * count_equal) / len(historical) * 100
    return round(percentile, 2)


def classify_premium(percentile: float) -> PremiumClassification:
    for classification, (lower, upper) in CLASSIFICATION_THRESHOLDS.items():
        if lower <= percentile < upper:
            return classification
    return PremiumClassification.MUITO_ALTO


def normalize_premium(
    dt: date, premium: float, historical_by_regime: list[float]
) -> PremiumResult:
    if premium is None:
        raise ValueError(f"Prêmio nulo para data {dt}")

    regime = get_regime(dt)

    if len(historical_by_regime) < MIN_HISTORICAL_SAMPLES:
        logger.warning(
            "Histórico insuficiente para regime %s: %d amostras (mínimo: %d)",
            regime,
            len(historical_by_regime),
            MIN_HISTORICAL_SAMPLES,
        )

    percentile = calculate_percentile(premium, historical_by_regime)
    classification = classify_premium(percentile)

    return PremiumResult(
        date=dt,
        premium_raw=premium,
        regime=regime,
        percentile=percentile,
        classification=classification,
        historical_count=len(historical_by_regime),
    )


def get_regime_months(regime: Regime) -> tuple[int, ...]:
    if regime == "safra":
        return SAFRA_MONTHS
    return ENTRESSAFRA_MONTHS
