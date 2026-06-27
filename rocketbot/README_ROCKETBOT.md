# Integracion Rocketbot

Este documento describe la capa RPA principal del prototipo de observabilidad sintetica y auto-remediacion.

## Objetivo

Rocketbot actua como orquestador del flujo completo:

1. Validar que la API FastAPI este activa.
2. Abrir el dashboard web en el navegador.
3. Validar el sitio vigilado en Docker.
4. Ejecutar el monitor Playwright.
5. Ejecutar el remediador Paramiko contra SSH Docker.
6. Guardar una evidencia JSON con fecha/hora, pasos ejecutados y resultado.

## Archivos

```text
rocketbot/robot_observabilidad.py
rocketbot/ejecutar_flujo_completo.bat
evidencias/rocketbot/
```

## Ejecucion manual

Desde la raiz del prototipo:

```bat
rocketbot\ejecutar_flujo_completo.bat
```

El archivo `.bat` detecta automaticamente si existe:

```text
venv\Scripts\python.exe
```

Si existe, usa ese entorno virtual. Si no existe, usa `python` del sistema.

## Uso desde Rocketbot Studio

Configurar una accion principal que ejecute:

```text
rocketbot\ejecutar_flujo_completo.bat
```

El robot no usa rutas absolutas. Todas las rutas se resuelven desde la ubicacion del archivo `.bat` y la carpeta raiz del prototipo.

## Evidencias

Cada ejecucion genera un archivo JSON en:

```text
evidencias\rocketbot\
```

El JSON incluye:

- fecha y hora de inicio
- fecha y hora de termino
- estado general
- pasos ejecutados
- salida estandar de Playwright y Paramiko
- errores capturados
- codigos de salida

## Checklist de defensa

- API activa.
- Dashboard visible.
- Monitor ejecutado.
- Incidente registrado.
- Remediacion ejecutada.
- Evidencia JSON creada.
- Rocketbot Studio ejecutando el `.bat`.

## Requisitos previos

La API debe estar activa en:

```text
http://localhost:8000/
```

El flujo tambien puede levantar Docker automaticamente con:

```text
docker compose -f docker/docker-compose.yml up --build -d
```

El dashboard debe existir en:

```text
dashboard\index.html
```

El monitor Playwright debe existir en:

```text
playwright-monitor\monitor.py
```

El remediador Paramiko debe existir en:

```text
remediacion\remediador.py
```

El contenedor SSH de laboratorio debe quedar disponible en:

```text
127.0.0.1:2222
usuario: rocketbot
password: rocketbot123
```
