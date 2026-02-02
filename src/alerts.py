import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from config import LOGS_DIR

LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class Alert:
    level: str
    source: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class AlertHandler(ABC):
    @abstractmethod
    def send(self, alert: Alert) -> bool:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class LogFileHandler(AlertHandler):
    def __init__(self, log_file: Path | None = None) -> None:
        self._log_file = log_file or (LOGS_DIR / "alerts.log")

    def send(self, alert: Alert) -> bool:
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                ts = alert.timestamp.strftime(DATE_FORMAT) if alert.timestamp else ""
                line = (
                    f"{ts} | {alert.level.upper():8} | {alert.source} | {alert.message}"
                )
                if alert.details:
                    line += f" | {alert.details}"
                f.write(line + "\n")
            return True
        except OSError as e:
            logging.error("Erro ao escrever log: %s", e)
            return False

    def name(self) -> str:
        return f"file:{self._log_file}"


class ConsoleHandler(AlertHandler):
    def send(self, alert: Alert) -> bool:
        level_colors = {
            "info": "\033[94m",
            "warning": "\033[93m",
            "error": "\033[91m",
            "critical": "\033[95m",
        }
        reset = "\033[0m"
        color = level_colors.get(alert.level, "")
        ts = alert.timestamp.strftime(DATE_FORMAT) if alert.timestamp else ""
        print(f"{color}[{ts}] {alert.level.upper()}: {alert.message}{reset}")
        return True

    def name(self) -> str:
        return "console"


class EmailHandler(AlertHandler):
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        recipients: list[str],
        min_level: str = "critical",
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._username = username
        self._password = password
        self._recipients = recipients
        self._min_level = min_level
        self._level_priority = {"info": 0, "warning": 1, "error": 2, "critical": 3}

    def _should_send(self, alert: Alert) -> bool:
        alert_priority = self._level_priority.get(alert.level, 0)
        min_priority = self._level_priority.get(self._min_level, 0)
        return alert_priority >= min_priority

    def send(self, alert: Alert) -> bool:
        if not self._should_send(alert):
            return True

        try:
            msg = MIMEText(
                f"""
Motor de Decisão - Alerta {alert.level.upper()}

Fonte: {alert.source}
Mensagem: {alert.message}
Timestamp: {alert.timestamp}

Detalhes:
{alert.details}
            """
            )
            msg["Subject"] = f"[Motor Decisão] {alert.level.upper()}: {alert.source}"
            msg["From"] = self._username
            msg["To"] = ", ".join(self._recipients)

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.send_message(msg)
            return True
        except smtplib.SMTPException as e:
            logging.error("Erro ao enviar email: %s", e)
            return False

    def name(self) -> str:
        return f"email:{','.join(self._recipients)}"


class AlertManager:
    def __init__(self) -> None:
        self._handlers: list[AlertHandler] = []
        self._logger = logging.getLogger("AlertManager")

    def add_handler(self, handler: AlertHandler) -> None:
        self._handlers.append(handler)
        self._logger.info("Handler adicionado: %s", handler.name())

    def send(self, alert: Alert) -> bool:
        if not self._handlers:
            self._logger.warning("Nenhum handler configurado")
            return False

        success = True
        for handler in self._handlers:
            try:
                if not handler.send(alert):
                    success = False
                    self._logger.warning("Falha em handler: %s", handler.name())
            except Exception as e:
                success = False
                self._logger.error("Erro em handler %s: %s", handler.name(), e)

        return success

    def info(
        self, source: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.send(Alert("info", source, message, details))

    def warning(
        self, source: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.send(Alert("warning", source, message, details))

    def error(
        self, source: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.send(Alert("error", source, message, details))

    def critical(
        self, source: str, message: str, details: dict[str, Any] | None = None
    ) -> None:
        self.send(Alert("critical", source, message, details))


def setup_logging(
    level: int = logging.INFO, log_file: Path | None = None
) -> logging.Logger:
    log_file = log_file or (LOGS_DIR / "motor_decisao.log")

    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers,
    )

    return logging.getLogger("MotorDecisao")


def create_default_alert_manager() -> AlertManager:
    manager = AlertManager()
    manager.add_handler(ConsoleHandler())
    manager.add_handler(LogFileHandler())
    return manager


_alert_manager: AlertManager | None = None


def get_alert_manager() -> AlertManager:
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = create_default_alert_manager()
    return _alert_manager
