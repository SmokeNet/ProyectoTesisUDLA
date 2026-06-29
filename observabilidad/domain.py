"""Objetos de dominio independientes de infraestructura."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Severity(StrEnum):
    INFO = "info"
    LOW = "baja"
    MEDIUM = "media"
    HIGH = "alta"
    CRITICAL = "critica"


class FinalStatus(StrEnum):
    OPEN = "abierto"
    RESOLVED = "resuelto"
    ESCALATED = "escalado"
    FAILED = "fallido"
    HEALTHY = "saludable"


@dataclass(slots=True)
class Observation:
    service: str
    server: str
    target: str
    observed_at: datetime = field(default_factory=utc_now)
    latency_ms: float | None = None
    http_status: int | None = None
    dns_ok: bool | None = None
    ssl_valid: bool | None = None
    ssl_days_remaining: int | None = None
    port_open: bool | None = None
    content_expected: bool | None = None
    content_changed: bool | None = None
    login_ok: bool | None = None
    database_ok: bool | None = None
    api_ok: bool | None = None
    docker_ok: bool | None = None
    container_running: bool | None = None
    ssh_ok: bool | None = None
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent: float | None = None
    connections_percent: float | None = None
    critical_resources_ok: bool | None = None
    error_kind: str | None = None
    error_detail: str | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        return data


@dataclass(frozen=True, slots=True)
class Detection:
    rule_id: str
    incident_type: str
    severity: Severity
    cause: str
    diagnosis: str
    strategy: str


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    kind: str
    path: Path
    sha256: str
    content_type: str


@dataclass(slots=True)
class OperationalEvent:
    server: str
    service: str
    incident_type: str
    level: str
    severity: str
    cause: str
    diagnosis: str
    action_executed: str = "ninguna"
    result: str = "detectado"
    execution_time_ms: float = 0.0
    recovery_time_ms: float | None = None
    user: str = "sistema"
    robot: str = "observability-engine"
    final_status: str = FinalStatus.OPEN
    evidence_hash: str | None = None
    evidence_path: str | None = None
    detected_at: datetime = field(default_factory=utc_now)
    recovered_at: datetime | None = None
    observation: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["detected_at"] = self.detected_at.isoformat()
        data["recovered_at"] = self.recovered_at.isoformat() if self.recovered_at else None
        return data


@dataclass(frozen=True, slots=True)
class RemediationResult:
    strategy: str
    attempted: bool
    success: bool
    escalated: bool
    reason: str
    action: str
    duration_ms: float
    state_before: dict[str, Any]
    state_after: dict[str, Any]
