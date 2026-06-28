"""Monitor sintetico ejecutable con evidencia y salida determinista."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGGER = logging.getLogger("monitor")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")

RAIZ = Path(__file__).resolve().parents[1]


def _cargar_entorno_local() -> None:
    """Carga docker/.env para la ejecucion local sin sobreescribir el entorno."""
    ruta = RAIZ / "docker" / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea and not linea.lstrip().startswith("#") and "=" in linea:
            nombre, valor = linea.split("=", 1)
            os.environ.setdefault(nombre.strip(), valor.strip())


_cargar_entorno_local()
URL_MONITOREADA = os.getenv("URL_MONITOREADA", "http://127.0.0.1:8080/")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_INCIDENTES_URL = os.getenv("API_INCIDENTES_URL", f"{API_BASE_URL}/incidentes")
API_WRITE_KEY = os.getenv("API_WRITE_KEY", "")
EXPECTED_TEXT = os.getenv("MONITOR_EXPECTED_TEXT", "Servicio web vigilado operativo")
TIMEOUT_MS = int(os.getenv("MONITOR_TIMEOUT_MS", "30000"))
EVIDENCE_DIR = Path(os.getenv("MONITOR_EVIDENCE_DIR", RAIZ / "evidencias" / "monitor"))


def limitar_mensaje(mensaje: str, largo_maximo: int = 1000) -> str:
    if len(mensaje) <= largo_maximo:
        return mensaje
    return f"{mensaje[:largo_maximo - 15]}... [truncado]"


def enviar_incidente(servicio: str, estado: str, mensaje: str) -> bool:
    """Envia un evento y confirma que la API lo acepto."""
    if not API_WRITE_KEY:
        LOGGER.error("API_WRITE_KEY no esta configurada; no se puede registrar el incidente")
        return False
    payload = json.dumps(
        {"servicio": servicio, "estado": estado, "mensaje": limitar_mensaje(mensaje)}
    ).encode("utf-8")
    request = Request(
        API_INCIDENTES_URL,
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": API_WRITE_KEY},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
            if response.status != 201:
                LOGGER.error("La API respondio con HTTP %s", response.status)
                return False
            return True
    except (HTTPError, URLError, TimeoutError) as error:
        LOGGER.error("No se pudo registrar el incidente: %s", error)
        return False


def _capturar_evidencia(page: object) -> str | None:
    """Captura la pagina fallida sin ocultar el error original."""
    try:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        nombre = datetime.now(timezone.utc).strftime("monitor_error_%Y%m%dT%H%M%SZ.png")
        ruta = EVIDENCE_DIR / nombre
        page.screenshot(path=str(ruta), full_page=True)
        return str(ruta)
    except (OSError, PlaywrightError) as error:
        LOGGER.warning("No fue posible guardar captura de evidencia: %s", error)
        return None


def validar_url() -> bool:
    """Valida transporte, HTTP y contenido; retorna False ante cualquier falla."""
    inicio = time.perf_counter()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                response = page.goto(URL_MONITOREADA, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
                codigo_http = response.status if response is not None else None
                if codigo_http is None:
                    raise PlaywrightError("La navegacion no entrego una respuesta HTTP.")
                if codigo_http >= 400:
                    raise PlaywrightError(f"La URL respondio HTTP {codigo_http}.")
                if EXPECTED_TEXT and EXPECTED_TEXT not in page.locator("body").inner_text():
                    raise PlaywrightError("El contenido esperado no esta presente.")
            except (PlaywrightError, PlaywrightTimeoutError) as error:
                evidencia = _capturar_evidencia(page)
                duracion = time.perf_counter() - inicio
                mensaje = limitar_mensaje(
                    f"Fallo sintetico en {URL_MONITOREADA}: {error}; "
                    f"duracion={duracion:.2f}s; evidencia={evidencia or 'no_disponible'}"
                )
                LOGGER.error(mensaje)
                enviar_incidente("playwright-monitor", "error", mensaje)
                return False
            finally:
                browser.close()
    except PlaywrightError as error:
        mensaje = f"No fue posible iniciar Playwright: {error}"
        LOGGER.error(mensaje)
        enviar_incidente("playwright-monitor", "error", mensaje)
        return False

    LOGGER.info(
        "Monitor OK url=%s http=%s duracion=%.2fs",
        URL_MONITOREADA,
        codigo_http,
        time.perf_counter() - inicio,
    )
    return True


if __name__ == "__main__":
    raise SystemExit(0 if validar_url() else 1)
