from basismind.book import BookState, calculate_effective_sizing, modulate_by_book
from basismind.scoring import (
    HedgeRecommendation,
    HedgeResult,
    Intensity,
    PhysicalRecommendation,
    PhysicalResult,
)

AUMENTAR = PhysicalResult(
    recommendation=PhysicalRecommendation.AUMENTAR,
    intensity=Intensity.MODERADA,
    sizing_pct=15.0,
)
REDUZIR = PhysicalResult(
    recommendation=PhysicalRecommendation.REDUZIR,
    intensity=Intensity.MODERADA,
    sizing_pct=-15.0,
)
HEDGE_AUMENTAR = HedgeResult(
    recommendation=HedgeRecommendation.AUMENTAR,
    intensity=Intensity.MODERADA,
    delta_pp=10.0,
)
HEDGE_MANTER = HedgeResult(
    recommendation=HedgeRecommendation.MANTER,
    intensity=Intensity.NEUTRA,
    delta_pp=0.0,
)


def make_book(exposicao=30.0, hedge_atual=45.0):
    return BookState(
        exposicao_fisica_pct=exposicao,
        limite_long_pct=80.0,
        limite_short_pct=-50.0,
        hedge_atual_pct=hedge_atual,
        hedge_meta_pct=60.0,
    )


class TestModulateByBook:
    def test_sem_limites_atingidos_nao_modula(self):
        result = modulate_by_book(AUMENTAR, HEDGE_AUMENTAR, make_book())
        assert result.physical == AUMENTAR
        assert result.hedge == HEDGE_AUMENTAR
        assert not result.physical_was_modulated
        assert not result.hedge_was_modulated
        assert result.modulation_reason is None

    def test_limite_long_bloqueia_aumento(self):
        result = modulate_by_book(AUMENTAR, HEDGE_MANTER, make_book(exposicao=80.0))
        assert result.physical.recommendation == PhysicalRecommendation.MANTER
        assert result.physical.sizing_pct == 0.0
        assert result.physical_was_modulated
        assert "limite long" in result.modulation_reason

    def test_limite_short_bloqueia_reducao(self):
        result = modulate_by_book(REDUZIR, HEDGE_MANTER, make_book(exposicao=-50.0))
        assert result.physical.recommendation == PhysicalRecommendation.MANTER
        assert result.physical_was_modulated

    def test_limite_long_nao_bloqueia_reducao(self):
        result = modulate_by_book(REDUZIR, HEDGE_MANTER, make_book(exposicao=80.0))
        assert result.physical == REDUZIR
        assert not result.physical_was_modulated

    def test_overhedge_bloqueia_aumento_de_hedge(self):
        result = modulate_by_book(AUMENTAR, HEDGE_AUMENTAR, make_book(hedge_atual=85.0))
        assert result.hedge.recommendation == HedgeRecommendation.MANTER
        assert result.hedge_was_modulated

    def test_hedge_dentro_da_tolerancia_nao_modula(self):
        result = modulate_by_book(AUMENTAR, HEDGE_AUMENTAR, make_book(hedge_atual=75.0))
        assert result.hedge == HEDGE_AUMENTAR


class TestEffectiveSizing:
    def test_sizing_positivo_limitado_pelo_headroom_long(self):
        book = make_book(exposicao=70.0)
        assert calculate_effective_sizing(15.0, book) == 10.0

    def test_sizing_positivo_com_headroom_suficiente(self):
        book = make_book(exposicao=30.0)
        assert calculate_effective_sizing(15.0, book) == 15.0

    def test_sizing_negativo_limitado_pelo_headroom_short(self):
        book = make_book(exposicao=-45.0)
        assert calculate_effective_sizing(-20.0, book) == -5.0

    def test_sizing_zero(self):
        assert calculate_effective_sizing(0.0, make_book()) == 0.0
