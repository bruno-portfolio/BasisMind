from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from config import (
    BOOK_HEDGE_TOLERANCE_PP,
)
from scoring import (
    PhysicalRecommendation,
    HedgeRecommendation,
    Intensity,
    PhysicalResult,
    HedgeResult,
)


@dataclass(frozen=True)
class BookState:
    exposicao_fisica_pct: float
    limite_long_pct: float
    limite_short_pct: float
    hedge_atual_pct: float
    hedge_meta_pct: float

    @property
    def exposicao_disponivel_long(self) -> float:
        return max(0, self.limite_long_pct - self.exposicao_fisica_pct)

    @property
    def exposicao_disponivel_short(self) -> float:
        return max(0, self.exposicao_fisica_pct - self.limite_short_pct)

    @property
    def hedge_vs_meta(self) -> float:
        return self.hedge_atual_pct - self.hedge_meta_pct

    @property
    def is_at_long_limit(self) -> bool:
        return self.exposicao_fisica_pct >= self.limite_long_pct

    @property
    def is_at_short_limit(self) -> bool:
        return self.exposicao_fisica_pct <= self.limite_short_pct

    @property
    def is_overhedged(self) -> bool:
        return self.hedge_atual_pct >= (self.hedge_meta_pct + BOOK_HEDGE_TOLERANCE_PP)


@dataclass(frozen=True)
class ModulatedResult:
    physical: PhysicalResult
    hedge: HedgeResult
    physical_was_modulated: bool
    hedge_was_modulated: bool
    modulation_reason: str | None


def modulate_by_book(
    physical: PhysicalResult,
    hedge: HedgeResult,
    book: BookState,
) -> ModulatedResult:
    new_physical = physical
    new_hedge = hedge
    physical_modulated = False
    hedge_modulated = False
    reasons: list[str] = []

    if physical.recommendation in (
        PhysicalRecommendation.AUMENTAR,
        PhysicalRecommendation.AUMENTAR_FORTE,
    ):
        if book.is_at_long_limit:
            new_physical = PhysicalResult(
                recommendation=PhysicalRecommendation.MANTER,
                intensity=Intensity.NEUTRA,
                sizing_pct=0.0,
            )
            physical_modulated = True
            reasons.append(f"Exposicao no limite long ({book.limite_long_pct}%)")

    if physical.recommendation in (
        PhysicalRecommendation.REDUZIR,
        PhysicalRecommendation.REDUZIR_FORTE,
    ):
        if book.is_at_short_limit:
            new_physical = PhysicalResult(
                recommendation=PhysicalRecommendation.MANTER,
                intensity=Intensity.NEUTRA,
                sizing_pct=0.0,
            )
            physical_modulated = True
            reasons.append(f"Exposicao no limite short ({book.limite_short_pct}%)")

    if hedge.recommendation in (
        HedgeRecommendation.AUMENTAR,
        HedgeRecommendation.AUMENTAR_FORTE,
    ):
        if book.is_overhedged:
            new_hedge = HedgeResult(
                recommendation=HedgeRecommendation.MANTER,
                intensity=Intensity.NEUTRA,
                delta_pp=0.0,
            )
            hedge_modulated = True
            reasons.append(
                f"Hedge acima da meta + tolerancia "
                f"({book.hedge_atual_pct}% vs meta {book.hedge_meta_pct}%)"
            )

    return ModulatedResult(
        physical=new_physical,
        hedge=new_hedge,
        physical_was_modulated=physical_modulated,
        hedge_was_modulated=hedge_modulated,
        modulation_reason=" | ".join(reasons) if reasons else None,
    )


def calculate_effective_sizing(
    sizing_pct: float,
    book: BookState,
) -> float:
    if sizing_pct > 0:
        return min(sizing_pct, book.exposicao_disponivel_long)
    elif sizing_pct < 0:
        return max(sizing_pct, -book.exposicao_disponivel_short)
    return 0.0
