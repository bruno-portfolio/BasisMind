from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from config import (
    LINEUP_DROP_OVERRIDE_THRESHOLD,
    PREMIUM_THRESHOLD_BAIXO,
    PREMIUM_THRESHOLD_ALTO,
    CRITICAL_SPREAD_THRESHOLD,
)
from scoring import (
    PhysicalRecommendation,
    HedgeRecommendation,
    Intensity,
    PhysicalResult,
    HedgeResult,
)


class OverrideType(Enum):
    LOGISTICA = "logistica"
    QUEDA_CONJUNTA = "queda_conjunta"
    ARMADILHA_PREMIO = "armadilha_premio"
    COMPETITIVIDADE_CRITICA = "competitividade_critica"
    CHICAGO_ESPECULATIVO = "chicago_especulativo"


OVERRIDE_PRIORITY: dict[OverrideType, int] = {
    OverrideType.LOGISTICA: 1,
    OverrideType.QUEDA_CONJUNTA: 2,
    OverrideType.ARMADILHA_PREMIO: 3,
    OverrideType.COMPETITIVIDADE_CRITICA: 4,
    OverrideType.CHICAGO_ESPECULATIVO: 5,
}


@dataclass(frozen=True)
class Override:
    type: OverrideType
    reason: str
    physical_action: PhysicalResult | None
    hedge_action: HedgeResult | None
    priority: int

    @property
    def affects_physical(self) -> bool:
        return self.physical_action is not None

    @property
    def affects_hedge(self) -> bool:
        return self.hedge_action is not None


@dataclass(frozen=True)
class OverrideEvaluation:
    active_overrides: tuple[Override, ...]
    dominant_override: Override | None
    original_physical: PhysicalResult
    original_hedge: HedgeResult
    final_physical: PhysicalResult
    final_hedge: HedgeResult

    @property
    def has_override(self) -> bool:
        return self.dominant_override is not None


def check_queda_conjunta(
    var_semanal_lineup: float | None,
    percentil_premium: float,
) -> Override | None:
    if var_semanal_lineup is None:
        return None

    lineup_caindo = var_semanal_lineup < LINEUP_DROP_OVERRIDE_THRESHOLD
    premio_baixo = percentil_premium < PREMIUM_THRESHOLD_BAIXO

    if lineup_caindo and premio_baixo:
        return Override(
            type=OverrideType.QUEDA_CONJUNTA,
            reason=f"Line-up caindo ({var_semanal_lineup:.1f}%) e premio baixo (percentil {percentil_premium:.0f})",
            physical_action=PhysicalResult(
                recommendation=PhysicalRecommendation.REDUZIR,
                intensity=Intensity.FORTE,
                sizing_pct=-20.0,
            ),
            hedge_action=None,
            priority=OVERRIDE_PRIORITY[OverrideType.QUEDA_CONJUNTA],
        )
    return None


def check_armadilha_premio(
    var_semanal_lineup: float | None,
    percentil_premium: float,
) -> Override | None:
    if var_semanal_lineup is None:
        return None

    lineup_caindo = var_semanal_lineup < LINEUP_DROP_OVERRIDE_THRESHOLD
    premio_alto = percentil_premium > PREMIUM_THRESHOLD_ALTO

    if lineup_caindo and premio_alto:
        return Override(
            type=OverrideType.ARMADILHA_PREMIO,
            reason=f"Premio alto (percentil {percentil_premium:.0f}) mas line-up caindo ({var_semanal_lineup:.1f}%)",
            physical_action=PhysicalResult(
                recommendation=PhysicalRecommendation.REDUZIR_FORTE,
                intensity=Intensity.FORTE,
                sizing_pct=-25.0,
            ),
            hedge_action=None,
            priority=OVERRIDE_PRIORITY[OverrideType.ARMADILHA_PREMIO],
        )
    return None


def check_logistica(
    logistics_flag_active: bool,
    logistics_reason: str | None = None,
) -> Override | None:
    if logistics_flag_active:
        reason = logistics_reason or "Restricao logistica ativa"
        return Override(
            type=OverrideType.LOGISTICA,
            reason=reason,
            physical_action=PhysicalResult(
                recommendation=PhysicalRecommendation.REDUZIR_FORTE,
                intensity=Intensity.FORTE,
                sizing_pct=-30.0,
            ),
            hedge_action=None,
            priority=OVERRIDE_PRIORITY[OverrideType.LOGISTICA],
        )
    return None


