import json
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

RAIZ = Path(__file__).resolve().parents[1]


def _cargar_entorno_local() -> None:
    ruta = RAIZ / "docker" / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea and not linea.lstrip().startswith("#") and "=" in linea:
            nombre, valor = linea.split("=", 1)
            os.environ.setdefault(nombre.strip(), valor.strip())


_cargar_entorno_local()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_URL = os.getenv("API_URL", f"{API_BASE_URL}/health/db")
API_INCIDENTES_URL = os.getenv(
    "API_INCIDENTES_URL",
    f"{API_BASE_URL}/incidentes",
)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:5500/")
SITIO_OBSERVADO_URL = os.getenv("SITIO_OBSERVADO_URL", "http://127.0.0.1:8080/")
SITIO_RESPALDO_URL = os.getenv("SITIO_RESPALDO_URL", "http://127.0.0.1:8081/")


def obtener_rutas() -> dict[str, Path]:
    """Calcula rutas relativas al prototipo sin depender de rutas absolutas."""
    rocketbot_dir = Path(__file__).resolve().parent
    raiz = rocketbot_dir.parent

    return {
        "raiz": raiz,
        "dashboard_dir": raiz / "dashboard",
        "monitor": raiz / "playwright-monitor" / "monitor.py",
        "continuidad": raiz / "continuidad" / "gestor_continuidad.py",
        "venv_python": raiz / "venv" / "Scripts" / "python.exe",
        "evidencias": raiz / "evidencias" / "rocketbot",
    }


def obtener_python(rutas: dict[str, Path]) -> str:
    """Usa el Python del entorno virtual si existe."""
    if rutas["venv_python"].exists():
        return str(rutas["venv_python"])

    return sys.executable


def flags_proceso_background() -> int:
    """Retorna flags para dejar servidores locales corriendo en Windows."""
    flags = 0

    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP

    if hasattr(subprocess, "DETACHED_PROCESS"):
        flags |= subprocess.DETACHED_PROCESS

    return flags


def fecha_hora_actual() -> str:
    """Retorna fecha y hora local en formato ISO."""
    return datetime.now().isoformat(timespec="seconds")


def crear_paso(nombre: str) -> dict[str, object]:
    """Crea la estructura base de un paso de ejecucion."""
    return {
        "nombre": nombre,
        "inicio": fecha_hora_actual(),
        "fin": None,
        "estado": "pendiente",
        "detalle": "",
    }


