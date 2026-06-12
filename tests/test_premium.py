from datetime import date

import pytest

from basismind.premium import (
    PremiumClassification,
    calculate_percentile,
    classify_premium,
    get_regime,
    normalize_premium,
)


class TestGetRegime:
    @pytest.mark.parametrize("month", [3, 4, 5, 6, 7])
    def test_meses_de_safra(self, month):
        assert get_regime(date(2024, month, 15)) == "safra"

    @pytest.mark.parametrize("month", [1, 2, 8, 9, 10, 11, 12])
    def test_meses_de_entressafra(self, month):
        assert get_regime(date(2024, month, 15)) == "entressafra"


class TestCalculatePercentile:
    def test_historico_vazio_lanca_erro(self):
        with pytest.raises(ValueError):
            calculate_percentile(50.0, [])

    def test_valor_mediano(self):
        historical = [float(x) for x in range(1, 100)]
        assert calculate_percentile(50.0, historical) == pytest.approx(50.0, abs=1.0)

    def test_valor_acima_de_todos(self):
        assert calculate_percentile(200.0, [10.0, 20.0, 30.0]) == 100.0

    def test_valor_abaixo_de_todos(self):
        assert calculate_percentile(5.0, [10.0, 20.0, 30.0]) == 0.0

    def test_empates_contam_metade(self):
        assert calculate_percentile(5.0, [5.0, 5.0, 5.0, 5.0]) == 50.0


class TestClassifyPremium:
    @pytest.mark.parametrize(
        "percentile,expected",
        [
            (10.0, PremiumClassification.MUITO_BAIXO),
            (20.0, PremiumClassification.BAIXO),
            (45.0, PremiumClassification.NEUTRO),
            (75.0, PremiumClassification.ALTO),
            (85.0, PremiumClassification.MUITO_ALTO),
            (100.0, PremiumClassification.MUITO_ALTO),
        ],
    )
    def test_limites_de_classificacao(self, percentile, expected):
        assert classify_premium(percentile) == expected


class TestNormalizePremium:
    def test_premio_acima_do_historico(self):
        historical = [float(x) for x in range(50, 110, 2)]
        result = normalize_premium(date(2024, 5, 15), 150.0, historical)
        assert result.regime == "safra"
        assert result.percentile == 100.0
        assert result.classification == PremiumClassification.MUITO_ALTO
        assert result.historical_count == len(historical)
