# Observabilidad sintética y continuidad operacional

Prototipo académico que supervisa un sitio web, registra eventos en FastAPI/MySQL,
los presenta en un dashboard y ejecuta una recuperación controlada con Docker
Compose. Si la recuperación no resulta, activa un sitio de respaldo y deja evidencia
JSON. `rocketbot/robot_observabilidad.py` es el adaptador invocado desde Rocketbot
Studio o desde los lanzadores de Windows.

## Flujo real

```text
Playwright -> sitio principal :8080
       | falla
       v
FastAPI :8000 -> MySQL (solo red Docker) -> dashboard :5500
       |
       v
gestor de continuidad -> recrear sitio principal -> volver a comprobar
       | sigue caído
       v
activar perfil continuidad / sitio de respaldo :8081 / notificar / evidenciar
```

La remediación acepta únicamente el servicio `sitio-vigilado`; no ejecuta texto
arbitrario ni monta el socket Docker dentro de un contenedor. La versión anterior
abría una sesión SSH que solo hacía `echo`: eso comprobaba conectividad, pero no
recuperaba el servicio, por lo que fue retirado como afirmación funcional.

## Componentes

| Ruta | Responsabilidad |
| --- | --- |
| `api/` | API, validación, persistencia y readiness |
| `playwright-monitor/` | prueba de HTTP, contenido, latencia y captura de error |
| `remediacion/` | recuperación con lista blanca mediante Compose |
| `continuidad/` | decisión, reintentos, respaldo, correo y evidencia |
| `rocketbot/` | adaptador/orquestador para Rocketbot Studio y Windows |
| `dashboard/` | vista paginada y protegida contra inyección HTML |
| `docker/` | servicios, redes, healthchecks y configuración local |
| `tests/` | pruebas unitarias sin infraestructura externa |
| `docs/` | arquitectura, pruebas, defensa e informe de auditoría |

## Preparación

Requisitos: Docker Desktop, Python 3.14 y PowerShell.

```powershell
Copy-Item docker\.env.example docker\.env
# Edite docker\.env y reemplace todos los valores "cambiar_...".
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium
```

`docker/.env` está ignorado por Git. `API_WRITE_KEY` debe tener 24 caracteres o
más. MySQL no publica el puerto 3306 al host y la API solo escucha en loopback.

## Ejecución

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod 'http://127.0.0.1:8000/incidentes?limit=20&offset=0'
```

Registrar un evento protegido:

```powershell
$config = Get-Content docker\.env | ConvertFrom-StringData
$headers = @{ 'X-API-Key' = $config.API_WRITE_KEY }
$body = @{ servicio='demo'; estado='abierto'; mensaje='Prueba controlada' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/incidentes -Method Post -Headers $headers -ContentType 'application/json' -Body $body
```

Monitor, continuidad y flujo orquestado:

```powershell
.\venv\Scripts\python.exe playwright-monitor\monitor.py
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
.\rocketbot\ejecutar_flujo_completo.bat
```

Para el dashboard:

```powershell
Push-Location dashboard
..\venv\Scripts\python.exe -m http.server 5500
Pop-Location
```

Abra `http://127.0.0.1:5500/`.

## Demostración de continuidad

```powershell
docker compose -f docker/docker-compose.yml stop sitio-vigilado
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

El gestor primero intenta recrear `sitio-vigilado`. Para demostrar el respaldo,
provoque además un fallo real de recuperación (por ejemplo, una imagen inválida en
un entorno de prueba aislado); entonces se inicia exclusivamente el perfil
`continuidad` y se valida `http://127.0.0.1:8081/`.

Consultar MySQL sin publicar credenciales en la línea de comandos:

```powershell
docker compose -f docker/docker-compose.yml exec mysql sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "SELECT id,servicio,estado,fecha_hora FROM incidentes ORDER BY id DESC LIMIT 5"'
```

## Pruebas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q api continuidad playwright-monitor remediacion rocketbot
docker compose -f docker/docker-compose.yml config --quiet
```

La evidencia generada se guarda bajo `evidencias/` y está excluida de Git para no
versionar datos operacionales. Consulte `docs/INFORME_AUDITORIA_TECNICA.md` para el
alcance verificado y las limitaciones de la ejecución actual.
