# Guía de demostración segura

## Preparación

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
```

Servicios: dashboard `http://127.0.0.1:5500`, sitio protegido `http://127.0.0.1:8080` y API `http://127.0.0.1:8000/docs`.

## Matriz automatizada

```powershell
.\venv\Scripts\python.exe demo\security_scenarios.py
```

Resultado esperado: normal `200`; SQLi, XSS, user-agent, fuerza bruta y escaneo `403`; flood `429`; `passed: true`. Son marcadores inertes enviados únicamente a loopback: no explotan vulnerabilidades ni consultan datos.

Luego actualice el dashboard y muestre el filtro Seguridad, la clasificación, la respuesta, la evidencia en `evidencias/security/eventos` y su SHA-256.

## Flujo operacional

```powershell
.\venv\Scripts\python.exe playwright-monitor\monitor.py
.\venv\Scripts\python.exe remediacion\remediador.py
```

Nunca ejecutar la demo contra una URL externa; el script rechaza destinos que no sean loopback.

Relato recomendado: “El prototipo detecta heurísticas comunes y automatiza respuestas reversibles. Puede producir falsos positivos; los eventos ambiguos se escalan. En producción se complementaría con WAF, SIEM y SOC.”
