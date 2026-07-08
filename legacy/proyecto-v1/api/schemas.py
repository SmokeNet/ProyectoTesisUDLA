"""Contratos HTTP versionados."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")


class EventCreate(ApiModel):
    id: str = Field(min_length=36, max_length=36)
    detected_at: datetime
    recovered_at: datetime | None = None
    server: str = Field(min_length=1, max_length=255)
    service: str = Field(min_length=1, max_length=100)
    incident_type: str = Field(min_length=1, max_length=100)
    level: str = Field(min_length=1, max_length=30)
    severity: Literal["info", "baja", "media", "alta", "critica"]
    cause: str = Field(min_length=1, max_length=1000)
    diagnosis: str = Field(min_length=1, max_length=10000)
    action_executed: str = Field(default="ninguna", max_length=10000)
    result: str = Field(default="detectado", max_length=10000)
    detection_time_ms: float = Field(default=0, ge=0)
    execution_time_ms: float = Field(default=0, ge=0)
    recovery_time_ms: float | None = Field(default=None, ge=0)
    user: str = Field(default="sistema", max_length=100)
    robot: str = Field(default="observability-engine", max_length=100)
    final_status: Literal["abierto", "resuelto", "escalado", "fallido", "saludable"]
    evidence_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence_path: str | None = Field(default=None, max_length=1000)
    observation: dict[str, Any]


class EventOut(ApiModel):
    id: str
    detectado_en: datetime
    recuperado_en: datetime | None
    servidor: str
    servicio: str
    tipo_incidente: str
    nivel: str
    severidad: str
    causa: str
    diagnostico: str
    accion_ejecutada: str
    resultado: str
    tiempo_deteccion_ms: float
    tiempo_ejecucion_ms: float
    tiempo_recuperacion_ms: float | None
    usuario: str
    robot_responsable: str
    estado_final: str
    hash_evidencia: str | None
    ruta_evidencia: str | None
    observacion: dict[str, Any]


class MetricCreate(ApiModel):
    service: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_.-]+$")
    value: float
    unit: str = Field(min_length=1, max_length=30)
    labels: dict[str, str] = Field(default_factory=dict)
    recorded_at: datetime | None = None


class MetricOut(ApiModel):
    id: int
    servicio: str
    nombre: str
    valor: float
    unidad: str
    etiquetas: dict
    registrada_en: datetime


class HeartbeatCreate(ApiModel):
    service: str = Field(min_length=1, max_length=100)
    service_type: str = Field(min_length=1, max_length=50)
    server: str = Field(min_length=1, max_length=255)
    target: str = Field(min_length=1, max_length=500)
    status: Literal["saludable", "degradado", "caido", "desconocido"]
    timestamp: datetime | None = None
    latency_ms: float | None = Field(default=None, ge=0)


class EvidenceCreate(ApiModel):
    kind: Literal["json", "log", "html", "screenshot", "command"]
    path: str = Field(min_length=1, max_length=1000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_type: str = Field(min_length=1, max_length=100)


class RemediationCreate(ApiModel):
    strategy: str = Field(min_length=1, max_length=100)
    attempt: int = Field(ge=1, le=10)
    attempted: bool
    success: bool
    escalated: bool
    reason: str = Field(max_length=10000)
    action: str = Field(max_length=10000)
    duration_ms: float = Field(ge=0)
    state_before: dict[str, Any]
    state_after: dict[str, Any]


class PaginatedEvents(ApiModel):
    events: list[EventOut]
    total: int
    limit: int
    offset: int


class SummaryOut(ApiModel):
    generated_at: datetime
    availability_percent: float
    active_incidents: int
    total_incidents: int
    mttr_ms: float | None
    mttd_ms: float | None
    remediation_count: int
    remediation_success_rate: float
    services: int
    operational_incidents: int
    security_incidents: int
    successful_remediations: int
    failed_remediations: int
    escalated_events: int
    trend: list[dict[str, Any]]


class ServiceOut(ApiModel):
    nombre: str
    tipo: str
    servidor: str
    objetivo: str
    estado_actual: str
    activo: bool
    ultimo_heartbeat: datetime | None
    actualizado_en: datetime
