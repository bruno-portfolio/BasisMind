from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Final

from config import (
    SCORING_WEIGHT_LINEUP,
    SCORING_WEIGHT_PREMIUM,
    SCORING_WEIGHT_COMPETITIVENESS,
    SCORING_WEIGHT_DEMAND,
    SCORING_WEIGHT_CAMBIO,
    LINEUP_TREND_FORTE_QUEDA,
    LINEUP_TREND_FORTE_ALTA,
    COMPETITIVENESS_MUITO_BARATO,
    COMPETITIVENESS_MUITO_CARO,
    DEMAND_Z_FORTE,
    CAMBIO_FORTE_THRESHOLD,
    SCORING_FISICO_MUITO_FORTE,
    SCORING_FISICO_FORTE,
    SCORING_FISICO_FRACO,
    SCORING_FISICO_MUITO_FRACO,
    HEDGE_PERCENTIL_MUITO_ALTO,
    HEDGE_PERCENTIL_ALTO,
    HEDGE_PERCENTIL_BAIXO,
    HEDGE_PERCENTIL_MUITO_BAIXO,
)


class PhysicalRecommendation(Enum):
    REDUZIR_FORTE = "reduzir_forte"
    REDUZIR = "reduzir"
    MANTER = "manter"
    AUMENTAR = "aumentar"
    AUMENTAR_FORTE = "aumentar_forte"


class HedgeRecommendation(Enum):
    REDUZIR_FORTE = "reduzir_forte"
    REDUZIR = "reduzir"
    MANTER = "manter"
    AUMENTAR = "aumentar"
    AUMENTAR_FORTE = "aumentar_forte"


class Intensity(Enum):
    FORTE = "forte"
    MODERADA = "moderada"
    NEUTRA = "neutra"


class PhysicalClassification(Enum):
    MUITO_FRACO = "muito_fraco"
    FRACO = "fraco"
    NEUTRO = "neutro"
    FORTE = "forte"
    MUITO_FORTE = "muito_forte"


@dataclass(frozen=True)
class ComponentScores:
    lineup: float
    premium: float
    competitiveness: float
    demand: float
    cambio: float

    def as_dict(self) -> dict[str, float]:
        return {
            "lineup": self.lineup,
            "premium": self.premium,
            "competitiveness": self.competitiveness,
            "demand": self.demand,
            "cambio": self.cambio,
        }


@dataclass(frozen=True)
class PhysicalResult:
    recommendation: PhysicalRecommendation
    intensity: Intensity
    sizing_pct: float


@dataclass(frozen=True)
class HedgeResult:
    recommendation: HedgeRecommendation
    intensity: Intensity
    delta_pp: float


@dataclass(frozen=True)
class ScoringResult:
    date: date
    score_fisico: float
    classification: PhysicalClassification
    components: ComponentScores
    physical: PhysicalResult
    hedge: HedgeResult
    chicago_percentile: float
    chicago_is_spike: bool


def _clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    return max(min_val, min(max_val, value))


def _linear_map(
    value: float,
    in_min: float,
    in_max: float,
    out_min: float = 0.0,
    out_max: float = 100.0,
) -> float:
    if in_max == in_min:
        return (out_min + out_max) / 2
    ratio = (value - in_min) / (in_max - in_min)
    result = out_min + ratio * (out_max - out_min)
    return _clamp(result, min(out_min, out_max), max(out_min, out_max))


def score_lineup(var_semanal: float | None) -> float:
    if var_semanal is None:
        return 50.0
    return _linear_map(
        var_semanal,
        LINEUP_TREND_FORTE_QUEDA,
        LINEUP_TREND_FORTE_ALTA,
        0.0,
        100.0,
    )


def score_premium(percentile: float) -> float:
    return _clamp(percentile)


def score_competitiveness(spread_adjusted: float) -> float:
    return _linear_map(
        spread_adjusted,
        COMPETITIVENESS_MUITO_CARO,
        COMPETITIVENESS_MUITO_BARATO,
        0.0,
        100.0,
    )


def score_demand(z_pace: float | None) -> float:
    if z_pace is None:
        return 50.0
    return _linear_map(
        z_pace,
        -DEMAND_Z_FORTE,
        DEMAND_Z_FORTE,
        0.0,
        100.0,
    )


def score_cambio(var_5d: float | None) -> float:
    if var_5d is None:
        return 50.0
    return _linear_map(
        var_5d,
        CAMBIO_FORTE_THRESHOLD,
        -CAMBIO_FORTE_THRESHOLD,
        0.0,
        100.0,
    )


def compute_component_scores(
    var_semanal_lineup: float | None,
    percentil_premium: float,
    spread_adjusted: float,
    z_pace: float | None,
    var_cambio_5d: float | None,
) -> ComponentScores:
    return ComponentScores(
        lineup=score_lineup(var_semanal_lineup),
        premium=score_premium(percentil_premium),
        competitiveness=score_competitiveness(spread_adjusted),
        demand=score_demand(z_pace),
        cambio=score_cambio(var_cambio_5d),
    )


