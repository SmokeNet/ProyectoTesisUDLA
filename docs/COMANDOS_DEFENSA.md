# Comandos de Defensa

Todos los comandos se ejecutan desde la raiz del prototipo:

```powershell
cd "C:\Users\bryan\OneDrive\Desktop\Proyecto Tesis - Monotoreo\tesis-observabilidad\prototipo"
```

## Levantar Docker

```powershell
docker compose -f docker/docker-compose.yml up --build -d
```

## Validar contenedores

```powershell
docker compose -f docker/docker-compose.yml ps
```

Servicios esperados:

- `observabilidad-api`
- `observabilidad-mysql`
- `sitio-vigilado`
- `ssh-remediacion`

## Validar API

```powershell
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/health/db
curl http://127.0.0.1:8000/incidentes
```

## Validar MySQL

```powershell
docker exec -it observabilidad-mysql mysql -u observabilidad -pobservabilidad123 observabilidad -e "SELECT * FROM incidentes ORDER BY id DESC LIMIT 5;"
```

## Abrir dashboard

```powershell
cd dashboard
..\venv\Scripts\python.exe -m http.server 5500
```

Abrir:

```text
http://127.0.0.1:5500/
```

## Probar sitio vigilado OK

```powershell
curl http://127.0.0.1:8080/
```

Debe mostrar `Servicio web vigilado operativo`.

## Simular caida del sitio vigilado

```powershell
docker compose -f docker/docker-compose.yml stop sitio-vigilado
```

## Recuperar sitio vigilado

```powershell
docker compose -f docker/docker-compose.yml start sitio-vigilado
```

## Ejecutar Playwright OK

```powershell
$env:URL_MONITOREADA="http://127.0.0.1:8080/"
.\venv\Scripts\python.exe playwright-monitor\monitor.py
```

## Ejecutar Playwright ERROR

```powershell
$env:URL_MONITOREADA="http://dominio-invalido-tesis.local/"
.\venv\Scripts\python.exe playwright-monitor\monitor.py
```

## Ejecutar Paramiko SSH real

```powershell
.\venv\Scripts\python.exe remediacion\remediador.py
```

Validacion manual opcional:

```powershell
ssh rocketbot@127.0.0.1 -p 2222
```

Password:

```text
rocketbot123
```

## Ejecutar Rocketbot

```powershell
.\rocketbot\ejecutar_flujo_completo.bat
```

Desde Rocketbot Studio se debe invocar el mismo archivo `.bat`.

## Revisar evidencia JSON

```powershell
Get-ChildItem evidencias\rocketbot | Sort-Object LastWriteTime -Descending | Select-Object -First 3
```

## Limpiar y reiniciar entorno

```powershell
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up --build -d
```

Para limpiar datos de incidentes:

```powershell
docker exec observabilidad-mysql mysql -uroot -proot123 -e "USE observabilidad; TRUNCATE TABLE incidentes;"
```
