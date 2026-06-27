# Pruebas Funcionales

## PF01 API activa

**Objetivo:** Confirmar que FastAPI responde.

**Procedimiento:** Ejecutar `GET /`.

**Resultado esperado:** La API retorna mensaje de estado `ok`.

## PF02 Docker API + MySQL

**Objetivo:** Confirmar que Docker Compose levanta API y MySQL.

**Procedimiento:** Ejecutar `docker compose -f docker/docker-compose.yml up --build -d` y consultar `docker compose -f docker/docker-compose.yml ps`.

**Resultado esperado:** Los contenedores `observabilidad-api`, `observabilidad-mysql`, `sitio-vigilado` y `ssh-remediacion` quedan en estado `Up`.

## PF03 Sitio de prueba operativo

**Objetivo:** Confirmar que el sitio de prueba responde.

**Procedimiento:** Levantar Docker Compose y consultar `http://127.0.0.1:8080/`.

**Resultado esperado:** `http://127.0.0.1:8080` muestra `Servicio web vigilado operativo`.

## PF04 Playwright OK

**Objetivo:** Validar monitoreo exitoso.

**Procedimiento:** Configurar `URL_MONITOREADA` con una URL valida y ejecutar `monitor.py`.

**Resultado esperado:** El monitor muestra URL, estado OK y tiempo de respuesta.

## PF05 Playwright error

**Objetivo:** Validar deteccion de falla.

**Procedimiento:** Configurar `URL_MONITOREADA` con una URL invalida y ejecutar `monitor.py`.

**Resultado esperado:** El monitor captura la excepcion, genera mensaje descriptivo y envia `POST /incidentes`.

## PF06 Registro en MySQL

**Objetivo:** Confirmar persistencia en MySQL.

**Procedimiento:** Ejecutar `POST /incidentes` con un payload de prueba y luego `GET /incidentes`.

**Resultado esperado:** El incidente creado aparece en la lista consultada.

## PF07 Dashboard

**Objetivo:** Confirmar visualizacion de incidentes.

**Procedimiento:** Abrir `dashboard/index.html` con la API activa.

**Resultado esperado:** El dashboard muestra total de incidentes y tabla con registros.

## PF08 Paramiko

**Objetivo:** Confirmar ejecucion del modulo de remediacion.

**Procedimiento:** Levantar el servicio `ssh-remediacion` y ejecutar `remediador.py`.

**Resultado esperado:** Paramiko se conecta a `127.0.0.1:2222`, ejecuta el comando de remediacion y registra el resultado en la API.

## PF09 Rocketbot

**Objetivo:** Confirmar que Rocketbot funciona como capa RPA principal del prototipo.

**Procedimiento:** Ejecutar desde Rocketbot Studio o desde consola el archivo:

```bat
rocketbot\ejecutar_flujo_completo.bat
```

El `.bat` ejecuta `rocketbot/robot_observabilidad.py`, que levanta Docker, valida la API, abre el dashboard, valida el sitio vigilado, ejecuta el monitor Playwright, ejecuta el remediador Paramiko contra SSH Docker y registra una evidencia JSON.

**Resultado esperado:** El flujo termina mostrando el estado general de la ejecucion y genera una evidencia JSON en `evidencias/rocketbot/`.

**Evidencia esperada:** Archivo `evidencia_rocketbot_YYYYMMDD_HHMMSS.json` con fecha/hora, pasos ejecutados, resultado de la validacion API, salida del monitor Playwright, salida del remediador Paramiko y estado general.

## Checklist de defensa

- API activa.
- Dashboard visible.
- Monitor ejecutado.
- Incidente registrado.
- Remediacion ejecutada.
- Evidencia JSON creada.
- Rocketbot Studio ejecutando el `.bat`.

**Estado actual:** Implementado como orquestador funcional mediante `rocketbot/ejecutar_flujo_completo.bat`.
