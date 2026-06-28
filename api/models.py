"""Modelos persistentes del dominio de observabilidad."""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
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
