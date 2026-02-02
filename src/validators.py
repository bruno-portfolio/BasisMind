import logging
import statistics
from dataclasses import dataclass
from datetime import date
from typing import Any

from config import (
    ANOMALY_STD_THRESHOLD,
    MARKET_DATA_COLUMNS,
    ColumnSpec,
)
from database import get_historical_data, log_quality_issue

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    issue_type: str | None = None
    message: str | None = None
    severity: str = "warning"


def validate_range(value: Any, spec: ColumnSpec) -> ValidationResult:
    if value is None:
        if not spec.nullable:
            return ValidationResult(
                is_valid=False,
                issue_type="missing",
                message=f"{spec.name} é obrigatório",
                severity="error",
            )
        return ValidationResult(is_valid=True)

    try:
        num_val = float(value)
    except (TypeError, ValueError):
        return ValidationResult(
            is_valid=False,
            issue_type="validation_error",
            message=f"{spec.name}: valor não numérico '{value}'",
            severity="error",
        )

    if spec.min_val is not None and num_val < spec.min_val:
        return ValidationResult(
            is_valid=False,
            issue_type="out_of_range",
            message=f"{spec.name}={num_val} < min={spec.min_val}",
            severity="warning",
        )

    if spec.max_val is not None and num_val > spec.max_val:
        return ValidationResult(
            is_valid=False,
            issue_type="out_of_range",
            message=f"{spec.name}={num_val} > max={spec.max_val}",
            severity="warning",
        )

    return ValidationResult(is_valid=True)


def detect_anomaly(
    column: str, value: float, lookback_days: int = 180
) -> ValidationResult:
    if value is None:
        return ValidationResult(is_valid=True)

    historical = get_historical_data(column, lookback_days)

    if len(historical) < 30:
        logger.debug(
            "Histórico insuficiente para %s (%d registros)", column, len(historical)
        )
        return ValidationResult(is_valid=True)

    try:
        mean = statistics.mean(historical)
        std = statistics.stdev(historical)
    except statistics.StatisticsError:
        return ValidationResult(is_valid=True)

    if std == 0:
        return ValidationResult(is_valid=True)

    z_score = abs(value - mean) / std

    if z_score > ANOMALY_STD_THRESHOLD:
        return ValidationResult(
            is_valid=False,
            issue_type="anomaly",
            message=f"{column}={value:.2f} (z={z_score:.1f}, μ={mean:.2f}, σ={std:.2f})",
            severity="warning",
        )

    return ValidationResult(is_valid=True)


def validate_lineup_consistency(
    lineup_bruto: int | None, lineup_liquido: int | None
) -> ValidationResult:
    if lineup_bruto is None or lineup_liquido is None:
        return ValidationResult(is_valid=True)

    if lineup_liquido > lineup_bruto:
        return ValidationResult(
            is_valid=False,
            issue_type="validation_error",
            message=f"lineup_liquido ({lineup_liquido}) > lineup_bruto ({lineup_bruto})",
            severity="error",
        )

    return ValidationResult(is_valid=True)


def validate_cancellation_rate(
    cancelamentos: int | None, lineup_bruto: int | None
) -> ValidationResult:
    if cancelamentos is None or lineup_bruto is None:
        return ValidationResult(is_valid=True)

    if lineup_bruto == 0:
        if cancelamentos > 0:
            return ValidationResult(
                is_valid=False,
                issue_type="validation_error",
                message="Cancelamentos positivos com lineup_bruto=0",
                severity="error",
            )
        return ValidationResult(is_valid=True)

    rate = cancelamentos / lineup_bruto
    if rate > 1.0:
        return ValidationResult(
            is_valid=False,
            issue_type="out_of_range",
            message=f"Taxa de cancelamento {rate:.1%} > 100%",
            severity="error",
        )

    return ValidationResult(is_valid=True)


def validate_row(
    row_data: dict[str, Any], row_date: date
) -> tuple[bool, list[ValidationResult]]:
    issues: list[ValidationResult] = []
    has_critical = False

    for spec in MARKET_DATA_COLUMNS:
        if spec.name == "date":
            continue
        value = row_data.get(spec.name)
        result = validate_range(value, spec)
        if not result.is_valid:
            issues.append(result)
            log_quality_issue(
                row_date,
                spec.name,
                result.issue_type or "unknown",
                value,
                f"[{spec.min_val}, {spec.max_val}]",
                result.severity,
            )
            if result.severity == "critical":
                has_critical = True

    lineup_result = validate_lineup_consistency(
        row_data.get("lineup_bruto"), row_data.get("lineup_liquido")
    )
    if not lineup_result.is_valid:
        issues.append(lineup_result)
        log_quality_issue(
            row_date,
            "lineup",
            lineup_result.issue_type or "unknown",
            f"bruto={row_data.get('lineup_bruto')}, liq={row_data.get('lineup_liquido')}",
            "liquido <= bruto",
            lineup_result.severity,
        )

    cancel_result = validate_cancellation_rate(
        row_data.get("cancelamentos_7d"), row_data.get("lineup_bruto")
    )
    if not cancel_result.is_valid:
        issues.append(cancel_result)
        log_quality_issue(
            row_date,
            "cancelamentos_7d",
            cancel_result.issue_type or "unknown",
            row_data.get("cancelamentos_7d"),
            "0-100%",
            cancel_result.severity,
        )

    anomaly_columns = ["premium_paranagua", "chicago_front", "usd_brl", "fob_us_gulf"]
    for col in anomaly_columns:
        value = row_data.get(col)
        if value is not None:
            anomaly_result = detect_anomaly(col, float(value))
            if not anomaly_result.is_valid:
                issues.append(anomaly_result)
                log_quality_issue(row_date, col, "anomaly", value, "4σ", "warning")

    return (not has_critical, issues)


def calculate_missing_rate(data: list[dict[str, Any]]) -> float:
    if not data:
        return 1.0

    total_cells = 0
    missing_cells = 0
    check_columns = [spec.name for spec in MARKET_DATA_COLUMNS if spec.name != "date"]

    for row in data:
        for col in check_columns:
            total_cells += 1
            if row.get(col) is None:
                missing_cells += 1

    return missing_cells / total_cells if total_cells > 0 else 0.0
