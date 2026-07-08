"""Modelos persistentes del dominio de observabilidad."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

ESTADOS_VALIDOS = (
    "abierto",
    "contingencia_activa",
    "error",
    "error_critico",
    "ok",
    "pendiente",
    "resuelto",
)


def fecha_hora_actual() -> datetime:
    """Retorna la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


class Incidente(Base):
    """Evento observable registrado por uno de los componentes."""

    __tablename__ = "incidentes"
    __table_args__ = (
        CheckConstraint(
            f"estado IN ({', '.join(repr(estado) for estado in ESTADOS_VALIDOS)})",
            name="ck_incidentes_estado_valido",
        ),
        Index("ix_incidentes_fecha_hora_id", "fecha_hora", "id"),
        Index("ix_incidentes_servicio_estado", "servicio", "estado"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    servicio: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(1000), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_hora_actual,
        nullable=False,
    )


class Servicio(Base):
    """Inventario y ultimo estado conocido de cada servicio."""

    __tablename__ = "servicios"

    nombre: Mapped[str] = mapped_column(String(100), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    servidor: Mapped[str] = mapped_column(String(255), nullable=False)
    objetivo: Mapped[str] = mapped_column(String(500), nullable=False)
    estado_actual: Mapped[str] = mapped_column(String(30), nullable=False, default="desconocido")
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ultimo_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_hora_actual,
        onupdate=fecha_hora_actual,
    )


class EventoOperacion(Base):
    """Bitacora completa e inmutable de detecciones operacionales."""

    __tablename__ = "eventos_operacionales"
    __table_args__ = (
        Index("ix_eventos_servicio_fecha", "servicio", "detectado_en"),
        Index("ix_eventos_estado_severidad", "estado_final", "severidad"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    detectado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recuperado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    servidor: Mapped[str] = mapped_column(String(255), nullable=False)
    servicio: Mapped[str] = mapped_column(
        ForeignKey("servicios.nombre"),
        nullable=False,
    )
    tipo_incidente: Mapped[str] = mapped_column(String(100), nullable=False)
    nivel: Mapped[str] = mapped_column(String(30), nullable=False)
    severidad: Mapped[str] = mapped_column(String(30), nullable=False)
    causa: Mapped[str] = mapped_column(String(1000), nullable=False)
    diagnostico: Mapped[str] = mapped_column(Text, nullable=False)
    accion_ejecutada: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)
    tiempo_deteccion_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tiempo_ejecucion_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tiempo_recuperacion_ms: Mapped[float | None] = mapped_column(Float)
    usuario: Mapped[str] = mapped_column(String(100), nullable=False)
    robot_responsable: Mapped[str] = mapped_column(String(100), nullable=False)
    estado_final: Mapped[str] = mapped_column(String(30), nullable=False)
    hash_evidencia: Mapped[str | None] = mapped_column(String(64))
    ruta_evidencia: Mapped[str | None] = mapped_column(String(1000))
    observacion: Mapped[dict] = mapped_column(JSON, nullable=False)


class Metrica(Base):
    """Serie temporal de indicadores tecnicos."""

    __tablename__ = "metricas"
    __table_args__ = (Index("ix_metricas_nombre_fecha", "nombre", "registrada_en"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    servicio: Mapped[str] = mapped_column(
        ForeignKey("servicios.nombre"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    unidad: Mapped[str] = mapped_column(String(30), nullable=False)
    etiquetas: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    registrada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=fecha_hora_actual, nullable=False)


class Evidencia(Base):
    """Indice de artefactos asociados a un evento."""

    __tablename__ = "evidencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evento_id: Mapped[str] = mapped_column(
        ForeignKey("eventos_operacionales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ruta: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=fecha_hora_actual, nullable=False)


class IntentoRemediacion(Base):
    """Auditoria de cada estrategia intentada o escalada."""

    __tablename__ = "intentos_remediacion"
    __table_args__ = (Index("ix_remediacion_evento_inicio", "evento_id", "iniciado_en"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    evento_id: Mapped[str] = mapped_column(ForeignKey("eventos_operacionales.id", ondelete="CASCADE"), nullable=False)
    estrategia: Mapped[str] = mapped_column(String(100), nullable=False)
    intento: Mapped[int] = mapped_column(Integer, nullable=False)
    ejecutada: Mapped[bool] = mapped_column(Boolean, nullable=False)
    exitosa: Mapped[bool] = mapped_column(Boolean, nullable=False)
    escalada: Mapped[bool] = mapped_column(Boolean, nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    duracion_ms: Mapped[float] = mapped_column(Float, nullable=False)
    estado_antes: Mapped[dict] = mapped_column(JSON, nullable=False)
    estado_despues: Mapped[dict] = mapped_column(JSON, nullable=False)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=fecha_hora_actual, nullable=False)