def check_chicago_especulativo(
    is_speculative_spike: bool,
    narrativa_confirmada: bool = False,
) -> Override | None:
    if is_speculative_spike and not narrativa_confirmada:
        return Override(
            type=OverrideType.CHICAGO_ESPECULATIVO,
            reason="Spike especulativo em Chicago (>5% em 5d) sem narrativa confirmada",
            physical_action=PhysicalResult(
                recommendation=PhysicalRecommendation.MANTER,
                intensity=Intensity.MODERADA,
                sizing_pct=0.0,
            ),
            hedge_action=HedgeResult(
                recommendation=HedgeRecommendation.AUMENTAR_FORTE,
                intensity=Intensity.FORTE,
                delta_pp=20.0,
            ),
            priority=OVERRIDE_PRIORITY[OverrideType.CHICAGO_ESPECULATIVO],
        )
    return None


def check_competitividade_critica(
    spread_adjusted: float,
) -> Override | None:
    if spread_adjusted > CRITICAL_SPREAD_THRESHOLD:
        return Override(
            type=OverrideType.COMPETITIVIDADE_CRITICA,
            reason=f"Brasil nao-competitivo (spread +{spread_adjusted:.1f} USD/ton)",
            physical_action=PhysicalResult(
                recommendation=PhysicalRecommendation.REDUZIR,
                intensity=Intensity.MODERADA,
                sizing_pct=-15.0,
            ),
            hedge_action=None,
            priority=OVERRIDE_PRIORITY[OverrideType.COMPETITIVIDADE_CRITICA],
        )
    return None


def evaluate_overrides(
    var_semanal_lineup: float | None,
    percentil_premium: float,
    spread_adjusted: float,
    logistics_flag_active: bool,
    logistics_reason: str | None,
    is_speculative_spike: bool,
    narrativa_confirmada: bool,
    original_physical: PhysicalResult,
    original_hedge: HedgeResult,
) -> OverrideEvaluation:
    active: list[Override] = []

    if override := check_logistica(logistics_flag_active, logistics_reason):
        active.append(override)

    if override := check_queda_conjunta(var_semanal_lineup, percentil_premium):
        active.append(override)

    if override := check_armadilha_premio(var_semanal_lineup, percentil_premium):
        active.append(override)

    if override := check_competitividade_critica(spread_adjusted):
        active.append(override)

    if override := check_chicago_especulativo(
        is_speculative_spike, narrativa_confirmada
    ):
        active.append(override)

    active.sort(key=lambda o: o.priority)

    dominant: Override | None = active[0] if active else None

    final_physical = original_physical
    final_hedge = original_hedge

    if dominant:
        if dominant.physical_action:
            final_physical = dominant.physical_action
        if dominant.hedge_action:
            final_hedge = dominant.hedge_action

    return OverrideEvaluation(
        active_overrides=tuple(active),
        dominant_override=dominant,
        original_physical=original_physical,
        original_hedge=original_hedge,
        final_physical=final_physical,
        final_hedge=final_hedge,
    )


def get_override_justification(evaluation: OverrideEvaluation) -> str:
    if not evaluation.has_override:
        return "Nenhum override ativo. Recomendacao baseada no score."

    assert evaluation.dominant_override is not None

    lines = [f"OVERRIDE ATIVO: {evaluation.dominant_override.type.value.upper()}"]
    lines.append(f"Motivo: {evaluation.dominant_override.reason}")

    if len(evaluation.active_overrides) > 1:
        others = [o.type.value for o in evaluation.active_overrides[1:]]
        lines.append(f"Outros overrides ativos (menor prioridade): {', '.join(others)}")

    if evaluation.dominant_override.affects_physical:
        lines.append(
            f"Acao fisica: {evaluation.final_physical.recommendation.value} "
            f"(era: {evaluation.original_physical.recommendation.value})"
        )

    if evaluation.dominant_override.affects_hedge:
        lines.append(
            f"Acao hedge: {evaluation.final_hedge.recommendation.value} "
            f"(era: {evaluation.original_hedge.recommendation.value})"
        )

    return " | ".join(lines)