def finalizar_paso(
    paso: dict[str, object],
    estado: str,
    detalle: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Finaliza un paso y agrega informacion adicional si existe."""
    paso["fin"] = fecha_hora_actual()
    paso["estado"] = estado
    paso["detalle"] = detalle

    if extra:
        paso.update(extra)

    return paso


def validar_api() -> dict[str, object]:
    """Valida que la API FastAPI responda."""
    paso = crear_paso("Validar API FastAPI")

    try:
        with urlopen(API_URL, timeout=10) as respuesta:
            cuerpo = respuesta.read().decode("utf-8")
            datos = json.loads(cuerpo)
            if datos.get("estado") != "ok":
                raise ValueError("La API respondio sin readiness de MySQL")
            return finalizar_paso(
                paso,
                "ok",
                "API activa",
                {
                    "url": API_URL,
                    "codigo_http": respuesta.status,
                    "respuesta": cuerpo,
                },
            )
    except (URLError, json.JSONDecodeError, ValueError) as error:
        return finalizar_paso(
            paso,
            "error",
            f"No fue posible conectar con la API: {error}",
            {"url": API_URL},
        )


def esperar_api(intentos: int = 10, intervalo: float = 2.0) -> dict[str, object]:
    """Espera readiness sin depender de una pausa fija."""
    resultado: dict[str, object] = {}
    for intento in range(1, intentos + 1):
        resultado = validar_api()
        resultado["intento"] = intento
        if resultado["estado"] == "ok":
            return resultado
        if intento < intentos:
            time.sleep(intervalo)
    return resultado


def validar_url(nombre: str, url: str, timeout: int = 10) -> dict[str, object]:
    """Valida que una URL responda."""
    paso = crear_paso(nombre)

    try:
        with urlopen(url, timeout=timeout) as respuesta:
            cuerpo = respuesta.read().decode("utf-8", errors="replace")
            return finalizar_paso(
                paso,
                "ok",
                "URL disponible",
                {
                    "url": url,
                    "codigo_http": respuesta.status,
                    "respuesta_muestra": cuerpo[:300],
                },
            )
    except URLError as error:
        return finalizar_paso(
            paso,
            "error",
            f"No fue posible conectar con la URL: {error}",
            {"url": url},
        )


def ejecutar_comando(
    nombre: str,
    comando: list[str],
    cwd: Path,
    timeout: int = 120,
) -> dict[str, object]:
    """Ejecuta un comando del sistema y captura salida."""
    paso = crear_paso(nombre)

    try:
        proceso = subprocess.run(
            comando,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        estado = "ok" if proceso.returncode == 0 else "error"
        detalle = "Comando ejecutado correctamente" if estado == "ok" else "Comando termino con error"

        return finalizar_paso(
            paso,
            estado,
            detalle,
            {
                "comando": " ".join(comando),
                "codigo_salida": proceso.returncode,
                "stdout": proceso.stdout.strip(),
                "stderr": proceso.stderr.strip(),
            },
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return finalizar_paso(
            paso,
            "error",
            f"Timeout al ejecutar comando: {error}",
            {"comando": " ".join(comando)},
        )


def levantar_docker_compose(rutas: dict[str, Path]) -> dict[str, object]:
    """Levanta API y MySQL mediante Docker Compose."""
    return ejecutar_comando(
        "Levantar Docker Compose API + MySQL",
        ["docker", "compose", "-f", "docker/docker-compose.yml", "up", "--build", "-d"],
        rutas["raiz"],
        timeout=180,
    )


def iniciar_servidor_http(
    nombre: str,
    url: str,
    carpeta: Path,
    puerto: int,
    python_cmd: str,
    raiz: Path,
) -> dict[str, object]:
    """Inicia un servidor HTTP local si el puerto todavia no responde."""
    disponible = validar_url(f"Validar {nombre}", url, timeout=3)

    if disponible["estado"] == "ok":
        disponible["detalle"] = f"{nombre} ya estaba disponible"
        return disponible

    paso = crear_paso(f"Levantar {nombre}")

    if not carpeta.exists():
        return finalizar_paso(
            paso,
            "error",
            "No existe la carpeta requerida",
            {"carpeta": str(carpeta.relative_to(raiz))},
        )

    try:
        proceso = subprocess.Popen(
            [python_cmd, "-m", "http.server", str(puerto)],
            cwd=carpeta,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags_proceso_background(),
        )
        time.sleep(2)
        validacion = validar_url(f"Validar {nombre} levantado", url, timeout=5)
        estado = "ok" if validacion["estado"] == "ok" else "error"
        detalle = f"{nombre} iniciado" if estado == "ok" else f"{nombre} no respondio despues de iniciar"
        if estado == "error":
            proceso.terminate()

        return finalizar_paso(
            paso,
            estado,
            detalle,
            {
                "url": url,
                "puerto": puerto,
                "pid": proceso.pid,
                "carpeta": str(carpeta.relative_to(raiz)),
                "validacion": validacion,
            },
        )
    except OSError as error:
        return finalizar_paso(
            paso,
            "error",
            f"No fue posible levantar {nombre}: {error}",
            {"url": url},
        )


def abrir_url(nombre: str, url: str) -> dict[str, object]:
    """Abre una URL en el navegador predeterminado."""
    paso = crear_paso(nombre)

    try:
        if not webbrowser.open(url):
            return finalizar_paso(
                paso,
                "error",
                "El sistema no confirmo la apertura del navegador",
                {"url": url},
            )
        return finalizar_paso(
            paso,
            "ok",
            "URL abierta en navegador",
            {"url": url},
        )
    except (OSError, webbrowser.Error) as error:
        return finalizar_paso(
            paso,
            "error",
            f"No fue posible abrir la URL: {error}",
            {"url": url},
        )


def consultar_incidentes() -> dict[str, object]:
    """Consulta incidentes desde la API para dejar evidencia del estado."""
    paso = crear_paso("Consultar incidentes API")

    try:
        with urlopen(API_INCIDENTES_URL, timeout=10) as respuesta:
            cuerpo = respuesta.read().decode("utf-8")
            datos = json.loads(cuerpo)
            incidentes = datos.get("incidentes", [])

            return finalizar_paso(
                paso,
                "ok",
                "Incidentes consultados correctamente",
                {
                    "url": API_INCIDENTES_URL,
                    "codigo_http": respuesta.status,
                    "total_incidentes": len(incidentes),
                    "ultimos_incidentes": incidentes[-5:],
                },
            )
    except (URLError, json.JSONDecodeError) as error:
        return finalizar_paso(
            paso,
            "error",
            f"No fue posible consultar incidentes: {error}",
            {"url": API_INCIDENTES_URL},
        )


def ejecutar_script(
    nombre: str,
    script: Path,
    cwd: Path,
    python_cmd: str,
    raiz: Path,
    timeout: int = 120,
    env_extra: dict[str, str] | None = None,
) -> dict[str, object]:
    """Ejecuta un script Python con subprocess y captura su salida."""
    paso = crear_paso(nombre)

    if not script.exists():
        return finalizar_paso(
            paso,
            "error",
            "No existe el script solicitado",
            {"archivo": str(script.relative_to(raiz))},
        )

    comando = [python_cmd, script.name]

    entorno = os.environ.copy()

    if env_extra:
        entorno.update(env_extra)

    try:
        proceso = subprocess.run(
            comando,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=entorno,
        )

        estado = "ok" if proceso.returncode == 0 else "error"
        detalle = "Script ejecutado correctamente" if estado == "ok" else "Script termino con error"

        return finalizar_paso(
            paso,
            estado,
            detalle,
            {
                "archivo": str(script.relative_to(raiz)),
                "codigo_salida": proceso.returncode,
                "stdout": proceso.stdout.strip(),
                "stderr": proceso.stderr.strip(),
            },
        )
    except subprocess.TimeoutExpired as error:
        return finalizar_paso(
            paso,
            "error",
            f"Timeout al ejecutar script: {error}",
            {"archivo": str(script.relative_to(raiz))},
        )


def guardar_evidencia(rutas: dict[str, Path], evidencia: dict[str, object]) -> Path:
    """Guarda la evidencia JSON del flujo Rocketbot."""
    rutas["evidencias"].mkdir(parents=True, exist_ok=True)
    nombre = f"evidencia_rocketbot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ruta_evidencia = rutas["evidencias"] / nombre

    with ruta_evidencia.open("w", encoding="utf-8") as archivo:
        json.dump(evidencia, archivo, indent=2, ensure_ascii=False)

    return ruta_evidencia


def ejecutar_flujo() -> int:
    """Ejecuta el flujo completo de observabilidad y remediacion."""
    rutas = obtener_rutas()
    python_cmd = obtener_python(rutas)
    pasos = []

    inicio = fecha_hora_actual()
    print("Iniciando flujo Rocketbot de observabilidad")
    print(f"Fecha y hora inicio: {inicio}")
    print(f"Python utilizado: {python_cmd}")

    pasos.append(levantar_docker_compose(rutas))
    pasos.append(esperar_api())
    pasos.append(validar_url("Validar sitio vigilado Docker puerto 8080", SITIO_OBSERVADO_URL))
    pasos.append(
        iniciar_servidor_http(
            "Dashboard puerto 5500",
            DASHBOARD_URL,
            rutas["dashboard_dir"],
            5500,
            python_cmd,
            rutas["raiz"],
        )
    )
    pasos.append(abrir_url("Abrir dashboard web", DASHBOARD_URL))
    pasos.append(abrir_url("Abrir sitio observado", SITIO_OBSERVADO_URL))
    pasos.append(validar_url("Navegar sitio observado", SITIO_OBSERVADO_URL))
    time.sleep(2)

    pasos.append(
        ejecutar_script(
            "Ejecutar monitor Playwright",
            rutas["monitor"],
            rutas["monitor"].parent,
            python_cmd,
            rutas["raiz"],
            env_extra={
                "URL_MONITOREADA": SITIO_OBSERVADO_URL,
                "API_BASE_URL": API_BASE_URL,
            },
        )
    )
    pasos.append(consultar_incidentes())

    pasos.append(
        ejecutar_script(
            "Ejecutar gestor de continuidad operacional",
            rutas["continuidad"],
            rutas["continuidad"].parent,
            python_cmd,
            rutas["raiz"],
            timeout=240,
            env_extra={
                "API_BASE_URL": API_BASE_URL,
                "URL_PRINCIPAL": SITIO_OBSERVADO_URL,
                "URL_RESPALDO": SITIO_RESPALDO_URL,
            },
        )
    )

    estado_general = "ok"
    if any(paso["estado"] == "error" for paso in pasos):
        estado_general = "con_errores"

    evidencia = {
        "flujo": "Rocketbot Observabilidad Sintetica, Auto-Remediacion y Continuidad Operacional",
        "inicio": inicio,
        "fin": fecha_hora_actual(),
        "estado_general": estado_general,
        "api_incidentes": API_INCIDENTES_URL,
        "sitio_observado": SITIO_OBSERVADO_URL,
        "sitio_respaldo": SITIO_RESPALDO_URL,
        "remediacion": {"modo": "Docker Compose", "servicio": "sitio-vigilado"},
        "pasos": pasos,
    }

    ruta_evidencia = guardar_evidencia(rutas, evidencia)
    print(f"Estado general: {estado_general}")
    print(f"Evidencia JSON: {ruta_evidencia.relative_to(rutas['raiz'])}")

    return 0 if estado_general == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(ejecutar_flujo())
