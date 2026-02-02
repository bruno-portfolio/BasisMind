from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import date
from typing import Any

from config import (
    TRIGGER_LINEUP_CHANGE_PCT,
    TRIGGER_PREMIUM_STD,
    TRIGGER_CHICAGO_CHANGE_PCT,
    DEFAULT_LIMITE_LONG_PCT,
    DEFAULT_LIMITE_SHORT_PCT,
    DEFAULT_HEDGE_META_PCT,
)
from scoring import (
    compute_scoring,
    ScoringResult,
    PhysicalRecommendation,
    HedgeRecommendation,
    Intensity,
)
from overrides import (
    evaluate_overrides,
    get_override_justification,
    OverrideEvaluation,
    OverrideType,
)
from book import (
    BookState,
    ModulatedResult,
    modulate_by_book,
    calculate_effective_sizing,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketInputs:
    dt: date
    var_semanal_lineup: float | None
    percentil_premium: float
    spread_adjusted: float
    z_pace: float | None
    var_cambio_5d: float | None
    chicago_percentile: float
    chicago_is_spike: bool
    logistics_flag_active: bool
    logistics_reason: str | None
    narrativa_confirmada: bool = False


@dataclass(frozen=True)
class TriggerCheck:
    lineup_triggered: bool
    premium_triggered: bool
    logistics_triggered: bool
    chicago_triggered: bool

    @property
    def any_triggered(self) -> bool:
        return any(
            [
                self.lineup_triggered,
                self.premium_triggered,
                self.logistics_triggered,
                self.chicago_triggered,
            ]
        )

    @property
    def triggered_reasons(self) -> list[str]:
        reasons = []
        if self.lineup_triggered:
            reasons.append(f"Line-up mudou > {TRIGGER_LINEUP_CHANGE_PCT}%")
        if self.premium_triggered:
            reasons.append(f"Premio moveu > {TRIGGER_PREMIUM_STD} std")
        if self.logistics_triggered:
            reasons.append("Flag de logistica ativado")
        if self.chicago_triggered:
            reasons.append(f"Chicago moveu > {TRIGGER_CHICAGO_CHANGE_PCT}%")
        return reasons


@dataclass(frozen=True)
class DecisionReport:
    data_referencia: date
    score_fisico: float
    classificacao: str
    recomendacao_fisica: dict[str, Any]
    recomendacao_hedge: dict[str, Any]
    componentes: dict[str, dict[str, float]]
    overrides_ativos: list[str]
    override_dominante: str | None
    modulacao_aplicada: bool
    modulacao_razao: str | None
    justificativa: str

    def to_json(self, indent: int = 2) -> str:
        data = {
            "data_referencia": self.data_referencia.isoformat(),
            "score_fisico": round(self.score_fisico, 1),
            "classificacao": self.classificacao,
            "recomendacao_fisica": self.recomendacao_fisica,
            "recomendacao_hedge": self.recomendacao_hedge,
            "componentes": self.componentes,
            "overrides_ativos": self.overrides_ativos,
            "override_dominante": self.override_dominante,
            "modulacao_aplicada": self.modulacao_aplicada,
            "modulacao_razao": self.modulacao_razao,
            "justificativa": self.justificativa,
        }
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_referencia": self.data_referencia.isoformat(),
            "score_fisico": round(self.score_fisico, 1),
            "classificacao": self.classificacao,
            "recomendacao_fisica": self.recomendacao_fisica,
            "recomendacao_hedge": self.recomendacao_hedge,
            "componentes": self.componentes,
            "overrides_ativos": self.overrides_ativos,
            "override_dominante": self.override_dominante,
            "modulacao_aplicada": self.modulacao_aplicada,
            "modulacao_razao": self.modulacao_razao,
            "justificativa": self.justificativa,
        }


def check_triggers(
    var_lineup_atual: float | None,
    var_lineup_anterior: float | None,
    premium_zscore_move: float | None,
    logistics_flag_active: bool,
    var_chicago_semanal: float | None,
) -> TriggerCheck:
    lineup_triggered = False
    if var_lineup_atual is not None and var_lineup_anterior is not None:
        delta = abs(var_lineup_atual - var_lineup_anterior)
        lineup_triggered = delta > TRIGGER_LINEUP_CHANGE_PCT

    premium_triggered = False
    if premium_zscore_move is not None:
        premium_triggered = abs(premium_zscore_move) > TRIGGER_PREMIUM_STD

    chicago_triggered = False
    if var_chicago_semanal is not None:
        chicago_triggered = abs(var_chicago_semanal) > TRIGGER_CHICAGO_CHANGE_PCT

    return TriggerCheck(
        lineup_triggered=lineup_triggered,
        premium_triggered=premium_triggered,
        logistics_triggered=logistics_flag_active,
        chicago_triggered=chicago_triggered,
    )


