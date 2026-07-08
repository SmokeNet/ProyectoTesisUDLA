"""Configuracion y ciclo de vida de la conexion SQLAlchemy."""

import logging
import os
import time
from collections.abc import Generator

from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

LOGGER = logging.getLogger(__name__)


def _entero_positivo(nombre: str, predeterminado: int) -> int:
    """Lee un entero positivo desde el entorno con un error comprensible."""
    valor = os.getenv(nombre, str(predeterminado))
    try:
        numero = int(valor)
    except ValueError as error:
        raise ValueError(f"{nombre} debe ser un numero entero.") from error
    if numero < 1:
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return numero


def _variable_requerida(nombre: str) -> str:
    valor = os.getenv(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta la variable de entorno requerida: {nombre}")
    return valor


MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql").strip()
MYSQL_PORT = _entero_positivo("MYSQL_PORT", 3306)
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "observabilidad").strip()
MYSQL_USER = _variable_requerida("MYSQL_USER")
MYSQL_PASSWORD = _variable_requerida("MYSQL_PASSWORD")

# URL.create escapa correctamente usuarios y contrasenas con caracteres especiales.
DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    database=MYSQL_DATABASE,
    query={"charset": "utf8mb4"},
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=_entero_positivo("DATABASE_POOL_RECYCLE_SECONDS", 1800),
    pool_size=_entero_positivo("DATABASE_POOL_SIZE", 5),
    max_overflow=_entero_positivo("DATABASE_MAX_OVERFLOW", 10),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base para los modelos de SQLAlchemy."""


def obtener_db() -> Generator[Session, None, None]:
    """Entrega una sesion por solicitud y garantiza su cierre."""
    with SessionLocal() as sesion:
        yield sesion


def comprobar_conexion() -> None:
    """Ejecuta una consulta real y falla si MySQL no responde."""
    with engine.connect() as conexion:
        conexion.execute(text("SELECT 1"))


def esperar_base_datos() -> None:
    """Espera MySQL con una cantidad finita de reintentos."""
    intentos = _entero_positivo("DATABASE_CONNECT_RETRIES", 10)
    espera_segundos = _entero_positivo("DATABASE_CONNECT_WAIT_SECONDS", 3)

    for intento in range(1, intentos + 1):
        try:
            comprobar_conexion()
            LOGGER.info("Conexion MySQL disponible")
            return
        except OperationalError:
            if intento == intentos:
                LOGGER.exception(
                    "MySQL no disponible tras %s intentos (host=%s port=%s database=%s)",
                    intentos,
                    MYSQL_HOST,
                    MYSQL_PORT,
                    MYSQL_DATABASE,
                )
                raise
            LOGGER.warning("MySQL no disponible; reintento %s/%s", intento, intentos)
            time.sleep(espera_segundos)


def crear_tablas() -> None:
    """Crea el esquema y aplica mejoras idempotentes a instalaciones existentes."""
    esperar_base_datos()
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    indices = {indice["name"] for indice in inspector.get_indexes("incidentes")}
    restricciones = {
        restriccion["name"]
        for restriccion in inspector.get_check_constraints("incidentes")
    }
    with engine.begin() as conexion:
        if "ix_incidentes_fecha_hora_id" not in indices:
            conexion.execute(
                text("CREATE INDEX ix_incidentes_fecha_hora_id ON incidentes (fecha_hora, id)")
            )
        if "ix_incidentes_servicio_estado" not in indices:
            conexion.execute(
                text("CREATE INDEX ix_incidentes_servicio_estado ON incidentes (servicio, estado)")
            )
        if "ck_incidentes_estado_valido" not in restricciones:
            conexion.execute(
                text(
                    "ALTER TABLE incidentes ADD CONSTRAINT ck_incidentes_estado_valido "
                    "CHECK (estado IN ('abierto','contingencia_activa','error',"
                    "'error_critico','ok','pendiente','resuelto'))"
                )
            )
