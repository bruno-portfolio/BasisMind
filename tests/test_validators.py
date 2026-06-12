from datetime import date

import pytest

import basismind.validators as validators
from basismind.config import ColumnSpec
from basismind.validators import (
    calculate_missing_rate,
    detect_anomaly,
    validate_cancellation_rate,
    validate_lineup_consistency,
    validate_range,
    validate_row,
)

NUMERIC_SPEC = ColumnSpec("usd_brl", "DECIMAL", min_val=3.0, max_val=10.0)
REQUIRED_SPEC = ColumnSpec("date", "DATE", nullable=False)

VALID_ROW = {
    "premium_paranagua": 100.0,
    "chicago_front": 1200.0,
    "usd_brl": 5.2,
    "fob_us_gulf": 450.0,
    "lineup_bruto": 80,
    "lineup_liquido": 70,
    "cancelamentos_7d": 5,
    "exports_weekly_tons": 2_500_000.0,
}


@pytest.fixture(autouse=True)
def sem_banco(monkeypatch):
    monkeypatch.setattr(validators, "log_quality_issue", lambda *args: None)
    monkeypatch.setattr(validators, "get_historical_data", lambda *args: [])


class TestValidateRange:
    def test_none_em_coluna_opcional_passa(self):
        assert validate_range(None, NUMERIC_SPEC).is_valid

    def test_none_em_coluna_obrigatoria_falha(self):
        result = validate_range(None, REQUIRED_SPEC)
        assert not result.is_valid
        assert result.severity == "error"

    def test_valor_nao_numerico_falha(self):
        result = validate_range("abc", NUMERIC_SPEC)
        assert not result.is_valid
        assert result.severity == "error"

    def test_abaixo_do_minimo_falha_com_error(self):
        result = validate_range(2.0, NUMERIC_SPEC)
        assert not result.is_valid
        assert result.issue_type == "out_of_range"
        assert result.severity == "error"

    def test_acima_do_maximo_falha_com_error(self):
        result = validate_range(15.0, NUMERIC_SPEC)
        assert not result.is_valid
        assert result.severity == "error"

    def test_dentro_do_range_passa(self):
        assert validate_range(5.2, NUMERIC_SPEC).is_valid


class TestLineupConsistency:
    def test_liquido_maior_que_bruto_falha(self):
        result = validate_lineup_consistency(80, 90)
        assert not result.is_valid
        assert result.severity == "error"

    def test_liquido_menor_que_bruto_passa(self):
        assert validate_lineup_consistency(80, 70).is_valid

    def test_valores_ausentes_passam(self):
        assert validate_lineup_consistency(None, 70).is_valid


class TestCancellationRate:
    def test_cancelamentos_com_lineup_zero_falha(self):
        result = validate_cancellation_rate(5, 0)
        assert not result.is_valid

    def test_taxa_acima_de_cem_por_cento_falha(self):
        result = validate_cancellation_rate(120, 80)
        assert not result.is_valid

    def test_taxa_normal_passa(self):
        assert validate_cancellation_rate(5, 80).is_valid


class TestDetectAnomaly:
    def test_historico_curto_nao_acusa(self, monkeypatch):
        monkeypatch.setattr(
            validators, "get_historical_data", lambda *args: [100.0] * 10
        )
        assert detect_anomaly("premium_paranagua", 500.0).is_valid

    def test_valor_dentro_do_padrao_passa(self, monkeypatch):
        historical = [99.0, 101.0] * 20
        monkeypatch.setattr(validators, "get_historical_data", lambda *args: historical)
        assert detect_anomaly("premium_paranagua", 100.5).is_valid

    def test_desvio_extremo_acusa_anomalia(self, monkeypatch):
        historical = [99.0, 101.0] * 20
        monkeypatch.setattr(validators, "get_historical_data", lambda *args: historical)
        result = detect_anomaly("premium_paranagua", 150.0)
        assert not result.is_valid
        assert result.issue_type == "anomaly"
        assert result.severity == "warning"


class TestValidateRow:
    def test_linha_valida_passa(self):
        is_valid, issues = validate_row(dict(VALID_ROW), date(2024, 5, 15))
        assert is_valid
        assert issues == []

    def test_campo_ausente_nao_bloqueia(self):
        row = dict(VALID_ROW, premium_paranagua=None)
        is_valid, issues = validate_row(row, date(2024, 5, 15))
        assert is_valid

    def test_valor_fora_do_range_bloqueia(self):
        row = dict(VALID_ROW, fob_us_gulf=999.0)
        is_valid, issues = validate_row(row, date(2024, 5, 15))
        assert not is_valid
        assert any(i.issue_type == "out_of_range" for i in issues)

    def test_lineup_inconsistente_bloqueia(self):
        row = dict(VALID_ROW, lineup_liquido=120)
        is_valid, issues = validate_row(row, date(2024, 5, 15))
        assert not is_valid

    def test_anomalia_gera_warning_mas_nao_bloqueia(self, monkeypatch):
        historical = [99.0, 101.0] * 20
        monkeypatch.setattr(validators, "get_historical_data", lambda *args: historical)
        row = dict(VALID_ROW, premium_paranagua=200.0)
        is_valid, issues = validate_row(row, date(2024, 5, 15))
        assert is_valid
        assert any(i.issue_type == "anomaly" for i in issues)


class TestMissingRate:
    def test_sem_dados_retorna_um(self):
        assert calculate_missing_rate([]) == 1.0

    def test_linha_completa_retorna_zero(self):
        assert calculate_missing_rate([dict(VALID_ROW)]) == 0.0

    def test_metade_ausente(self):
        row = dict(
            VALID_ROW,
            premium_paranagua=None,
            chicago_front=None,
            usd_brl=None,
            fob_us_gulf=None,
        )
        assert calculate_missing_rate([row]) == 0.5
