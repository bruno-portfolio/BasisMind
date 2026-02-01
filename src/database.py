import sqlite3
import logging
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Iterator, Any
from dataclasses import dataclass

from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)


@dataclass
class MarketDataRow:
    date: date
    premium_paranagua: Decimal | None
    chicago_front: Decimal | None
    usd_brl: Decimal | None
    fob_us_gulf: Decimal | None
    lineup_bruto: int | None
    lineup_liquido: int | None
    cancelamentos_7d: int | None
    exports_weekly_tons: Decimal | None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS market_data (
    date DATE PRIMARY KEY,
    premium_paranagua DECIMAL(10,2),
    chicago_front DECIMAL(10,2),
    usd_brl DECIMAL(10,4),
    fob_us_gulf DECIMAL(10,2),
    lineup_bruto INTEGER,
    lineup_liquido INTEGER,
    cancelamentos_7d INTEGER,
    exports_weekly_tons DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_market_data_date ON market_data(date);

CREATE TABLE IF NOT EXISTS data_quality_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    column_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    value_found TEXT,
    expected_range TEXT,
    severity TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_log_date ON data_quality_log(date);
CREATE INDEX IF NOT EXISTS idx_quality_log_type ON data_quality_log(issue_type);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date DATE NOT NULL,
    status TEXT NOT NULL,
    records_processed INTEGER,
    records_failed INTEGER,
    missing_rate DECIMAL(5,4),
    anomalies_detected INTEGER,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP
);

CREATE TRIGGER IF NOT EXISTS update_market_data_timestamp
AFTER UPDATE ON market_data
BEGIN
    UPDATE market_data SET updated_at = CURRENT_TIMESTAMP WHERE date = NEW.date;
END;
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        DB_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        logger.error("Erro de banco de dados: %s", e)
        raise
    finally:
        conn.close()


def init_database() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        logger.info("Banco de dados inicializado: %s", DB_PATH)


def insert_market_data(row: MarketDataRow) -> bool:
    sql = """
    INSERT INTO market_data (
        date, premium_paranagua, chicago_front, usd_brl, fob_us_gulf,
        lineup_bruto, lineup_liquido, cancelamentos_7d, exports_weekly_tons
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(date) DO UPDATE SET
        premium_paranagua = excluded.premium_paranagua,
        chicago_front = excluded.chicago_front,
        usd_brl = excluded.usd_brl,
        fob_us_gulf = excluded.fob_us_gulf,
        lineup_bruto = excluded.lineup_bruto,
        lineup_liquido = excluded.lineup_liquido,
        cancelamentos_7d = excluded.cancelamentos_7d,
        exports_weekly_tons = excluded.exports_weekly_tons
    """
    with get_connection() as conn:
        conn.execute(sql, (
            row.date,
            float(row.premium_paranagua) if row.premium_paranagua else None,
            float(row.chicago_front) if row.chicago_front else None,
            float(row.usd_brl) if row.usd_brl else None,
            float(row.fob_us_gulf) if row.fob_us_gulf else None,
            row.lineup_bruto,
            row.lineup_liquido,
            row.cancelamentos_7d,
            float(row.exports_weekly_tons) if row.exports_weekly_tons else None,
        ))
    return True


def log_quality_issue(
    dt: date,
    column: str,
    issue_type: str,
    value_found: Any,
    expected_range: str,
    severity: str
) -> None:
    sql = """
    INSERT INTO data_quality_log
    (date, column_name, issue_type, value_found, expected_range, severity)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        conn.execute(sql, (dt, column, issue_type, str(value_found), expected_range, severity))


def log_pipeline_run(
    run_date: date,
    status: str,
    records_processed: int,
    records_failed: int,
    missing_rate: float,
    anomalies_detected: int,
    error_message: str | None,
    started_at: str,
    completed_at: str | None
) -> int:
    sql = """
    INSERT INTO pipeline_runs
    (run_date, status, records_processed, records_failed, missing_rate,
     anomalies_detected, error_message, started_at, completed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, (
            run_date, status, records_processed, records_failed,
            missing_rate, anomalies_detected, error_message,
            started_at, completed_at
        ))
        return cursor.lastrowid or 0


def get_historical_data(column: str, days: int = 180) -> list[float]:
    sql = f"""
    SELECT {column} FROM market_data
    WHERE {column} IS NOT NULL
    ORDER BY date DESC LIMIT ?
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (days,)).fetchall()
        return [float(row[0]) for row in rows]


def get_historical_by_regime(
    column: str,
    regime_months: tuple[int, ...],
    years: int = 3,
    before_date: date | None = None
) -> list[float]:
    placeholders = ",".join("?" * len(regime_months))
    ref_date = before_date or date.today()

    sql = f"""
    SELECT {column} FROM market_data
    WHERE {column} IS NOT NULL
      AND CAST(strftime('%m', date) AS INTEGER) IN ({placeholders})
      AND date >= date(?, '-' || ? || ' years')
      AND date < ?
    ORDER BY date DESC
    """
    params = (*regime_months, ref_date.isoformat(), years, ref_date.isoformat())

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [float(row[0]) for row in rows]


def get_lineup_at_date(dt: date) -> dict[str, int | None] | None:
    sql = """
    SELECT lineup_bruto, lineup_liquido, cancelamentos_7d
    FROM market_data WHERE date = ?
    """
    with get_connection() as conn:
        row = conn.execute(sql, (dt.isoformat(),)).fetchone()
        if row is None:
            return None
        return {
            "lineup_bruto": row["lineup_bruto"],
            "lineup_liquido": row["lineup_liquido"],
            "cancelamentos_7d": row["cancelamentos_7d"],
        }


def get_lineup_days_ago(reference_date: date, days: int = 7) -> dict[str, int | None] | None:
    sql = """
    SELECT lineup_bruto, lineup_liquido, cancelamentos_7d
    FROM market_data
    WHERE date = date(?, '-' || ? || ' days')
    """
    with get_connection() as conn:
        row = conn.execute(sql, (reference_date.isoformat(), days)).fetchone()
        if row is None:
            return None
        return {
            "lineup_bruto": row["lineup_bruto"],
            "lineup_liquido": row["lineup_liquido"],
            "cancelamentos_7d": row["cancelamentos_7d"],
        }


def get_value_days_ago(
    column: str,
    reference_date: date,
    days: int
) -> float | None:
    sql = f"""
    SELECT {column} FROM market_data
    WHERE date = date(?, '-' || ? || ' days')
    """
    with get_connection() as conn:
        row = conn.execute(sql, (reference_date.isoformat(), days)).fetchone()
        if row is None or row[0] is None:
            return None
        return float(row[0])


def get_exports_same_week_historical(
    reference_date: date,
    years: int = 5
) -> list[float]:
    week_number = reference_date.isocalendar()[1]
    sql = """
    SELECT exports_weekly_tons FROM market_data
    WHERE CAST(strftime('%W', date) AS INTEGER) = ?
      AND date >= date(?, '-' || ? || ' years')
      AND date < ?
      AND exports_weekly_tons IS NOT NULL
    ORDER BY date DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (
            week_number,
            reference_date.isoformat(),
            years,
            reference_date.isoformat()
        )).fetchall()
        return [float(row[0]) for row in rows]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
