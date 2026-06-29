# Ecosistema profesional de observabilidad y auto-remediación

Plataforma académica orientada a PyME que ejecuta observabilidad sintética,
clasifica fallas mediante reglas configurables, persiste telemetría y bitácora en
MySQL, genera evidencia verificable y aplica estrategias seguras con revalidación.

## Capacidades

- Health, heartbeat, disponibilidad, latencia, MTTD, MTTR y tendencias.
- 23 reglas para HTTP, timeout, DNS, SSL, puertos, contenido, recursos, Docker,
  API, MySQL, conexiones, login y SSH.
- Eventos operacionales con causa, diagnóstico, acción, resultado, tiempos,
  responsable, estado final y referencia de evidencia.
- Evidencia JSON, HTML, logs y capturas con SHA-256.
- Remediación con lista blanca, máximo de intentos, cooldown y verificación posterior.
- Contingencia mediante sitio de respaldo cuando la recuperación aplicable falla.
- Dashboard operativo y adaptador trazable para Rocketbot Studio.

## Arquitectura

```text
Rocketbot / Programador de tareas
             |
             v
ObservationOrchestrator
  | sondas -> RuleEngine -> OperationalEvent -> EvidenceStore
  |                         |                   JSON/HTML/PNG/SHA-256
  |                         v
  |                    FastAPI v2 -> MySQL
  |                         |
  +-> RemediationEngine ----+-> revalidación -> continuidad/escalamiento
                                  |
                                  v
                           Dashboard operativo
```

El núcleo está en `observability/`. `playwright-monitor/`, `continuidad/`,
`remediacion/` y `rocketbot/` son adaptadores; no duplican reglas de negocio.

## Preparación

```powershell
Copy-Item docker\.env.example docker\.env
# Reemplace todos los valores cambiar_... de docker/.env
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium
```

## Ejecución

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
.\rocketbot\ejecutar_monitor.bat
```

Servicios locales:

- Dashboard: `http://127.0.0.1:5500/`
- API/OpenAPI: `http://127.0.0.1:8000/docs`
- Sitio vigilado: `http://127.0.0.1:8080/`
- Respaldo bajo contingencia: `http://127.0.0.1:8081/`

Flujo Rocketbot/continuidad:

```powershell
.\rocketbot\ejecutar_flujo_completo.bat
.\rocketbot\ejecutar_continuidad.bat
```

## Configuración de reglas

`config/detection_rules.json` contiene umbrales y activación. Login, recursos
críticos y SSH vienen deshabilitados hasta aportar objetivos/credenciales de prueba
seguros. SSH solo valida el banner del puerto configurado; nunca ejecuta comandos.

## Seguridad operacional

- No hay credenciales versionadas; `docker/.env` está ignorado.
- Escrituras API requieren `X-API-Key`.
- Los comandos se construyen desde estrategias y servicios permitidos; no usan shell.
- DNS, SSL, disco, conexiones, SSH y despliegue se escalan: no se aplican cambios
  destructivos o difíciles de revertir.
- MySQL no publica puerto al host y la API solo escucha en loopback.

## Pruebas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q api observability playwright-monitor remediacion continuidad rocketbot tests
docker compose -f docker/docker-compose.yml config --quiet
```

Consulte [FASE1_IMPLEMENTACION.md](docs/FASE1_IMPLEMENTACION.md) para cobertura,
justificación, riesgos, validación y limitaciones reales.
