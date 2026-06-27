import os
import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_TYPE = os.getenv("DATABASE_TYPE", "mysql").lower().strip()

if DATABASE_TYPE != "mysql":
    raise ValueError("Este prototipo usa solo MySQL. Configure DATABASE_TYPE=mysql.")

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "observabilidad")
MYSQL_USER = os.getenv("MYSQL_USER", "observabilidad")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "observabilidad123")
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)


# Engine de SQLAlchemy para conectar con MySQL.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# Fabrica de sesiones para leer y escribir en la base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base para los modelos de SQLAlchemy."""


def esperar_base_datos() -> None:
    """Espera a que la base de datos acepte conexiones."""
    intentos = int(os.getenv("DATABASE_CONNECT_RETRIES", "10"))
    espera_segundos = int(os.getenv("DATABASE_CONNECT_WAIT_SECONDS", "3"))

    for intento in range(1, intentos + 1):
        try:
            with engine.connect() as conexion:
                conexion.execute(text("SELECT 1"))
            print("Conexion a base de datos disponible.", flush=True)
            return
        except OperationalError as error:
            if intento == intentos:
                print(
                    "No fue posible conectar con la base de datos "
                    "MySQL despues de "
                    f"{intentos} intentos. host={MYSQL_HOST} "
                    f"port={MYSQL_PORT} database={MYSQL_DATABASE}",
                    flush=True,
                )
                raise

            print(
                "Base de datos no disponible "
                f"(intento {intento}/{intentos}): {error}",
                flush=True,
            )
            time.sleep(espera_segundos)


def crear_tablas() -> None:
    """Crea las tablas definidas si todavia no existen."""
    esperar_base_datos()
    Base.metadata.create_all(bind=engine)


def obtener_info_base_datos() -> dict[str, Any]:
    """Retorna informacion segura sobre la base configurada."""
    return {
        "engine": "mysql",
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "database": MYSQL_DATABASE,
        "user": MYSQL_USER,
    }


def mostrar_configuracion_base_datos() -> None:
    """Muestra en logs la configuracion de base usada por la API."""
    info = obtener_info_base_datos()

    print(
        "Base de datos configurada: "
        f"engine=mysql host={info['host']} port={info['port']} "
        f"database={info['database']} user={info['user']}",
        flush=True,
    )
