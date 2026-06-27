from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from database import (
    SessionLocal,
    crear_tablas,
    mostrar_configuracion_base_datos,
    obtener_info_base_datos,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas necesarias al iniciar la aplicacion."""
    mostrar_configuracion_base_datos()
    crear_tablas()
    yield


# Crea la aplicacion principal de FastAPI.
app = FastAPI(
    title="API de Observabilidad Sintetica",
    lifespan=lifespan,
)

# Permite que el dashboard HTML consulte la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def obtener_db():
    """Entrega una sesion de base de datos y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class IncidenteEntrada(BaseModel):
    """Datos requeridos para registrar un incidente."""

    servicio: str
    estado: str
    mensaje: str


def limitar_texto(valor: str, largo_maximo: int) -> str:
    """Ajusta textos recibidos al largo definido por el modelo de datos."""
    texto = valor.strip()

    if len(texto) <= largo_maximo:
        return texto

    return f"{texto[:largo_maximo - 15]}... [truncado]"


def formatear_incidente(incidente: models.Incidente) -> dict[str, Any]:
    """Convierte un incidente de SQLAlchemy en un diccionario JSON."""
    return {
        "id": incidente.id,
        "servicio": incidente.servicio,
        "estado": incidente.estado,
        "mensaje": incidente.mensaje,
        "fecha_hora": incidente.fecha_hora.isoformat(),
    }


def guardar_incidente(db: Session, datos: IncidenteEntrada) -> models.Incidente:
    """Guarda un incidente en MySQL y retorna el registro creado."""
    incidente = models.Incidente(
        servicio=limitar_texto(datos.servicio, 100),
        estado=limitar_texto(datos.estado, 50),
        mensaje=limitar_texto(datos.mensaje, 1000),
    )

    db.add(incidente)
    db.commit()
    db.refresh(incidente)

    return incidente


@app.get("/")
def obtener_estado() -> dict[str, str]:
    """Retorna un mensaje basico para confirmar que la API esta activa."""
    return {
        "mensaje": "API de observabilidad sintetica activa",
        "estado": "ok",
    }


@app.get("/health/db")
def obtener_estado_base_datos() -> dict[str, Any]:
    """Retorna el motor de base de datos configurado."""
    return obtener_info_base_datos()


@app.get("/incidentes")
def obtener_incidentes(db: Session = Depends(obtener_db)) -> dict[str, list[dict[str, Any]]]:
    """Retorna los incidentes guardados en MySQL."""
    incidentes = db.query(models.Incidente).order_by(models.Incidente.id).all()
    return {"incidentes": [formatear_incidente(incidente) for incidente in incidentes]}


@app.post("/incidentes")
def crear_incidente(
    incidente_entrada: IncidenteEntrada,
    db: Session = Depends(obtener_db),
) -> dict[str, Any]:
    """Registra un incidente recibido desde otro modulo del MVP."""
    incidente = guardar_incidente(db, incidente_entrada)
    return formatear_incidente(incidente)


@app.post("/incidentes/demo")
def crear_incidente_demo(db: Session = Depends(obtener_db)) -> dict[str, Any]:
    """Inserta un incidente de prueba en la base de datos."""
    datos_demo = IncidenteEntrada(
        servicio="api",
        estado="abierto",
        mensaje="Incidente de prueba generado desde POST /incidentes/demo.",
    )
    incidente = guardar_incidente(db, datos_demo)

    return {
        "mensaje": "Incidente demo creado",
        "incidente": formatear_incidente(incidente),
    }
