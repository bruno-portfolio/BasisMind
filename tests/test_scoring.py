import pytest

from basismind.scoring import (
    ComponentScores,
    HedgeRecommendation,
    Intensity,
    PhysicalClassification,
    PhysicalRecommendation,
    classify_score_fisico,
    compute_hedge_recommendation,
    compute_physical_recommendation,
    compute_score_fisico,
    score_cambio,
    score_competitiveness,
    score_demand,
    score_lineup,
    score_premium,
)


class TestScoreLineup:
    def test_sem_dado_retorna_neutro(self):
        assert score_lineup(None) == 50.0

    def test_forte_queda_zera_score(self):
        assert score_lineup(-15.0) == 0.0

    def test_forte_alta_maximiza_score(self):
        assert score_lineup(15.0) == 100.0

    def test_estavel_retorna_neutro(self):
        assert score_lineup(0.0) == 50.0

    def test_clamp_abaixo_do_range(self):
        assert score_lineup(-30.0) == 0.0

    def test_clamp_acima_do_range(self):
        assert score_lineup(30.0) == 100.0


class TestScorePremium:
    def test_percentil_passa_direto(self):
        assert score_premium(72.0) == 72.0

    def test_clamp_superior(self):
        assert score_premium(120.0) == 100.0

    def test_clamp_inferior(self):
        assert score_premium(-5.0) == 0.0


class TestScoreCompetitiveness:
    def test_brasil_muito_caro_zera_score(self):
        assert score_competitiveness(20.0) == 0.0

    def test_brasil_muito_barato_maximiza_score(self):
        assert score_competitiveness(-20.0) == 100.0

    def test_spread_neutro(self):
        assert score_competitiveness(0.0) == 50.0

    def test_spread_positivo_reduz_score(self):
        assert score_competitiveness(5.0) == 37.5


class TestScoreDemand:
    def test_sem_dado_retorna_neutro(self):
        assert score_demand(None) == 50.0

    def test_z_forte_negativo_zera(self):
        assert score_demand(-1.5) == 0.0

    def test_z_forte_positivo_maximiza(self):
        assert score_demand(1.5) == 100.0


class TestScoreCambio:
    def test_sem_dado_retorna_neutro(self):
        assert score_cambio(None) == 50.0

    def test_alta_forte_zera(self):
        assert score_cambio(3.0) == 0.0

    def test_queda_forte_maximiza(self):
        assert score_cambio(-3.0) == 100.0


class TestScoreFisico:
    def test_todos_componentes_maximos(self):
        components = ComponentScores(100, 100, 100, 100, 100)
        assert compute_score_fisico(components) == 100.0

    def test_peso_do_lineup(self):
        components = ComponentScores(100, 0, 0, 0, 0)
        assert compute_score_fisico(components) == pytest.approx(30.0)

    def test_pesos_somam_cem_por_cento(self):
        components = ComponentScores(50, 50, 50, 50, 50)
        assert compute_score_fisico(components) == pytest.approx(50.0)


class TestClassifyScoreFisico:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (80.0, PhysicalClassification.MUITO_FORTE),
            (79.9, PhysicalClassification.FORTE),
            (65.0, PhysicalClassification.FORTE),
            (64.9, PhysicalClassification.NEUTRO),
            (50.0, PhysicalClassification.NEUTRO),
            (35.1, PhysicalClassification.NEUTRO),
            (35.0, PhysicalClassification.FRACO),
            (20.0, PhysicalClassification.MUITO_FRACO),
        ],
    )
    def test_limites_de_classificacao(self, score, expected):
        assert classify_score_fisico(score) == expected


class TestPhysicalRecommendation:
    def test_muito_forte_aumenta_forte(self):
        result = compute_physical_recommendation(85.0)
        assert result.recommendation == PhysicalRecommendation.AUMENTAR_FORTE
        assert result.sizing_pct == 25.0

    def test_forte_aumenta(self):
        result = compute_physical_recommendation(70.0)
        assert result.recommendation == PhysicalRecommendation.AUMENTAR
        assert result.sizing_pct == 15.0

    def test_neutro_mantem(self):
        result = compute_physical_recommendation(50.0)
        assert result.recommendation == PhysicalRecommendation.MANTER
        assert result.sizing_pct == 0.0

    def test_fraco_reduz(self):
        result = compute_physical_recommendation(30.0)
        assert result.recommendation == PhysicalRecommendation.REDUZIR
        assert result.sizing_pct == -15.0

    def test_muito_fraco_reduz_forte(self):
        result = compute_physical_recommendation(15.0)
        assert result.recommendation == PhysicalRecommendation.REDUZIR_FORTE
        assert result.sizing_pct == -25.0


class TestHedgeRecommendation:
    def test_percentil_muito_alto(self):
        result = compute_hedge_recommendation(85.0)
        assert result.recommendation == HedgeRecommendation.AUMENTAR_FORTE
        assert result.delta_pp == 20.0

    def test_percentil_alto(self):
        result = compute_hedge_recommendation(70.0)
        assert result.recommendation == HedgeRecommendation.AUMENTAR

    def test_percentil_neutro(self):
        result = compute_hedge_recommendation(50.0)
        assert result.recommendation == HedgeRecommendation.MANTER
        assert result.delta_pp == 0.0

    def test_percentil_baixo(self):
        result = compute_hedge_recommendation(30.0)
        assert result.recommendation == HedgeRecommendation.REDUZIR

    def test_percentil_muito_baixo(self):
        result = compute_hedge_recommendation(15.0)
        assert result.recommendation == HedgeRecommendation.REDUZIR_FORTE
        assert result.delta_pp == -20.0

    def test_spike_especulativo_com_percentil_alto(self):
        result = compute_hedge_recommendation(60.0, is_speculative_spike=True)
        assert result.recommendation == HedgeRecommendation.AUMENTAR
        assert result.intensity == Intensity.MODERADA
        assert result.delta_pp == 10.0

    def test_spike_com_percentil_baixo_ignora_spike(self):
        result = compute_hedge_recommendation(30.0, is_speculative_spike=True)
        assert result.recommendation == HedgeRecommendation.REDUZIR