def compute_score_fisico(components: ComponentScores) -> float:
    score = (
        SCORING_WEIGHT_LINEUP * components.lineup
        + SCORING_WEIGHT_PREMIUM * components.premium
        + SCORING_WEIGHT_COMPETITIVENESS * components.competitiveness
        + SCORING_WEIGHT_DEMAND * components.demand
        + SCORING_WEIGHT_CAMBIO * components.cambio
    )
    return _clamp(score)


def classify_score_fisico(score: float) -> PhysicalClassification:
    if score >= SCORING_FISICO_MUITO_FORTE:
        return PhysicalClassification.MUITO_FORTE
    if score >= SCORING_FISICO_FORTE:
        return PhysicalClassification.FORTE
    if score <= SCORING_FISICO_MUITO_FRACO:
        return PhysicalClassification.MUITO_FRACO
    if score <= SCORING_FISICO_FRACO:
        return PhysicalClassification.FRACO
    return PhysicalClassification.NEUTRO


def determine_intensity(score: float) -> Intensity:
    if score > 80 or score < 20:
        return Intensity.FORTE
    if score > 65 or score < 35:
        return Intensity.MODERADA
    return Intensity.NEUTRA


def compute_physical_recommendation(score: float) -> PhysicalResult:
    intensity = determine_intensity(score)

    if score >= SCORING_FISICO_MUITO_FORTE:
        return PhysicalResult(
            recommendation=PhysicalRecommendation.AUMENTAR_FORTE,
            intensity=Intensity.FORTE,
            sizing_pct=25.0,
        )
    if score >= SCORING_FISICO_FORTE:
        return PhysicalResult(
            recommendation=PhysicalRecommendation.AUMENTAR,
            intensity=intensity,
            sizing_pct=15.0,
        )
    if score <= SCORING_FISICO_MUITO_FRACO:
        return PhysicalResult(
            recommendation=PhysicalRecommendation.REDUZIR_FORTE,
            intensity=Intensity.FORTE,
            sizing_pct=-25.0,
        )
    if score <= SCORING_FISICO_FRACO:
        return PhysicalResult(
            recommendation=PhysicalRecommendation.REDUZIR,
            intensity=intensity,
            sizing_pct=-15.0,
        )
    return PhysicalResult(
        recommendation=PhysicalRecommendation.MANTER,
        intensity=Intensity.NEUTRA,
        sizing_pct=0.0,
    )


def compute_hedge_recommendation(
    chicago_percentile: float,
    is_speculative_spike: bool = False,
) -> HedgeResult:
    if is_speculative_spike and chicago_percentile >= 50:
        return HedgeResult(
            recommendation=HedgeRecommendation.AUMENTAR,
            intensity=Intensity.MODERADA,
            delta_pp=10.0,
        )

    if chicago_percentile >= HEDGE_PERCENTIL_MUITO_ALTO:
        return HedgeResult(
            recommendation=HedgeRecommendation.AUMENTAR_FORTE,
            intensity=Intensity.FORTE,
            delta_pp=20.0,
        )
    if chicago_percentile >= HEDGE_PERCENTIL_ALTO:
        return HedgeResult(
            recommendation=HedgeRecommendation.AUMENTAR,
            intensity=Intensity.MODERADA,
            delta_pp=10.0,
        )
    if chicago_percentile <= HEDGE_PERCENTIL_MUITO_BAIXO:
        return HedgeResult(
            recommendation=HedgeRecommendation.REDUZIR_FORTE,
            intensity=Intensity.FORTE,
            delta_pp=-20.0,
        )
    if chicago_percentile <= HEDGE_PERCENTIL_BAIXO:
        return HedgeResult(
            recommendation=HedgeRecommendation.REDUZIR,
            intensity=Intensity.MODERADA,
            delta_pp=-10.0,
        )
    return HedgeResult(
        recommendation=HedgeRecommendation.MANTER,
        intensity=Intensity.NEUTRA,
        delta_pp=0.0,
    )


def compute_scoring(
    dt: date,
    var_semanal_lineup: float | None,
    percentil_premium: float,
    spread_adjusted: float,
    z_pace: float | None,
    var_cambio_5d: float | None,
    chicago_percentile: float,
    chicago_is_spike: bool = False,
) -> ScoringResult:
    components = compute_component_scores(
        var_semanal_lineup=var_semanal_lineup,
        percentil_premium=percentil_premium,
        spread_adjusted=spread_adjusted,
        z_pace=z_pace,
        var_cambio_5d=var_cambio_5d,
    )

    score_fisico = compute_score_fisico(components)
    classification = classify_score_fisico(score_fisico)
    physical = compute_physical_recommendation(score_fisico)
    hedge = compute_hedge_recommendation(chicago_percentile, chicago_is_spike)

    return ScoringResult(
        date=dt,
        score_fisico=score_fisico,
        classification=classification,
        components=components,
        physical=physical,
        hedge=hedge,
        chicago_percentile=chicago_percentile,
        chicago_is_spike=chicago_is_spike,
    )
