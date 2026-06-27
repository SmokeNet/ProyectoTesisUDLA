# Sistema de Observabilidad Sintetica, Auto-Remediacion y Continuidad Operacional

Prototipo funcional para tesis de Ingenieria de Ejecucion en Informatica.

El proyecto implementa un flujo de observabilidad sintetica para validar la disponibilidad de un sitio web, registrar incidentes en una API, persistirlos en MySQL Docker, visualizarlos en un dashboard y ejecutar una remediacion SSH controlada mediante Paramiko. La version actual incorpora continuidad operacional automatizada: cuando el sitio principal permanece caido despues de la remediacion, se levanta un sitio de respaldo, se registra la trazabilidad y se notifica a un responsable humano. Rocketbot actua como capa RPA de orquestacion para ejecutar el flujo completo y generar evidencias.

## Arquitectura

```text
Sitio principal Docker :8080
        ↓
Monitor Playwright
        ↓
API FastAPI :8000 → MySQL Docker :3306 → Dashboard :5500
        ↓
Rocketbot / Gestor de continuidad
        ↓
Paramiko / SSH Docker :2222
        ↓
¿Servicio recuperado?
        ↓ No
Sitio de respaldo Docker :8081 + notificacion humana
```

## Componentes

| Carpeta | Descripcion |
| --- | --- |
| `api/` | API FastAPI, modelo SQLAlchemy y conexion MySQL |
| `dashboard/` | Dashboard HTML, Bootstrap y JavaScript Vanilla |
| `docker/` | Dockerfile de API, Dockerfile SSH y Docker Compose |
| `playwright-monitor/` | Monitor sintetico con Playwright |
| `continuidad/` | Gestor de continuidad operacional: valida, remedia, activa respaldo y notifica |
| `remediacion/` | Remediador SSH con Paramiko |
| `rocketbot/` | Orquestador para Rocketbot Studio mediante `.bat` |
| `Sitio-prueba/` | Sitio web principal vigilado por Playwright |
| `Sitio-respaldo/` | Sitio de contingencia activado cuando el principal no se recupera |
| `docs/` | Documentacion tecnica y comandos de defensa |
| `evidencias/` | Carpeta preparada para evidencias generadas en ejecucion |

## Requisitos

- Docker Desktop para Windows
- Python 3.14
- PowerShell
- Navegadores de Playwright instalados en el entorno local

Instalar dependencias locales:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m playwright install chromium
```

## Ejecucion rapida

Desde la raiz del proyecto:

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
```

Validar API:

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health/db
curl http://127.0.0.1:8000/incidentes
```

Validar sitio vigilado:

```powershell
curl http://127.0.0.1:8080/
```

Ejecutar monitor Playwright:

```powershell
$env:URL_MONITOREADA="http://127.0.0.1:8080/"
.\venv\Scripts\python.exe playwright-monitor\monitor.py
```

Ejecutar remediacion SSH:

```powershell
.\venv\Scripts\python.exe remediacion\remediador.py
```

Ejecutar continuidad operacional:

```powershell
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

Demostrar contingencia con sitio principal caido:

```powershell
docker stop sitio-vigilado
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

Abrir sitio de respaldo:

```text
http://127.0.0.1:8081/
```


Ejecutar flujo completo Rocketbot:

```powershell
.\rocketbot\ejecutar_flujo_completo.bat
```

## Dashboard

Levantar servidor estatico:

```powershell
cd dashboard
..\venv\Scripts\python.exe -m http.server 5500
```

Abrir:

```text
http://127.0.0.1:5500/
```

## Base de datos

La persistencia del prototipo usa MySQL Docker.

Validar registros:

```powershell
docker exec -it observabilidad-mysql mysql -u observabilidad -pobservabilidad123 observabilidad -e "SELECT * FROM incidentes ORDER BY id DESC LIMIT 5;"
```

## Documentacion de defensa

Los comandos y checklist final estan en:

- `docs/COMANDOS_DEFENSA.md`
- `docs/CHECKLIST_FINAL_DEFENSA.md`
- `docs/FLUJO_ROCKETBOT_DEFENSA.md`
- `continuidad/README_CONTINUIDAD.md`

## Nota de seguridad

Las credenciales incluidas son de laboratorio y se usan solo para demostracion academica local. En un ambiente productivo deben reemplazarse por variables seguras, gestion de secretos y autenticacion.