def _build_justificativa(
    scoring: ScoringResult,
    override_eval: OverrideEvaluation,
    modulated: ModulatedResult,
) -> str:
    parts = []

    parts.append(
        f"Fisico {scoring.classification.value} (score {scoring.score_fisico:.0f})"
    )

    comp = scoring.components
    top_components = sorted(
        [
            ("lineup", comp.lineup),
            ("premio", comp.premium),
            ("competitividade", comp.competitiveness),
        ],
        key=lambda x: abs(x[1] - 50),
        reverse=True,
    )[:2]

    drivers = []
    for name, score in top_components:
        direction = "forte" if score > 65 else "fraco" if score < 35 else "neutro"
        drivers.append(f"{name} {direction}")
    parts.append(f"Drivers: {', '.join(drivers)}")

    if override_eval.has_override:
        parts.append(get_override_justification(override_eval))

    if modulated.modulation_reason:
        parts.append(f"Modulacao: {modulated.modulation_reason}")

    parts.append(
        f"Recomendacao: {modulated.physical.recommendation.value} (fisica), "
        f"{modulated.hedge.recommendation.value} (hedge)"
    )

    return " | ".join(parts)


def run_decision_engine(
    inputs: MarketInputs,
    book: BookState | None = None,
) -> DecisionReport:
    if book is None:
        book = BookState(
            exposicao_fisica_pct=0.0,
            limite_long_pct=DEFAULT_LIMITE_LONG_PCT,
            limite_short_pct=DEFAULT_LIMITE_SHORT_PCT,
            hedge_atual_pct=0.0,
            hedge_meta_pct=DEFAULT_HEDGE_META_PCT,
        )

    scoring = compute_scoring(
        dt=inputs.dt,
        var_semanal_lineup=inputs.var_semanal_lineup,
        percentil_premium=inputs.percentil_premium,
        spread_adjusted=inputs.spread_adjusted,
        z_pace=inputs.z_pace,
        var_cambio_5d=inputs.var_cambio_5d,
        chicago_percentile=inputs.chicago_percentile,
        chicago_is_spike=inputs.chicago_is_spike,
    )

    override_eval = evaluate_overrides(
        var_semanal_lineup=inputs.var_semanal_lineup,
        percentil_premium=inputs.percentil_premium,
        spread_adjusted=inputs.spread_adjusted,
        logistics_flag_active=inputs.logistics_flag_active,
        logistics_reason=inputs.logistics_reason,
        is_speculative_spike=inputs.chicago_is_spike,
        narrativa_confirmada=inputs.narrativa_confirmada,
        original_physical=scoring.physical,
        original_hedge=scoring.hedge,
    )

    modulated = modulate_by_book(
        physical=override_eval.final_physical,
        hedge=override_eval.final_hedge,
        book=book,
    )

    effective_sizing = calculate_effective_sizing(
        modulated.physical.sizing_pct,
        book,
    )

    justificativa = _build_justificativa(scoring, override_eval, modulated)

    return DecisionReport(
        data_referencia=inputs.dt,
        score_fisico=scoring.score_fisico,
        classificacao=scoring.classification.value,
        recomendacao_fisica={
            "acao": modulated.physical.recommendation.value,
            "intensidade": modulated.physical.intensity.value,
            "sizing_pct": round(effective_sizing, 1),
        },
        recomendacao_hedge={
            "acao": modulated.hedge.recommendation.value,
            "intensidade": modulated.hedge.intensity.value,
            "delta_pp": round(modulated.hedge.delta_pp, 1),
        },
        componentes={
            "lineup": {
                "score": round(scoring.components.lineup, 1),
                "var_semanal": inputs.var_semanal_lineup or 0.0,
            },
            "premio": {
                "score": round(scoring.components.premium, 1),
                "percentil": inputs.percentil_premium,
            },
            "competitividade": {
                "score": round(scoring.components.competitiveness, 1),
                "spread": inputs.spread_adjusted,
            },
            "demanda": {
                "score": round(scoring.components.demand, 1),
                "z_pace": inputs.z_pace or 0.0,
            },
            "cambio": {
                "score": round(scoring.components.cambio, 1),
                "var_5d": inputs.var_cambio_5d or 0.0,
            },
        },
        overrides_ativos=[o.type.value for o in override_eval.active_overrides],
        override_dominante=(
            override_eval.dominant_override.type.value
            if override_eval.dominant_override
            else None
        ),
        modulacao_aplicada=(
            modulated.physical_was_modulated or modulated.hedge_was_modulated
        ),
        modulacao_razao=modulated.modulation_reason,
        justificativa=justificativa,
    )


class DecisionEngine:
    def __init__(self, book: BookState | None = None):
        self._book = book or BookState(
            exposicao_fisica_pct=0.0,
            limite_long_pct=DEFAULT_LIMITE_LONG_PCT,
            limite_short_pct=DEFAULT_LIMITE_SHORT_PCT,
            hedge_atual_pct=0.0,
            hedge_meta_pct=DEFAULT_HEDGE_META_PCT,
        )
        self._last_report: DecisionReport | None = None

    @property
    def book(self) -> BookState:
        return self._book

    @property
    def last_report(self) -> DecisionReport | None:
        return self._last_report

    def update_book(self, book: BookState) -> None:
        self._book = book

    def run(self, inputs: MarketInputs) -> DecisionReport:
        report = run_decision_engine(inputs, self._book)
        self._last_report = report
        logger.info(
            "Decision engine run: score=%.1f, physical=%s, hedge=%s",
            report.score_fisico,
            report.recomendacao_fisica["acao"],
            report.recomendacao_hedge["acao"],
        )
        return report

    def run_and_print(self, inputs: MarketInputs) -> DecisionReport:
        report = self.run(inputs)
        print(report.to_json())
        return report
