import logging
from datetime import date
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LineupTrend(Enum):
    FORTE_QUEDA = "forte_queda"
    QUEDA = "queda"
    ESTAVEL = "estavel"
    ALTA = "alta"
    FORTE_ALTA = "forte_alta"


@dataclass(frozen=True)
class LineupMetrics:
    date: date
    lineup_bruto: int
    lineup_liquido: int
    cancelamentos_7d: int
    taxa_cancelamento: float
    var_semanal: float | None
    trend: LineupTrend | None
    is_valid: bool
    validation_errors: tuple[str, ...]


TREND_THRESHOLDS: dict[LineupTrend, tuple[float, float]] = {
    LineupTrend.FORTE_QUEDA: (float("-inf"), -15),
    LineupTrend.QUEDA: (-15, -5),
    LineupTrend.ESTAVEL: (-5, 5),
    LineupTrend.ALTA: (5, 15),
    LineupTrend.FORTE_ALTA: (15, float("inf")),
}

LINEUP_DROP_OVERRIDE_THRESHOLD: float = -10.0


def calculate_lineup_liquido(
    lineup_bruto: int,
    cancelados: int,
    adiados_14d: int
) -> int:
    return max(0, lineup_bruto - cancelados - adiados_14d)


def calculate_taxa_cancelamento(
    cancelados_7d: int,
    adiados_14d_7d: int,
    lineup_bruto_7d_atras: int
) -> float:
    if lineup_bruto_7d_atras <= 0:
        return 0.0
    taxa = (cancelados_7d + adiados_14d_7d) / lineup_bruto_7d_atras * 100
    return round(min(100.0, max(0.0, taxa)), 2)


def calculate_var_semanal(
    lineup_liquido_atual: int,
    lineup_liquido_7d_atras: int | None
) -> float | None:
    if lineup_liquido_7d_atras is None or lineup_liquido_7d_atras <= 0:
        return None
    var = (lineup_liquido_atual - lineup_liquido_7d_atras) / lineup_liquido_7d_atras * 100
    return round(var, 2)


def classify_trend(var_semanal: float | None) -> LineupTrend | None:
    if var_semanal is None:
        return None
    for trend, (lower, upper) in TREND_THRESHOLDS.items():
        if lower <= var_semanal < upper:
            return trend
    return LineupTrend.FORTE_ALTA


def validate_lineup(lineup_bruto: int, lineup_liquido: int) -> list[str]:
    errors = []
    if lineup_liquido > lineup_bruto:
        errors.append(f"lineup_liquido ({lineup_liquido}) > lineup_bruto ({lineup_bruto})")
    if lineup_bruto < 0:
        errors.append(f"lineup_bruto negativo: {lineup_bruto}")
    if lineup_liquido < 0:
        errors.append(f"lineup_liquido negativo: {lineup_liquido}")
    return errors


def compute_lineup_metrics(
    dt: date,
    lineup_bruto: int,
    lineup_liquido: int,
    cancelamentos_7d: int,
    lineup_bruto_7d_atras: int | None = None,
    lineup_liquido_7d_atras: int | None = None,
    adiados_14d_7d: int = 0
) -> LineupMetrics:
    validation_errors = validate_lineup(lineup_bruto, lineup_liquido)

    taxa_cancelamento = 0.0
    if lineup_bruto_7d_atras is not None:
        taxa_cancelamento = calculate_taxa_cancelamento(
            cancelamentos_7d, adiados_14d_7d, lineup_bruto_7d_atras
        )
        if not (0 <= taxa_cancelamento <= 100):
            validation_errors.append(f"taxa_cancelamento fora de range: {taxa_cancelamento}")

    var_semanal = calculate_var_semanal(lineup_liquido, lineup_liquido_7d_atras)
    trend = classify_trend(var_semanal)

    return LineupMetrics(
        date=dt,
        lineup_bruto=lineup_bruto,
        lineup_liquido=lineup_liquido,
        cancelamentos_7d=cancelamentos_7d,
        taxa_cancelamento=taxa_cancelamento,
        var_semanal=var_semanal,
        trend=trend,
        is_valid=len(validation_errors) == 0,
        validation_errors=tuple(validation_errors)
    )


def is_lineup_dropping(var_semanal: float | None) -> bool:
    if var_semanal is None:
        return False
    return var_semanal < LINEUP_DROP_OVERRIDE_THRESHOLD
