import json
import os
import smtplib
import ssl
import subprocess
import sys
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RAIZ = Path(__file__).resolve().parents[1]
DOCKER_COMPOSE_FILE = RAIZ / "docker" / "docker-compose.yml"


def _cargar_entorno_local() -> None:
    ruta = RAIZ / "docker" / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea and not linea.lstrip().startswith("#") and "=" in linea:
            nombre, valor = linea.split("=", 1)
            os.environ.setdefault(nombre.strip(), valor.strip())


_cargar_entorno_local()

URL_PRINCIPAL = os.getenv("URL_PRINCIPAL", os.getenv("URL_MONITOREADA", "http://127.0.0.1:8080/"))
URL_RESPALDO = os.getenv("URL_RESPALDO", "http://127.0.0.1:8081/")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_INCIDENTES_URL = os.getenv("API_INCIDENTES_URL", f"{API_BASE_URL}/incidentes")
API_WRITE_KEY = os.getenv("API_WRITE_KEY", "")

INTENTOS_VALIDACION = int(os.getenv("INTENTOS_VALIDACION", "2"))
SEGUNDOS_ENTRE_INTENTOS = int(os.getenv("SEGUNDOS_ENTRE_INTENTOS", "3"))
TIMEOUT_HTTP = int(os.getenv("TIMEOUT_HTTP", "8"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_TO = os.getenv("SMTP_TO", "")


class ResultadoUrl(dict):
    """Resultado serializable de una comprobacion HTTP."""


def fecha_hora_actual() -> str:
    return datetime.now().isoformat(timespec="seconds")


def limitar_texto(texto: str, largo_maximo: int = 950) -> str:
    if len(texto) <= largo_maximo:
        return texto
    return f"{texto[:largo_maximo - 15]}... [truncado]"


def registrar_incidente(servicio: str, estado: str, mensaje: str) -> None:
    if not API_WRITE_KEY:
        print("No se pudo registrar incidente: API_WRITE_KEY no configurada")
        return
    payload = {
        "servicio": servicio,
        "estado": estado,
        "mensaje": limitar_texto(mensaje),
    }
    request = Request(
        API_INCIDENTES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": API_WRITE_KEY},
        method="POST",
    )

    try:
        with urlopen(request, timeout=TIMEOUT_HTTP) as response:
            print(f"Incidente registrado en API ({response.status}): {servicio} - {estado}")
    except (HTTPError, URLError) as error:
        print(f"No se pudo registrar incidente en API: {error}")


def validar_url(url: str, nombre: str) -> ResultadoUrl:
    inicio = time.perf_counter()
    try:
        with urlopen(url, timeout=TIMEOUT_HTTP) as response:
            cuerpo = response.read(250).decode("utf-8", errors="replace")
            duracion = time.perf_counter() - inicio
            if response.status >= 400:
                return ResultadoUrl(
                    estado="error",
                    nombre=nombre,
                    url=url,
                    codigo_http=response.status,
                    tiempo_segundos=round(duracion, 2),
                    detalle=f"HTTP {response.status}",
                )
            return ResultadoUrl(
                estado="ok",
                nombre=nombre,
                url=url,
                codigo_http=response.status,
                tiempo_segundos=round(duracion, 2),
                detalle="URL disponible",
                muestra=cuerpo,
            )
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        duracion = time.perf_counter() - inicio
        return ResultadoUrl(
            estado="error",
            nombre=nombre,
            url=url,
            codigo_http=None,
            tiempo_segundos=round(duracion, 2),
            detalle=str(error),
        )


def validar_url_con_reintentos(url: str, nombre: str) -> ResultadoUrl:
    ultimo_resultado = ResultadoUrl()
    for intento in range(1, INTENTOS_VALIDACION + 1):
        ultimo_resultado = validar_url(url, nombre)
        ultimo_resultado["intento"] = intento
        print(f"Validacion {nombre} intento {intento}: {ultimo_resultado['estado']} - {ultimo_resultado['detalle']}")
        if ultimo_resultado["estado"] == "ok":
            return ultimo_resultado
        if intento < INTENTOS_VALIDACION:
            time.sleep(SEGUNDOS_ENTRE_INTENTOS)
    return ultimo_resultado


def obtener_python() -> str:
    python_venv = RAIZ / "venv" / "Scripts" / "python.exe"
    if python_venv.exists():
        return str(python_venv)
    return sys.executable


def ejecutar_remediacion() -> dict[str, object]:
    script = RAIZ / "remediacion" / "remediador.py"
    python_cmd = obtener_python()
    if not script.exists():
        return {
            "estado": "error",
            "detalle": "No existe remediacion/remediador.py",
        }

    try:
        proceso = subprocess.run(
            [python_cmd, script.name],
            cwd=script.parent,
            capture_output=True,
            text=True,
            timeout=150,
            check=False,
            env=os.environ.copy(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"estado": "error", "detalle": str(error)}
    return {
        "estado": "ok" if proceso.returncode == 0 else "error",
        "codigo_salida": proceso.returncode,
        "stdout": proceso.stdout.strip(),
        "stderr": proceso.stderr.strip(),
    }


def activar_sitio_respaldo() -> dict[str, object]:
    comando = [
        "docker",
        "compose",
        "-f",
        str(DOCKER_COMPOSE_FILE),
        "--profile",
        "continuidad",
        "up",
        "-d",
        "sitio-respaldo",
    ]
    print("Activando sitio de respaldo con Docker Compose...")
    try:
        proceso = subprocess.run(
            comando,
            cwd=RAIZ,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        return {
            "estado": "ok" if proceso.returncode == 0 else "error",
            "comando": " ".join(comando),
            "codigo_salida": proceso.returncode,
            "stdout": proceso.stdout.strip(),
            "stderr": proceso.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {
            "estado": "error",
            "comando": " ".join(comando),
            "detalle": str(error),
        }


def enviar_notificacion_humana(asunto: str, cuerpo: str) -> dict[str, object]:
    if not (SMTP_HOST and SMTP_FROM and SMTP_TO):
        detalle = (
            "Notificacion SMTP no enviada porque faltan variables SMTP_HOST, SMTP_FROM/SMTP_USER o SMTP_TO. "
            "Se deja registro de notificacion simulada para evidencia academica."
        )
        registrar_incidente("notificacion-humana", "pendiente", f"{asunto}. {detalle}")
        return {"estado": "simulada", "detalle": detalle}

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = SMTP_FROM
    mensaje["To"] = SMTP_TO
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if SMTP_USER and SMTP_PASSWORD:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(mensaje)
        registrar_incidente("notificacion-humana", "ok", f"Correo enviado a {SMTP_TO}: {asunto}")
        return {"estado": "ok", "destinatario": SMTP_TO}
    except (OSError, smtplib.SMTPException) as error:
        registrar_incidente("notificacion-humana", "error", f"Fallo envio de correo: {error}")
        return {"estado": "error", "detalle": str(error)}


def guardar_evidencia(evidencia: dict[str, object]) -> Path:
    carpeta = RAIZ / "evidencias" / "continuidad"
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f"evidencia_continuidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with archivo.open("w", encoding="utf-8") as salida:
        json.dump(evidencia, salida, indent=2, ensure_ascii=False)
    return archivo


def ejecutar_continuidad() -> int:
    inicio = fecha_hora_actual()
    evidencia: dict[str, object] = {
        "flujo": "Continuidad operacional automatizada",
        "inicio": inicio,
        "url_principal": URL_PRINCIPAL,
        "url_respaldo": URL_RESPALDO,
        "api_incidentes": API_INCIDENTES_URL,
        "pasos": [],
    }

    print("Iniciando gestor de continuidad operacional")
    print(f"URL principal: {URL_PRINCIPAL}")
    print(f"URL respaldo: {URL_RESPALDO}")

    validacion_inicial = validar_url_con_reintentos(URL_PRINCIPAL, "sitio-principal")
    evidencia["pasos"].append({"paso": "validacion_inicial", **validacion_inicial})

    if validacion_inicial["estado"] == "ok":
        mensaje = "Sitio principal disponible. No se requiere continuidad operacional."
        registrar_incidente("continuidad-operacional", "ok", mensaje)
        evidencia.update({"estado_general": "ok", "decision": "mantener_sitio_principal", "fin": fecha_hora_actual()})
        ruta = guardar_evidencia(evidencia)
        print(mensaje)
        print(f"Evidencia JSON: {ruta.relative_to(RAIZ)}")
        return 0

    registrar_incidente(
        "continuidad-operacional",
        "error",
        f"Sitio principal indisponible: {validacion_inicial['detalle']}",
    )

    remediacion = ejecutar_remediacion()
    evidencia["pasos"].append({"paso": "remediacion_compose", **remediacion})

    validacion_post_remediacion = validar_url_con_reintentos(URL_PRINCIPAL, "sitio-principal-post-remediacion")
    evidencia["pasos"].append({"paso": "validacion_post_remediacion", **validacion_post_remediacion})

    if validacion_post_remediacion["estado"] == "ok":
        mensaje = "Sitio principal recuperado despues de la remediacion Docker Compose."
        registrar_incidente("continuidad-operacional", "resuelto", mensaje)
        notificacion = enviar_notificacion_humana(
            "Servicio principal recuperado automaticamente",
            f"El sitio {URL_PRINCIPAL} fue recuperado por el proceso "
            f"de auto-remediacion.\nFecha: {fecha_hora_actual()}",
        )
        evidencia["pasos"].append({"paso": "notificacion_humana", **notificacion})
        evidencia.update(
            {
                "estado_general": "ok",
                "decision": "sitio_principal_recuperado",
                "fin": fecha_hora_actual(),
            }
        )
        ruta = guardar_evidencia(evidencia)
        print(mensaje)
        print(f"Evidencia JSON: {ruta.relative_to(RAIZ)}")
        return 0

    activacion = activar_sitio_respaldo()
    evidencia["pasos"].append({"paso": "activar_sitio_respaldo", **activacion})
    time.sleep(3)

    validacion_respaldo = validar_url_con_reintentos(URL_RESPALDO, "sitio-respaldo")
    evidencia["pasos"].append({"paso": "validacion_respaldo", **validacion_respaldo})

    if validacion_respaldo["estado"] == "ok":
        registrar_incidente(
            "continuidad-operacional",
            "contingencia_activa",
            f"Sitio de respaldo activado en {URL_RESPALDO} porque el sitio principal no fue recuperado.",
        )
        asunto = "Alerta: sitio principal caido y contingencia activada"
        cuerpo = (
            f"Se detecto indisponibilidad del sitio principal: {URL_PRINCIPAL}\n"
            f"La remediacion automatica no logro restablecer el servicio principal.\n"
            f"Se activo el sitio de respaldo: {URL_RESPALDO}\n"
            f"Fecha: {fecha_hora_actual()}\n\n"
            "Accion requerida: revisar servicio principal y normalizar operacion."
        )
        notificacion = enviar_notificacion_humana(asunto, cuerpo)
        evidencia["pasos"].append({"paso": "notificacion_humana", **notificacion})
        evidencia.update(
            {
                "estado_general": "contingencia_activa",
                "decision": "activar_respaldo",
                "fin": fecha_hora_actual(),
            }
        )
        ruta = guardar_evidencia(evidencia)
        print("Contingencia activa. Sitio de respaldo disponible.")
        print(f"Evidencia JSON: {ruta.relative_to(RAIZ)}")
        return 0

    registrar_incidente(
        "continuidad-operacional",
        "error_critico",
        "No fue posible recuperar el sitio principal ni activar correctamente el sitio de respaldo.",
    )
    notificacion = enviar_notificacion_humana(
        "Alerta critica: sitio principal y respaldo no disponibles",
        f"No fue posible recuperar {URL_PRINCIPAL} ni activar {URL_RESPALDO}. "
        f"Fecha: {fecha_hora_actual()}",
    )
    evidencia["pasos"].append({"paso": "notificacion_humana", **notificacion})
    evidencia.update(
        {
            "estado_general": "error_critico",
            "decision": "escalamiento_manual",
            "fin": fecha_hora_actual(),
        }
    )
    ruta = guardar_evidencia(evidencia)
    print("Error critico. Requiere intervencion humana inmediata.")
    print(f"Evidencia JSON: {ruta.relative_to(RAIZ)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(ejecutar_continuidad())
