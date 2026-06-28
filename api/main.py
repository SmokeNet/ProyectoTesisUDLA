"""API HTTP para registrar y consultar eventos de observabilidad."""

import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models
from database import comprobar_conexion, crear_tablas, obtener_db

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger(__name__)

EstadoIncidente = Literal[
    "abierto",
    "contingencia_activa",
    "error",
    "error_critico",
    "ok",
    "pendiente",
    "resuelto",
]


def _origenes_cors() -> list[str]:
    valor = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    )
    origenes = [origen.strip() for origen in valor.split(",") if origen.strip()]
    if not origenes:
        raise RuntimeError("CORS_ALLOWED_ORIGINS debe contener al menos un origen.")
    return origenes


def _api_write_key() -> str:
    clave = os.getenv("API_WRITE_KEY", "")
    if len(clave) < 24:
        raise RuntimeError("API_WRITE_KEY debe tener al menos 24 caracteres.")
    return clave


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Valida configuracion y prepara el esquema al iniciar."""
    _api_write_key()
    crear_tablas()
    LOGGER.info("API iniciada y esquema MySQL disponible")
    yield


app = FastAPI(
    title="API de Observabilidad Sintetica",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes_cors(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


class IncidenteEntrada(BaseModel):
    """Datos validados para registrar un evento."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    servicio: str = Field(min_length=1, max_length=100, pattern=r"^[\w .:/-]+$")
    estado: EstadoIncidente
    mensaje: str = Field(min_length=1, max_length=1000)

    @field_validator("mensaje")
    @classmethod
    def mensaje_visible(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El mensaje no puede estar vacio.")
        return valor.strip()


class IncidenteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    servicio: str
    estado: EstadoIncidente
    mensaje: str
    fecha_hora: datetime

    @field_validator("fecha_hora", mode="before")
    @classmethod
    def asegurar_utc(cls, valor: datetime) -> datetime:
        # MySQL puede devolver DATETIME sin tzinfo; el sistema guarda siempre UTC.
        if valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor.astimezone(timezone.utc)


class ListaIncidentes(BaseModel):
    incidentes: list[IncidenteSalida]
    total: int
    limit: int
    offset: int


def exigir_clave_escritura(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Protege las operaciones que modifican datos."""
    clave_configurada = _api_write_key()
    if x_api_key is None or not secrets.compare_digest(x_api_key, clave_configurada):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de escritura invalida.",
        )


def guardar_incidente(db: Session, datos: IncidenteEntrada) -> models.Incidente:
    incidente = models.Incidente(**datos.model_dump())
    try:
        db.add(incidente)
        db.commit()
        db.refresh(incidente)
    except SQLAlchemyError as error:
        db.rollback()
        LOGGER.exception("No fue posible guardar el incidente")
        raise HTTPException(status_code=503, detail="Persistencia no disponible.") from error
    return incidente


@app.get("/", tags=["estado"])
def obtener_estado() -> dict[str, str]:
    """Liveness: confirma que el proceso HTTP esta activo."""
    return {"mensaje": "API de observabilidad sintetica activa", "estado": "ok"}


@app.get("/health/db", tags=["estado"])
def obtener_estado_base_datos(response: Response) -> dict[str, str]:
    """Readiness: comprueba MySQL mediante SELECT 1."""
    try:
        comprobar_conexion()
    except SQLAlchemyError as error:
        LOGGER.warning("Readiness MySQL fallo: %s", error.__class__.__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"engine": "mysql", "estado": "error"}
    return {"engine": "mysql", "estado": "ok"}


@app.get("/incidentes", response_model=ListaIncidentes, tags=["incidentes"])
def obtener_incidentes(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(obtener_db),
) -> ListaIncidentes:
    """Retorna una pagina ordenada desde el evento mas reciente."""
    try:
        total = db.scalar(select(func.count(models.Incidente.id))) or 0
        consulta = (
            select(models.Incidente)
            .order_by(models.Incidente.fecha_hora.desc(), models.Incidente.id.desc())
            .offset(offset)
            .limit(limit)
        )
        incidentes = list(db.scalars(consulta))
    except SQLAlchemyError as error:
        LOGGER.exception("No fue posible consultar incidentes")
        raise HTTPException(status_code=503, detail="Persistencia no disponible.") from error
    return ListaIncidentes(incidentes=incidentes, total=total, limit=limit, offset=offset)


@app.post(
    "/incidentes",
    response_model=IncidenteSalida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_clave_escritura)],
    tags=["incidentes"],
)
def crear_incidente(
    incidente_entrada: IncidenteEntrada,
    db: Session = Depends(obtener_db),
) -> models.Incidente:
    """Registra un evento validado."""
    return guardar_incidente(db, incidente_entrada)


@app.post(
    "/incidentes/demo",
    response_model=IncidenteSalida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_clave_escritura)],
    include_in_schema=False,
)
def crear_incidente_demo(db: Session = Depends(obtener_db)) -> models.Incidente:
    """Crea un evento controlado para la demostracion local."""
    return guardar_incidente(
        db,
        IncidenteEntrada(
            servicio="api",
            estado="abierto",
            mensaje="Incidente de prueba generado desde POST /incidentes/demo.",
        ),
    )
