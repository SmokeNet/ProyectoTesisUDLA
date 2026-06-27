# Continuidad operacional automatizada

Este modulo agrega un flujo de continuidad operacional al prototipo. Cuando el sitio principal no responde, el sistema:

1. Valida el sitio principal con reintentos.
2. Registra el incidente en la API.
3. Ejecuta la auto-remediacion SSH existente.
4. Vuelve a validar el sitio principal.
5. Si no se recupera, levanta un sitio de respaldo mediante Docker Compose.
6. Valida el sitio de respaldo.
7. Notifica a un responsable humano por SMTP si las variables estan configuradas; si no, deja una notificacion simulada registrada en la API.
8. Genera evidencia JSON en `evidencias/continuidad/`.

## Ejecucion normal

```powershell
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

## Demostracion de contingencia

```powershell
docker compose -f docker/docker-compose.yml up --build -d

docker stop sitio-vigilado

.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

Luego abrir:

```text
http://127.0.0.1:8081/
```

## Variables SMTP opcionales

```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="correo@gmail.com"
$env:SMTP_PASSWORD="contraseña_de_aplicacion"
$env:SMTP_FROM="correo@gmail.com"
$env:SMTP_TO="responsable@empresa.cl"
```

Si estas variables no se configuran, el flujo no falla: registra una notificacion simulada como evidencia academica.
