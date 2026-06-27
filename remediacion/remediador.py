import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import paramiko


# Variables editables para la conexion SSH local de laboratorio.
HOST = os.getenv("SSH_HOST", "127.0.0.1")
PORT = int(os.getenv("SSH_PORT", "2222"))
USERNAME = os.getenv("SSH_USER", os.getenv("SSH_USERNAME", "rocketbot"))
PASSWORD = os.getenv("SSH_PASSWORD", "rocketbot123")

# Endpoint de la API donde se registra el resultado de la remediacion.
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_INCIDENTES_URL = os.getenv(
    "API_INCIDENTES_URL",
    f"{API_BASE_URL}/incidentes",
)

# Comando minimo solicitado para validar la auto-remediacion por SSH.
COMANDO_REMEDIACION = os.getenv(
    "SSH_COMMAND",
    'echo "Remediacion SSH ejecutada correctamente"',
)


def fecha_hora_actual() -> str:
    """Retorna la fecha y hora local en formato legible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def registrar_incidente(servicio: str, estado: str, mensaje: str) -> None:
    """Envia el resultado de la remediacion a la API."""
    payload = {
        "servicio": servicio,
        "estado": estado,
        "mensaje": mensaje[:1000],
    }

    request = Request(
        API_INCIDENTES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print("Payload enviado a la API:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

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
        print(f"No se pudo registrar el resultado en la API: {error}")


def ejecutar_remediacion() -> bool:
    """Intenta conectar por SSH y ejecutar el comando de remediacion."""
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Fecha y hora: {fecha_hora_actual()}")
    print(f"Intentando conexion SSH a {HOST}:{PORT}")

    try:
        cliente.connect(
            hostname=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=10,
        )
        print("Conexion SSH exitosa")

        stdin, stdout, stderr = cliente.exec_command(COMANDO_REMEDIACION)
        salida = stdout.read().decode("utf-8").strip()
        error = stderr.read().decode("utf-8").strip()
        codigo_salida = stdout.channel.recv_exit_status()

        print(f"Resultado del comando: {salida}")

        if error:
            print(f"Error del comando: {error}")

        if codigo_salida == 0:
            registrar_incidente(
                "remediacion-paramiko",
                "ok",
                salida or "Remediacion SSH ejecutada correctamente",
            )
            return True
        else:
            mensaje_error = (
                f"Remediacion fallo con codigo {codigo_salida}. "
                f"Detalle: {error or salida}"
            )
            registrar_incidente("remediacion-paramiko", "error", mensaje_error)
            return False

    except Exception as error:
        mensaje_error = f"Conexion o ejecucion SSH fallida: {error}"
        print("Conexion SSH fallida")
        print(f"Resultado del comando: {mensaje_error}")
        registrar_incidente("remediacion-paramiko", "error", mensaje_error)
        return False

    finally:
        cliente.close()
        print(f"Fecha y hora fin: {fecha_hora_actual()}")


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar_remediacion() else 1)
