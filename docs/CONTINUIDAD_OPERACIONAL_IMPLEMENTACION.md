# Implementacion agregada: continuidad operacional automatizada

## Descripcion

Se incorporo un modulo de continuidad operacional que extiende el flujo original de observabilidad sintetica y auto-remediacion. La mejora permite que, ante la caida del sitio principal, el sistema intente primero la remediacion automatica mediante SSH. Si el servicio principal no vuelve a estar disponible, el robot activa un sitio de respaldo en Docker, registra la trazabilidad del evento en la API/MySQL y notifica a un responsable humano.

## Flujo de decision

```text
Validar sitio principal :8080
        |
        v
¿Disponible?
  |             
  | Si -> Registrar OK y finalizar
  |
  No
  |
  v
Registrar incidente
  |
  v
Ejecutar remediacion SSH
  |
  v
Validar nuevamente sitio principal
  |
  +-- Si -> Registrar resuelto y notificar recuperacion
  |
  +-- No -> Activar sitio de respaldo :8081
              |
              v
          Validar respaldo
              |
              +-- Si -> Registrar contingencia activa y notificar humano
              |
              +-- No -> Registrar error critico y escalar manualmente
```

## Archivos agregados

| Archivo/carpeta | Funcion |
| --- | --- |
| `continuidad/gestor_continuidad.py` | Motor de decision de continuidad operacional. Valida el sitio principal, ejecuta remediacion, activa respaldo, registra incidentes y notifica. |
| `continuidad/README_CONTINUIDAD.md` | Instrucciones de ejecucion del modulo de continuidad. |
| `Sitio-respaldo/` | Sitio de contingencia servido por Nginx cuando el sitio principal no se recupera. |
| `rocketbot/ejecutar_continuidad.bat` | Lanzador para ejecutar el flujo desde Windows o Rocketbot Studio. |

## Archivos modificados

| Archivo | Cambio aplicado |
| --- | --- |
| `docker/docker-compose.yml` | Se agrego el servicio `sitio-respaldo` con perfil `continuidad` y puerto `8081:80`. |
| `rocketbot/robot_observabilidad.py` | Se agrego la ejecucion del gestor de continuidad dentro del flujo orquestado por Rocketbot. |
| `dashboard/index.html` | Se agregaron estados visuales para `contingencia_activa`, `pendiente` y `error_critico`. |
| `README.md` | Se actualizo la arquitectura, componentes y comandos de ejecucion. |

## Comandos de demostracion

Levantar la arquitectura base:

```powershell
docker compose -f docker/docker-compose.yml up --build -d
```

Simular caida del sitio principal:

```powershell
docker stop sitio-vigilado
```

Ejecutar continuidad operacional:

```powershell
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

Abrir el sitio de respaldo:

```text
http://127.0.0.1:8081/
```

Revisar dashboard:

```text
http://127.0.0.1:5500/
```

## Estados registrados en la API

| Estado | Significado |
| --- | --- |
| `ok` | El sitio principal estaba disponible o el flujo se ejecuto sin contingencia. |
| `error` | Se detecto indisponibilidad o fallo de remediacion. |
| `resuelto` | La remediacion recupero el sitio principal. |
| `contingencia_activa` | El sitio de respaldo fue levantado correctamente. |
| `pendiente` | Se dejo evidencia de notificacion humana simulada por falta de configuracion SMTP. |
| `error_critico` | No se logro recuperar el principal ni activar el respaldo. |

## Texto breve para informe

La mejora incorporada transforma el prototipo desde un esquema de monitoreo y remediacion hacia un flujo de continuidad operacional automatizada. Ante la indisponibilidad del sitio principal, el sistema ejecuta una secuencia de validacion, remediacion, verificacion posterior y activacion de un sitio de respaldo cuando la recuperacion automatica no resulta exitosa. Este comportamiento permite mantener una respuesta visible para los usuarios, registrar trazabilidad del incidente y escalar la situacion a un responsable humano.

## Texto breve para PPT

Continuidad operacional automatizada: si el sitio principal cae, el robot intenta remediar mediante SSH. Si no logra recuperar el servicio, activa un sitio de respaldo, registra la evidencia en MySQL, actualiza el dashboard y notifica a un humano para intervencion.
