import json
from datetime import date

import pytest

from basismind.book import BookState
from basismind.engine import (
    DecisionEngine,
    MarketInputs,
    check_triggers,
    run_decision_engine,
)

OPPORTUNITY = dict(
    var_semanal_lineup=15.0,
    percentil_premium=82.0,
    spread_adjusted=-18.0,
    z_pace=1.2,
    var_cambio_5d=-2.0,
)


def make_inputs(**overrides):
    defaults = dict(
        dt=date(2024, 5, 15),
        var_semanal_lineup=8.0,
        percentil_premium=72.0,
        spread_adjusted=5.0,
        z_pace=0.5,
        var_cambio_5d=-0.8,
        chicago_percentile=65.0,
        chicago_is_spike=False,
        logistics_flag_active=False,
        logistics_reason=None,
    )
    defaults.update(overrides)
    return MarketInputs(**defaults)


def make_book(exposicao=30.0, hedge_atual=45.0):
    return BookState(
        exposicao_fisica_pct=exposicao,
        limite_long_pct=80.0,
        limite_short_pct=-50.0,
        hedge_atual_pct=hedge_atual,
        hedge_meta_pct=60.0,
    )


class TestCheckTriggers:
    def test_variacao_de_lineup_acima_do_limite_dispara(self):
        result = check_triggers(35.0, 10.0, None, False, None)
        assert result.lineup_triggered
        assert result.any_triggered

    def test_movimento_de_premio_dispara(self):
        result = check_triggers(None, None, 2.5, False, None)
        assert result.premium_triggered

    def test_chicago_dispara(self):
        result = check_triggers(None, None, None, False, 6.0)
        assert result.chicago_triggered

    def test_sem_dados_nao_dispara(self):
        result = check_triggers(None, None, None, False, None)
        assert not result.any_triggered
        assert result.triggered_reasons == []


class TestRunDecisionEngine:
    def test_cenario_neutro(self):
        report = run_decision_engine(make_inputs())
        assert report.score_fisico == pytest.approx(64.8, abs=0.1)
        assert report.classificacao == "neutro"
        assert report.recomendacao_fisica["acao"] == "manter"
        assert report.recomendacao_hedge["acao"] == "aumentar"
        assert report.overrides_ativos == []
        assert not report.modulacao_aplicada

    def test_cenario_oportunidade(self):
        inputs = make_inputs(
            dt=date(2024, 6, 1), chicago_percentile=70.0, **OPPORTUNITY
        )
        report = run_decision_engine(inputs, make_book())
        assert report.score_fisico == pytest.approx(91.3, abs=0.1)
        assert report.classificacao == "muito_forte"
        assert report.recomendacao_fisica["acao"] == "aumentar_forte"
        assert report.recomendacao_fisica["sizing_pct"] == 25.0

    def test_override_armadilha_domina_score(self):
        inputs = make_inputs(var_semanal_lineup=-12.0, percentil_premium=85.0)
        report = run_decision_engine(inputs)
        assert "armadilha_premio" in report.overrides_ativos
        assert report.override_dominante == "armadilha_premio"
        assert report.recomendacao_fisica["acao"] == "reduzir_forte"

    def test_book_no_limite_long_modula_recomendacao(self):
        inputs = make_inputs(**OPPORTUNITY)
        book = make_book(exposicao=80.0, hedge_atual=60.0)
        report = run_decision_engine(inputs, book)
        assert report.modulacao_aplicada
        assert report.recomendacao_fisica["acao"] == "manter"
        assert report.recomendacao_fisica["sizing_pct"] == 0.0

    def test_sizing_efetivo_limitado_pelo_headroom(self):
        inputs = make_inputs(**OPPORTUNITY)
        report = run_decision_engine(inputs, make_book(exposicao=70.0))
        assert report.recomendacao_fisica["sizing_pct"] == 10.0

    def test_json_round_trip(self):
        report = run_decision_engine(make_inputs())
        data = json.loads(report.to_json())
        assert data["data_referencia"] == "2024-05-15"
        assert data["score_fisico"] == 64.8
        assert set(data["componentes"]) == {
            "lineup",
            "premio",
            "competitividade",
            "demanda",
            "cambio",
        }


class TestDecisionEngineClass:
    def test_guarda_ultimo_relatorio(self):
        engine = DecisionEngine()
        assert engine.last_report is None
        report = engine.run(make_inputs())
        assert engine.last_report is report

    def test_update_book(self):
        engine = DecisionEngine()
        new_book = make_book(exposicao=50.0)
        engine.update_book(new_book)
        assert engine.book is new_book
