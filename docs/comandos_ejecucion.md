# Comandos de Ejecucion

## Levantar Docker

Desde la raiz del prototipo:

```powershell
cd "C:\Users\bryan\OneDrive\Desktop\Proyecto Tesis - Monotoreo\tesis-observabilidad\prototipo"
docker compose -f docker/docker-compose.yml up --build -d
```

Ver estado:

```powershell
docker compose -f docker/docker-compose.yml ps
```

Ver logs:

```powershell
docker compose -f docker/docker-compose.yml logs -f
```

Detener servicios:

```powershell
docker compose -f docker/docker-compose.yml down
```

## Ejecutar Playwright

Desde la carpeta del monitor:

```powershell
cd "C:\Users\bryan\OneDrive\Desktop\Proyecto Tesis - Monotoreo\tesis-observabilidad\prototipo\playwright-monitor"
..\venv\Scripts\python.exe monitor.py
```

Instalar navegador de Playwright si falta:

```powershell
..\venv\Scripts\python.exe -m playwright install chromium
```

## Ejecutar remediador

Desde la carpeta de remediacion:

```powershell
cd "C:\Users\bryan\OneDrive\Desktop\Proyecto Tesis - Monotoreo\tesis-observabilidad\prototipo\remediacion"
..\venv\Scripts\python.exe remediador.py
```

## Consultar incidentes

Consultar API:

```powershell
Invoke-RestMethod http://localhost:8000/incidentes
```

Crear incidente de prueba:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/incidentes `
  -ContentType "application/json" `
  -Body '{"servicio":"prueba","estado":"ok","mensaje":"Incidente de prueba"}'
```

Crear incidente demo:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/incidentes/demo
```

## Levantar sitio de prueba

Desde la carpeta del sitio:

```powershell
docker compose -f docker/docker-compose.yml up --build -d sitio-vigilado
```

URLs:

```text
http://127.0.0.1:8080
http://127.0.0.1:8080/estado.html
http://127.0.0.1:8080/error.html
```

Simular caida controlada:

```powershell
docker compose -f docker/docker-compose.yml stop sitio-vigilado
```

Recuperar sitio:

```powershell
docker compose -f docker/docker-compose.yml start sitio-vigilado
```

## Validar SSH de remediacion

Ejecutar remediador:

```powershell
.\venv\Scripts\python.exe remediacion\remediador.py
```

Validacion manual opcional:

```powershell
ssh rocketbot@127.0.0.1 -p 2222
```
