from basismind.overrides import (
    OverrideType,
    check_armadilha_premio,
    check_chicago_especulativo,
    check_competitividade_critica,
    check_logistica,
    check_queda_conjunta,
    evaluate_overrides,
    get_override_justification,
)
from basismind.scoring import (
    HedgeRecommendation,
    HedgeResult,
    Intensity,
    PhysicalRecommendation,
    PhysicalResult,
)

NEUTRAL_PHYSICAL = PhysicalResult(
    recommendation=PhysicalRecommendation.MANTER,
    intensity=Intensity.NEUTRA,
    sizing_pct=0.0,
)
NEUTRAL_HEDGE = HedgeResult(
    recommendation=HedgeRecommendation.MANTER,
    intensity=Intensity.NEUTRA,
    delta_pp=0.0,
)

TRIPLE_OVERRIDE = dict(
    var_semanal_lineup=-15.0,
    percentil_premium=25.0,
    spread_adjusted=20.0,
    logistics_flag_active=True,
    logistics_reason="greve",
)


def evaluate(**overrides):
    defaults = dict(
        var_semanal_lineup=5.0,
        percentil_premium=50.0,
        spread_adjusted=0.0,
        logistics_flag_active=False,
        logistics_reason=None,
        is_speculative_spike=False,
        narrativa_confirmada=False,
        original_physical=NEUTRAL_PHYSICAL,
        original_hedge=NEUTRAL_HEDGE,
    )
    defaults.update(overrides)
    return evaluate_overrides(**defaults)


class TestQuedaConjunta:
    def test_lineup_caindo_e_premio_baixo_ativa(self):
        override = check_queda_conjunta(-12.0, 30.0)
        assert override is not None
        assert override.type == OverrideType.QUEDA_CONJUNTA
        assert override.physical_action.recommendation == PhysicalRecommendation.REDUZIR

    def test_premio_acima_do_limite_nao_ativa(self):
        assert check_queda_conjunta(-12.0, 45.0) is None

    def test_lineup_acima_do_limite_nao_ativa(self):
        assert check_queda_conjunta(-8.0, 30.0) is None

    def test_sem_dado_de_lineup_nao_ativa(self):
        assert check_queda_conjunta(None, 30.0) is None


class TestArmadilhaPremio:
    def test_premio_alto_com_lineup_caindo_ativa(self):
        override = check_armadilha_premio(-12.0, 85.0)
        assert override is not None
        assert override.type == OverrideType.ARMADILHA_PREMIO
        assert (
            override.physical_action.recommendation
            == PhysicalRecommendation.REDUZIR_FORTE
        )

    def test_premio_no_limite_nao_ativa(self):
        assert check_armadilha_premio(-12.0, 80.0) is None


class TestLogistica:
    def test_flag_ativa_com_motivo(self):
        override = check_logistica(True, "greve nos portos")
        assert override is not None
        assert override.reason == "greve nos portos"
        assert override.priority == 1

    def test_flag_ativa_sem_motivo_usa_default(self):
        override = check_logistica(True, None)
        assert override is not None
        assert override.reason == "Restricao logistica ativa"

    def test_flag_inativa(self):
        assert check_logistica(False) is None


class TestChicagoEspeculativo:
    def test_spike_sem_narrativa_ativa(self):
        override = check_chicago_especulativo(True, False)
        assert override is not None
        assert override.physical_action.recommendation == PhysicalRecommendation.MANTER
        assert (
            override.hedge_action.recommendation == HedgeRecommendation.AUMENTAR_FORTE
        )

    def test_spike_com_narrativa_confirmada_nao_ativa(self):
        assert check_chicago_especulativo(True, True) is None

    def test_sem_spike_nao_ativa(self):
        assert check_chicago_especulativo(False, False) is None


class TestCompetitividadeCritica:
    def test_spread_acima_do_limite_ativa(self):
        override = check_competitividade_critica(16.0)
        assert override is not None
        assert override.type == OverrideType.COMPETITIVIDADE_CRITICA

    def test_spread_no_limite_nao_ativa(self):
        assert check_competitividade_critica(15.0) is None


class TestEvaluateOverrides:
    def test_sem_condicoes_nao_ha_override(self):
        evaluation = evaluate()
        assert not evaluation.has_override
        assert evaluation.final_physical == NEUTRAL_PHYSICAL
        assert evaluation.final_hedge == NEUTRAL_HEDGE

    def test_logistica_domina_outros_overrides(self):
        evaluation = evaluate(**TRIPLE_OVERRIDE)
        assert evaluation.dominant_override.type == OverrideType.LOGISTICA
        assert len(evaluation.active_overrides) == 3
        assert (
            evaluation.final_physical.recommendation
            == PhysicalRecommendation.REDUZIR_FORTE
        )
        assert evaluation.final_hedge == NEUTRAL_HEDGE

    def test_justificativa_lista_overrides_secundarios(self):
        justification = get_override_justification(evaluate(**TRIPLE_OVERRIDE))
        assert "LOGISTICA" in justification
        assert "queda_conjunta" in justification
