from pathlib import Path
from dataclasses import dataclass
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).parent.parent
DATA_DIR: Final[Path] = ROOT_DIR / "data"
LOGS_DIR: Final[Path] = ROOT_DIR / "logs"
DB_PATH: Final[Path] = DATA_DIR / "motor_decisao.db"

ANOMALY_STD_THRESHOLD: Final[float] = 4.0
MAX_MISSING_RATE: Final[float] = 0.05
MIN_OI_FRONT_MONTH: Final[int] = 10_000
ROLL_DAYS_BEFORE_EXPIRY: Final[int] = 45

LINEUP_WINDOW_WEEKS: Final[tuple[int, int]] = (2, 6)
CANCELLATION_LOOKBACK_DAYS: Final[int] = 7
POSTPONE_THRESHOLD_DAYS: Final[int] = 14

SAFRA_MONTHS: Final[tuple[int, ...]] = (3, 4, 5, 6, 7)
ENTRESSAFRA_MONTHS: Final[tuple[int, ...]] = (1, 2, 8, 9, 10, 11, 12)

PREMIUM_LOOKBACK_YEARS: Final[int] = 3
MIN_HISTORICAL_SAMPLES: Final[int] = 30

PREMIUM_THRESHOLD_MUITO_BAIXO: Final[float] = 20.0
PREMIUM_THRESHOLD_BAIXO: Final[float] = 40.0
PREMIUM_THRESHOLD_NEUTRO: Final[float] = 60.0
PREMIUM_THRESHOLD_ALTO: Final[float] = 80.0

LINEUP_LOOKBACK_DAYS: Final[int] = 7
LINEUP_DROP_OVERRIDE_THRESHOLD: Final[float] = -10.0

LINEUP_TREND_FORTE_QUEDA: Final[float] = -15.0
LINEUP_TREND_QUEDA: Final[float] = -5.0
LINEUP_TREND_ALTA: Final[float] = 5.0
LINEUP_TREND_FORTE_ALTA: Final[float] = 15.0

FREIGHT_ABNORMAL_STD: Final[float] = 2.0
CRITICAL_SPREAD_THRESHOLD: Final[float] = 15.0

COMPETITIVENESS_MUITO_BARATO: Final[float] = -20.0
COMPETITIVENESS_BARATO: Final[float] = -10.0
COMPETITIVENESS_CARO: Final[float] = 10.0
COMPETITIVENESS_MUITO_CARO: Final[float] = 20.0

CAMBIO_VAR_LOOKBACK_SHORT: Final[int] = 5
CAMBIO_VAR_LOOKBACK_LONG: Final[int] = 20
CAMBIO_FORTE_THRESHOLD: Final[float] = 3.0

DEMAND_LOOKBACK_YEARS: Final[int] = 5
DEMAND_Z_FORTE: Final[float] = 1.5

LOGISTICS_WAIT_THRESHOLD_DAYS: Final[int] = 15
LOGISTICS_WAIT_CONSECUTIVE_WEEKS: Final[int] = 2
LOGISTICS_LOADING_RATE_MIN: Final[float] = 0.70

CHICAGO_LOOKBACK_DAYS: Final[int] = 180
CHICAGO_SPECULATIVE_SPIKE: Final[float] = 5.0

SCORING_WEIGHT_LINEUP: Final[float] = 0.30
SCORING_WEIGHT_PREMIUM: Final[float] = 0.25
SCORING_WEIGHT_COMPETITIVENESS: Final[float] = 0.20
SCORING_WEIGHT_DEMAND: Final[float] = 0.15
SCORING_WEIGHT_CAMBIO: Final[float] = 0.10

SCORING_FISICO_MUITO_FORTE: Final[float] = 80.0
SCORING_FISICO_FORTE: Final[float] = 65.0
SCORING_FISICO_FRACO: Final[float] = 35.0
SCORING_FISICO_MUITO_FRACO: Final[float] = 20.0

HEDGE_PERCENTIL_MUITO_ALTO: Final[float] = 80.0
HEDGE_PERCENTIL_ALTO: Final[float] = 65.0
HEDGE_PERCENTIL_BAIXO: Final[float] = 35.0
HEDGE_PERCENTIL_MUITO_BAIXO: Final[float] = 20.0

BOOK_HEDGE_TOLERANCE_PP: Final[float] = 20.0

TRIGGER_LINEUP_CHANGE_PCT: Final[float] = 20.0
TRIGGER_PREMIUM_STD: Final[float] = 2.0
TRIGGER_PREMIUM_DAYS: Final[int] = 3
TRIGGER_CHICAGO_CHANGE_PCT: Final[float] = 5.0

DEFAULT_LIMITE_LONG_PCT: Final[float] = 80.0
DEFAULT_LIMITE_SHORT_PCT: Final[float] = -50.0
DEFAULT_HEDGE_META_PCT: Final[float] = 60.0

OVERRIDE_QUEDA_LINEUP_THRESHOLD: Final[float] = -10.0
OVERRIDE_QUEDA_PREMIUM_PERCENTILE: Final[float] = 40.0
OVERRIDE_ARMADILHA_LINEUP_THRESHOLD: Final[float] = -10.0
OVERRIDE_ARMADILHA_PREMIUM_PERCENTILE: Final[float] = 80.0
OVERRIDE_COMPETITIVIDADE_SPREAD: Final[float] = 15.0

VALID_RANGES: Final[dict[str, tuple[float, float]]] = {
    "premium_paranagua": (-200, 500),
    "chicago_front": (500, 2500),
    "usd_brl": (3.0, 10.0),
    "fob_us_gulf": (200, 800),
    "exports_weekly_tons": (0, 10_000_000),
}


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str
    min_val: float | None = None
    max_val: float | None = None
    nullable: bool = False


MARKET_DATA_COLUMNS: Final[tuple[ColumnSpec, ...]] = (
    ColumnSpec("date", "DATE", nullable=False),
    ColumnSpec("premium_paranagua", "DECIMAL", min_val=-200, max_val=500),
    ColumnSpec("chicago_front", "DECIMAL", min_val=500, max_val=2500),
    ColumnSpec("usd_brl", "DECIMAL", min_val=3.0, max_val=10.0),
    ColumnSpec("fob_us_gulf", "DECIMAL", min_val=500, max_val=2500),
    ColumnSpec("lineup_bruto", "INTEGER", min_val=0, max_val=500),
    ColumnSpec("lineup_liquido", "INTEGER", min_val=0, max_val=500),
    ColumnSpec("cancelamentos_7d", "INTEGER", min_val=0, max_val=100),
    ColumnSpec("exports_weekly_tons", "DECIMAL", min_val=0, max_val=10_000_000),
)
