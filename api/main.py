"""API versionada del ecosistema de observabilidad."""

import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any, Callable, Literal, TypeVar

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import models
import repository
import schemas
from database import comprobar_conexion, crear_tablas, obtener_db

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


def _origins() -> list[str]:
    value = os.getenv("CORS_ALLOWED_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not origins:
        raise RuntimeError("CORS_ALLOWED_ORIGINS no puede estar vacio")
    return origins


def _write_key() -> str:
    key = os.getenv("API_WRITE_KEY", "")
    if len(key) < 24:
        raise RuntimeError("API_WRITE_KEY debe tener al menos 24 caracteres")
    return key


@asynccontextmanager
async def lifespan(_: FastAPI):
    _write_key()
    crear_tablas()
    LOGGER.info("API operacional iniciada")
    yield


app = FastAPI(
    title="Plataforma de Observabilidad y Auto-Remediacion",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


def require_write_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    if x_api_key is None or not secrets.compare_digest(x_api_key, _write_key()):
        raise HTTPException(status_code=401, detail="Credencial de escritura invalida")


def db_call(db: Session, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="El recurso ya existe o viola una relacion") from error
    except SQLAlchemyError as error:
        db.rollback()
        LOGGER.exception("Operacion de persistencia fallida")
        raise HTTPException(status_code=503, detail="Persistencia no disponible") from error


@app.get("/", tags=["estado"])
def liveness() -> dict[str, str]:
    return {"estado": "ok", "version": "2.0.0", "servicio": "observability-api"}


@app.get("/health/db", tags=["estado"])
def database_health(response: Response) -> dict[str, str]:
    try:
        comprobar_conexion()
    except SQLAlchemyError as error:
        LOGGER.warning("Readiness MySQL fallo: %s", error.__class__.__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"engine": "mysql", "estado": "error"}
    return {"engine": "mysql", "estado": "ok"}


@app.get("/api/v1/health", tags=["estado"])
def platform_health(response: Response) -> dict[str, Any]:
    db_status = database_health(response)
    return {
        "estado": "ok" if db_status["estado"] == "ok" else "degradado",
        "componentes": {"api": "ok", "mysql": db_status["estado"]},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/api/v1/events",
    response_model=schemas.EventOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
    tags=["eventos"],
)
def create_event(payload: schemas.EventCreate, db: Session = Depends(obtener_db)):
    return db_call(db, lambda: repository.create_event(db, payload))


@app.get("/api/v1/events", response_model=schemas.PaginatedEvents, tags=["eventos"])
def list_events(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    event_status: Annotated[str | None, Query(alias="status")] = None,
    db: Session = Depends(obtener_db),
) -> schemas.PaginatedEvents:
    events, total = db_call(db, lambda: repository.list_events(db, limit, offset, event_status))
    return schemas.PaginatedEvents(events=events, total=total, limit=limit, offset=offset)


@app.post(
    "/api/v1/metrics",
    response_model=schemas.MetricOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
    tags=["metricas"],
)
def create_metric(payload: schemas.MetricCreate, db: Session = Depends(obtener_db)):
    return db_call(db, lambda: repository.create_metric(db, payload))


@app.post(
    "/api/v1/heartbeat",
    response_model=schemas.ServiceOut,
    dependencies=[Depends(require_write_key)],
    tags=["servicios"],
)
def heartbeat(payload: schemas.HeartbeatCreate, db: Session = Depends(obtener_db)):
    return db_call(db, lambda: repository.upsert_heartbeat(db, payload))


@app.get("/api/v1/services", response_model=list[schemas.ServiceOut], tags=["servicios"])
def list_services(db: Session = Depends(obtener_db)):
    return db_call(
        db,
        lambda: list(db.scalars(select(models.Servicio).order_by(models.Servicio.nombre))),
    )


@app.post(
    "/api/v1/events/{event_id}/evidence",
    status_code=201,
    dependencies=[Depends(require_write_key)],
    tags=["evidencias"],
)
def add_evidence(event_id: str, payload: schemas.EvidenceCreate, db: Session = Depends(obtener_db)):
    if db.get(models.EventoOperacion, event_id) is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    item = db_call(db, lambda: repository.add_evidence(db, event_id, payload))
    return {"id": item.id, "evento_id": item.evento_id, "sha256": item.sha256, "ruta": item.ruta}


@app.post(
    "/api/v1/events/{event_id}/remediations",
    status_code=201,
    dependencies=[Depends(require_write_key)],
    tags=["remediaciones"],
)
def add_remediation(event_id: str, payload: schemas.RemediationCreate, db: Session = Depends(obtener_db)):
    if db.get(models.EventoOperacion, event_id) is None:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    item = db_call(db, lambda: repository.add_remediation(db, event_id, payload))
    return {"id": item.id, "evento_id": item.evento_id, "exitosa": item.exitosa, "escalada": item.escalada}


@app.get("/api/v1/metrics/summary", response_model=schemas.SummaryOut, tags=["metricas"])
def metrics_summary(
    hours: Annotated[int, Query(ge=1, le=24 * 90)] = 24,
    db: Session = Depends(obtener_db),
):
    return db_call(db, lambda: repository.summary(db, hours))


# Compatibilidad con consumidores de la primera version.
LegacyState = Literal["abierto", "contingencia_activa", "error", "error_critico", "ok", "pendiente", "resuelto"]


class LegacyIncidentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    servicio: str = Field(min_length=1, max_length=100, pattern=r"^[\w .:/-]+$")
    estado: LegacyState
    mensaje: str = Field(min_length=1, max_length=1000)

    @field_validator("mensaje")
    @classmethod
    def non_empty(cls, value: str) -> str:
        return value.strip()


class LegacyIncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    servicio: str
    estado: LegacyState
    mensaje: str
    fecha_hora: datetime


@app.get("/incidentes", tags=["compatibilidad"])
def legacy_list(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(obtener_db),
):
    total = db_call(db, lambda: db.scalar(select(func.count(models.Incidente.id))) or 0)
    query = select(models.Incidente).order_by(models.Incidente.id.desc()).offset(offset).limit(limit)
    items = db_call(db, lambda: list(db.scalars(query)))
    return {
        "incidentes": [LegacyIncidentOut.model_validate(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.post(
    "/incidentes",
    response_model=LegacyIncidentOut,
    status_code=201,
    dependencies=[Depends(require_write_key)],
    tags=["compatibilidad"],
)
def legacy_create(payload: LegacyIncidentCreate, db: Session = Depends(obtener_db)):
    item = models.Incidente(**payload.model_dump())

    def save():
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    return db_call(db, save)
