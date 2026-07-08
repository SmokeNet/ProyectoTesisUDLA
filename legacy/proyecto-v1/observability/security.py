"""Deteccion defensiva de patrones HTTP para escenarios controlados.

No intenta sustituir un WAF. Correlaciona metadatos de solicitudes, limita el
impacto localmente y produce decisiones explicables y auditables.
"""

from __future__ import annotations

import re
import threading
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import ClassVar, Iterable
from urllib.parse import unquote_plus
from pathlib import Path

from .domain import Severity


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class HttpAccessEvent:
    source_ip: str
    method: str
    path: str
    user_agent: str = ""
    body_sample: str = ""
    status_code: int | None = None
    occurred_at: datetime = field(default_factory=utc_now)

    SENSITIVE: ClassVar[re.Pattern[str]] = re.compile(
        r"(?i)(password|passwd|clave|token|api[_-]?key|authorization)(=|%3[dD])([^&\s]{1,512})"
    )

    @classmethod
    def _redact(cls, value: str, limit: int) -> str:
        return cls.SENSITIVE.sub(r"\1\2[REDACTED]", value[:limit])

    def safe_dict(self) -> dict[str, object]:
        """Devuelve telemetria acotada; nunca persiste credenciales completas."""
        return {
            "source_ip": self.source_ip,
            "method": self.method[:10].upper(),
            "path": self._redact(self.path, 1000),
            "user_agent": self.user_agent[:500],
            "body_sample": self._redact(self.body_sample, 512),
            "status_code": self.status_code,
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class SecurityDetection:
    rule_id: str
    incident_type: str
    severity: Severity
    cause: str
    diagnosis: str
    response: str


@dataclass(frozen=True, slots=True)
class SecurityPolicy:
    flood_requests: int = 30
    flood_window_seconds: int = 10
    brute_force_attempts: int = 5
    brute_force_window_seconds: int = 60
    scan_unique_paths: int = 7
    scan_window_seconds: int = 30
    temporary_block_seconds: int = 60

    @classmethod
    def from_file(cls, path: str | Path) -> "SecurityPolicy":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        thresholds = data.get("thresholds", {})
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        values = {key: int(value) for key, value in thresholds.items() if key in allowed}
        return cls(**values)


class SecurityWatcher:
    """Motor correlacional thread-safe con ventanas deslizantes por origen."""

    SQLI = re.compile(
        r"(?:\bunion\s+(?:all\s+)?select\b|\bor\s+['\"]?1['\"]?\s*=\s*['\"]?1|"
        r"\bdrop\s+table\b|--\s|/\*|\bsleep\s*\()",
        re.IGNORECASE,
    )
    XSS = re.compile(
        r"(?:<\s*script\b|javascript\s*:|on(?:error|load|click)\s*=|<\s*iframe\b)",
        re.IGNORECASE,
    )
    SUSPICIOUS_UA = re.compile(
        r"(?:sqlmap|nikto|masscan|nmap|gobuster|dirbuster|wpscan)", re.IGNORECASE
    )
    LOGIN_PATH = re.compile(r"/(?:login|signin|auth)(?:/|$|\?)", re.IGNORECASE)

    def __init__(self, policy: SecurityPolicy | None = None):
        self.policy = policy or SecurityPolicy()
        self._requests: dict[str, deque[tuple[datetime, str]]] = defaultdict(deque)
        self._login_attempts: dict[str, deque[datetime]] = defaultdict(deque)
        self._blocked_until: dict[str, datetime] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _prune(items: deque, cutoff: datetime) -> None:
        while items:
            timestamp = items[0][0] if isinstance(items[0], tuple) else items[0]
            if timestamp >= cutoff:
                break
            items.popleft()

    def blocked_until(self, source_ip: str, now: datetime | None = None) -> datetime | None:
        moment = now or utc_now()
        with self._lock:
            expiry = self._blocked_until.get(source_ip)
            if expiry and expiry <= moment:
                self._blocked_until.pop(source_ip, None)
                return None
            return expiry

    def _block(self, source_ip: str, now: datetime) -> None:
        self._blocked_until[source_ip] = now + timedelta(
            seconds=self.policy.temporary_block_seconds
        )

    def evaluate(self, event: HttpAccessEvent) -> list[SecurityDetection]:
        now = event.occurred_at
        text = unquote_plus(f"{event.path}\n{event.body_sample}")
        detections: list[SecurityDetection] = []
        with self._lock:
            requests = self._requests[event.source_ip]
            requests.append((now, event.path))
            self._prune(
                requests,
                now - timedelta(seconds=max(
                    self.policy.flood_window_seconds, self.policy.scan_window_seconds
                )),
            )

            flood_count = sum(
                1 for timestamp, _ in requests
                if timestamp >= now - timedelta(seconds=self.policy.flood_window_seconds)
            )
            if flood_count > self.policy.flood_requests:
                detections.append(SecurityDetection(
                    "http_flood", "flood_http", Severity.HIGH,
                    "Volumen HTTP sobre el umbral por origen",
                    f"{flood_count} solicitudes en {self.policy.flood_window_seconds} segundos.",
                    "rate_limit",
                ))

            unique_paths = {
                path for timestamp, path in requests
                if timestamp >= now - timedelta(seconds=self.policy.scan_window_seconds)
            }
            if len(unique_paths) >= self.policy.scan_unique_paths:
                detections.append(SecurityDetection(
                    "route_scan", "escaneo_rutas", Severity.MEDIUM,
                    "Exploracion de multiples rutas desde un origen",
                    f"{len(unique_paths)} rutas unicas en {self.policy.scan_window_seconds} segundos.",
                    "temporary_block",
                ))

            if self.LOGIN_PATH.search(event.path) and event.method.upper() == "POST":
                attempts = self._login_attempts[event.source_ip]
                attempts.append(now)
                cutoff = now - timedelta(seconds=self.policy.brute_force_window_seconds)
                while attempts and attempts[0] < cutoff:
                    attempts.popleft()
                if len(attempts) >= self.policy.brute_force_attempts:
                    detections.append(SecurityDetection(
                        "brute_force", "fuerza_bruta_simulada", Severity.HIGH,
                        "Intentos repetidos sobre una ruta de autenticacion",
                        f"{len(attempts)} intentos en {self.policy.brute_force_window_seconds} segundos.",
                        "temporary_block",
                    ))

            if self.SQLI.search(text):
                detections.append(SecurityDetection(
                    "sqli_basic", "inyeccion_sql_basica", Severity.HIGH,
                    "Patron compatible con SQL Injection basica",
                    "La solicitud se rechazo por coincidencia defensiva; no se ejecuto payload.",
                    "temporary_block",
                ))
            if self.XSS.search(text):
                detections.append(SecurityDetection(
                    "xss_basic", "xss_basico", Severity.HIGH,
                    "Patron compatible con XSS basico",
                    "La solicitud se rechazo antes de alcanzar el sitio vigilado.",
                    "temporary_block",
                ))
            if self.SUSPICIOUS_UA.search(event.user_agent):
                detections.append(SecurityDetection(
                    "suspicious_user_agent", "user_agent_sospechoso", Severity.MEDIUM,
                    "Firma de herramienta automatizada en User-Agent",
                    "Indicador heuristico; requiere correlacion y no prueba compromiso.",
                    "escalate",
                ))

            if any(item.response == "temporary_block" for item in detections):
                self._block(event.source_ip, now)
        return self._deduplicate(detections)

    @staticmethod
    def _deduplicate(items: Iterable[SecurityDetection]) -> list[SecurityDetection]:
        result: list[SecurityDetection] = []
        seen: set[str] = set()
        for item in items:
            if item.rule_id not in seen:
                seen.add(item.rule_id)
                result.append(item)
        return result
