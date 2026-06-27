# Arquitectura del Prototipo

## Descripcion general

El prototipo implementa un flujo minimo de observabilidad sintetica y auto-remediacion. Un sitio web vigilado en Docker actua como objetivo controlado. Playwright monitorea su disponibilidad, registra incidentes en una API FastAPI y la API persiste la informacion en MySQL Docker. El dashboard consulta la API para visualizar incidentes. Rocketbot orquesta el flujo completo y Paramiko ejecuta una remediacion SSH real contra un contenedor de laboratorio.

Flujo final esperado:

```text
Sitio vigilado Docker -> Playwright -> FastAPI -> MySQL -> Dashboard -> Rocketbot -> Paramiko/SSH Docker
```

## Diagrama de componentes

```mermaid
flowchart LR
    sitio["Sitio vigilado Docker :8080"]
    monitor["Playwright Monitor"]
    api["FastAPI"]
    mysql["MySQL"]
    dashboard["Dashboard Web"]
    rocketbot["Rocketbot"]
    remediacion["Modulo Remediacion"]
    ssh["SSH remediacion Docker :2222"]

    monitor --> sitio
    monitor --> api
    api --> mysql
    dashboard --> api
    rocketbot --> remediacion
    remediacion --> ssh
    remediacion --> api
```

## Diagrama de flujo

```mermaid
sequenceDiagram
    participant Sitio as Sitio vigilado
    participant Playwright as Playwright
    participant API as FastAPI
    participant DB as MySQL
    participant Dashboard as Dashboard
    participant Rocketbot as Rocketbot
    participant SSH as SSH Docker

    Playwright->>Sitio: Validar URL monitoreada
    alt Servicio disponible
        Playwright->>Playwright: Registrar estado OK en consola
    else Servicio con error
        Playwright->>API: POST /incidentes
        API->>DB: Guardar incidente
    end
    Dashboard->>API: GET /incidentes
    API->>DB: Consultar incidentes
    API-->>Dashboard: Lista de incidentes
    Rocketbot->>SSH: Ejecutar remediacion
    SSH-->>Rocketbot: Resultado
    Rocketbot->>API: Registrar resultado
```
