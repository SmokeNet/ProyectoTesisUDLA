"""Ejecutor de una accion de remediacion controlada y verificable."""

import json
import logging
import os
import subprocess
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LOGGER = logging.getLogger("remediador")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")

RAIZ = Path(__file__).resolve().parents[1]
COMPOSE_FILE = RAIZ / "docker" / "docker-compose.yml"


def _cargar_entorno_local() -> None:
    ruta = RAIZ / "docker" / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea and not linea.lstrip().startswith("#") and "=" in linea:
            nombre, valor = linea.split("=", 1)
            os.environ.setdefault(nombre.strip(), valor.strip())


_cargar_entorno_local()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_INCIDENTES_URL = os.getenv("API_INCIDENTES_URL", f"{API_BASE_URL}/incidentes")
API_WRITE_KEY = os.getenv("API_WRITE_KEY", "")
SERVICIO_OBJETIVO = os.getenv("REMEDIATION_SERVICE", "sitio-vigilado")
SERVICIOS_PERMITIDOS = {"sitio-vigilado"}


def registrar_incidente(estado: str, mensaje: str) -> bool:
    if not API_WRITE_KEY:
        LOGGER.error("API_WRITE_KEY no configurada")
        return False
    request = Request(
        API_INCIDENTES_URL,
        data=json.dumps(
            {"servicio": "remediacion-compose", "estado": estado, "mensaje": mensaje[:1000]}
        ).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": API_WRITE_KEY},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
            return response.status == 201
    except (HTTPError, URLError, TimeoutError) as error:
        LOGGER.error("No se pudo registrar el resultado: %s", error)
        return False


def ejecutar_remediacion() -> bool:
    """Recrea el servicio permitido mediante Compose, sin shell ni comando arbitrario."""
    if SERVICIO_OBJETIVO not in SERVICIOS_PERMITIDOS:
        mensaje = f"Servicio de remediacion no permitido: {SERVICIO_OBJETIVO}"
        LOGGER.error(mensaje)
        registrar_incidente("error", mensaje)
        return False

    comando = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "up",
        "-d",
        "--no-deps",
        "--force-recreate",
        SERVICIO_OBJETIVO,
    ]
    try:
        proceso = subprocess.run(
            comando,
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        mensaje = f"No se pudo ejecutar la remediacion: {error}"
        LOGGER.error(mensaje)
        registrar_incidente("error", mensaje)
        return False

    detalle = (proceso.stderr or proceso.stdout).strip()
    if proceso.returncode != 0:
        mensaje = f"Remediacion fallo con codigo {proceso.returncode}: {detalle}"
        LOGGER.error(mensaje)
        registrar_incidente("error", mensaje)
        return False

    mensaje = f"Servicio {SERVICIO_OBJETIVO} recreado correctamente mediante Docker Compose."
    LOGGER.info(mensaje)
    registrar_incidente("resuelto", mensaje)
    return True


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar_remediacion() else 1)
