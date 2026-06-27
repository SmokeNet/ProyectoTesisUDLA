from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def fecha_hora_actual() -> datetime:
    """Retorna la fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


class Incidente(Base):
    """Modelo de la tabla incidentes."""

    __tablename__ = "incidentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    servicio: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(1000), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=fecha_hora_actual,
        nullable=False,
    )
