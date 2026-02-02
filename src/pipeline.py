import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from config import MAX_MISSING_RATE
from database import (
    MarketDataRow,
    init_database,
    insert_market_data,
    log_pipeline_run,
)
from validators import validate_row, calculate_missing_rate

logger = logging.getLogger(__name__)


class DataSourceError(Exception):
    pass


@dataclass
class PipelineResult:
    status: str
    records_processed: int
    records_failed: int
    missing_rate: float
    anomalies_detected: int
    errors: list[str]


class DataSource(ABC):
    @abstractmethod
    def fetch(self, target_date: date) -> dict[str, Any]:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class ManualDataSource(DataSource):
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def fetch(self, target_date: date) -> dict[str, Any]:
        return self._data

    def name(self) -> str:
        return "manual"


class CSVDataSource(DataSource):
    def __init__(self, filepath: str) -> None:
        self._filepath = filepath
        self._cache: dict[date, dict[str, Any]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        import csv

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
                    self._cache[row_date] = self._parse_row(row)
        except FileNotFoundError:
            logger.warning("CSV não encontrado: %s", self._filepath)
        except KeyError as e:
            raise DataSourceError(f"Coluna obrigatória ausente no CSV: {e}") from e

    def _parse_row(self, row: dict[str, str]) -> dict[str, Any]:
        def to_decimal(val: str) -> Decimal | None:
            return Decimal(val) if val.strip() else None

        def to_int(val: str) -> int | None:
            return int(val) if val.strip() else None

        return {
            "premium_paranagua": to_decimal(row.get("premium_paranagua", "")),
            "chicago_front": to_decimal(row.get("chicago_front", "")),
            "usd_brl": to_decimal(row.get("usd_brl", "")),
            "fob_us_gulf": to_decimal(row.get("fob_us_gulf", "")),
            "lineup_bruto": to_int(row.get("lineup_bruto", "")),
            "lineup_liquido": to_int(row.get("lineup_liquido", "")),
            "cancelamentos_7d": to_int(row.get("cancelamentos_7d", "")),
            "exports_weekly_tons": to_decimal(row.get("exports_weekly_tons", "")),
        }

    def fetch(self, target_date: date) -> dict[str, Any]:
        if target_date not in self._cache:
            raise DataSourceError(f"Data {target_date} não encontrada no CSV")
        return self._cache[target_date]

    def name(self) -> str:
        return f"csv:{self._filepath}"


class DataPipeline:
    def __init__(self, sources: list[DataSource]) -> None:
        if not sources:
            raise ValueError("Pelo menos uma fonte de dados é necessária")
        self._sources = sources

    def _try_fetch(self, target_date: date) -> tuple[dict[str, Any] | None, str | None]:
        for source in self._sources:
            try:
                data = source.fetch(target_date)
                logger.debug("Dados obtidos de %s para %s", source.name(), target_date)
                return data, None
            except DataSourceError as e:
                logger.warning("Falha em %s: %s", source.name(), e)
                continue
        return None, "Todas as fontes falharam"

    def run(self, target_date: date) -> PipelineResult:
        started_at = datetime.now().isoformat()
        errors: list[str] = []
        anomalies = 0

        data, fetch_error = self._try_fetch(target_date)
        if fetch_error:
            errors.append(fetch_error)
            result = PipelineResult(
                status="failed",
                records_processed=0,
                records_failed=1,
                missing_rate=1.0,
                anomalies_detected=0,
                errors=errors,
            )
            log_pipeline_run(
                target_date,
                "failed",
                0,
                1,
                1.0,
                0,
                fetch_error,
                started_at,
                datetime.now().isoformat(),
            )
            return result

        is_valid, issues = validate_row(data, target_date)
        anomalies = sum(1 for i in issues if i.issue_type == "anomaly")

        for issue in issues:
            if issue.message:
                msg = f"[{issue.severity}] {issue.message}"
                errors.append(msg)
                logger.warning(msg)

        missing_rate = calculate_missing_rate([data])
        if missing_rate > MAX_MISSING_RATE:
            logger.warning(
                "Missing rate %.1f%% > threshold %.1f%%",
                missing_rate * 100,
                MAX_MISSING_RATE * 100,
            )

        if is_valid:
            assert data is not None
            row = MarketDataRow(
                date=target_date,
                premium_paranagua=data.get("premium_paranagua"),
                chicago_front=data.get("chicago_front"),
                usd_brl=data.get("usd_brl"),
                fob_us_gulf=data.get("fob_us_gulf"),
                lineup_bruto=data.get("lineup_bruto"),
                lineup_liquido=data.get("lineup_liquido"),
                cancelamentos_7d=data.get("cancelamentos_7d"),
                exports_weekly_tons=data.get("exports_weekly_tons"),
            )
            insert_market_data(row)
            status = "success" if not errors else "partial"
            records_failed = 0
        else:
            status = "failed"
            records_failed = 1

        result = PipelineResult(
            status=status,
            records_processed=1,
            records_failed=records_failed,
            missing_rate=missing_rate,
            anomalies_detected=anomalies,
            errors=errors,
        )

        log_pipeline_run(
            target_date,
            status,
            1,
            records_failed,
            missing_rate,
            anomalies,
            "; ".join(errors) if errors else None,
            started_at,
            datetime.now().isoformat(),
        )

        return result

    def run_batch(self, dates: list[date]) -> list[PipelineResult]:
        results = []
        for d in dates:
            result = self.run(d)
            results.append(result)
            logger.info("Pipeline %s: %s", d, result.status)
        return results


def run_daily_pipeline(sources: list[DataSource] | None = None) -> PipelineResult:
    init_database()

    if sources is None:
        logger.error("Nenhuma fonte de dados configurada")
        return PipelineResult(
            status="failed",
            records_processed=0,
            records_failed=0,
            missing_rate=1.0,
            anomalies_detected=0,
            errors=["Nenhuma fonte de dados configurada"],
        )

    pipeline = DataPipeline(sources)
    return pipeline.run(date.today())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    init_database()
    logger.info("Pipeline inicializado. Configure fontes de dados para execução.")
