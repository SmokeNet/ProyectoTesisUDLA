import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


# URL que sera validada por el monitor sintetico.
URL_MONITOREADA = os.getenv("URL_MONITOREADA", "http://127.0.0.1:8080/")

# Endpoint de la API donde se registran incidentes detectados.
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_INCIDENTES_URL = os.getenv(
    "API_INCIDENTES_URL",
    f"{API_BASE_URL}/incidentes",
)


def limpiar_mensaje(mensaje: str) -> str:
    """Evita caracteres incompatibles con algunas consolas de Windows."""
    return mensaje.encode("ascii", errors="replace").decode("ascii")


def limitar_mensaje(mensaje: str, largo_maximo: int = 900) -> str:
    """Evita enviar mensajes demasiado largos a la API."""
    if len(mensaje) <= largo_maximo:
        return mensaje

    return f"{mensaje[:largo_maximo - 15]}... [truncado]"


def enviar_incidente(servicio: str, estado: str, mensaje: str) -> None:
    """Envia un incidente a la API usando una peticion POST."""
    datos = {
        "servicio": servicio,
        "estado": estado,
        "mensaje": limitar_mensaje(mensaje),
    }
    payload = json.dumps(datos)

    print("Payload enviado a la API:")
    print(payload)

    request = Request(
        API_INCIDENTES_URL,
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            cuerpo = response.read().decode("utf-8")
            print(f"Respuesta API - Codigo HTTP: {response.status}")
            print(f"Respuesta API - Cuerpo: {cuerpo}")
    except HTTPError as error:
        cuerpo = error.read().decode("utf-8")
        print(f"Respuesta API - Codigo HTTP: {error.code}")
        print(f"Respuesta API - Cuerpo: {cuerpo}")
    except URLError as error:
        print(f"No se pudo enviar el incidente a la API: {error}")


def validar_url() -> None:
    """Abre la URL monitoreada, mide respuesta y detecta fallos."""
    inicio = time.perf_counter()
    browser = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()

            # goto retorna la respuesta principal cuando el navegador logra cargar.
            response = page.goto(URL_MONITOREADA, wait_until="load", timeout=30000)
            tiempo_respuesta = time.perf_counter() - inicio
            codigo_http = response.status if response is not None else None

            browser.close()
            browser = None

            if codigo_http is None:
                raise PlaywrightError("No fue posible obtener codigo HTTP.")

            if codigo_http >= 400:
                raise PlaywrightError(f"La URL respondio con codigo HTTP {codigo_http}.")

            print(f"URL: {URL_MONITOREADA}")
            print("Estado: OK")
            print(f"Codigo HTTP: {codigo_http}")
            print(f"Tiempo de respuesta: {tiempo_respuesta:.2f} segundos")

    except PlaywrightTimeoutError:
        tiempo_respuesta = time.perf_counter() - inicio
        mensaje = (
            f"Timeout al navegar a {URL_MONITOREADA}. "
            f"Tiempo transcurrido: {tiempo_respuesta:.2f} segundos."
        )
        print(limpiar_mensaje(mensaje))
        enviar_incidente("playwright-monitor", "error", mensaje)

    except PlaywrightError as error:
        tiempo_respuesta = time.perf_counter() - inicio
        mensaje = (
            f"Error al validar {URL_MONITOREADA}: {error}. "
            f"Tiempo transcurrido: {tiempo_respuesta:.2f} segundos."
        )
        print(limpiar_mensaje(mensaje))
        enviar_incidente("playwright-monitor", "error", mensaje)

    finally:
        if browser is not None:
            try:
                browser.close()
            except PlaywrightError:
                pass


if __name__ == "__main__":
    validar_url()
