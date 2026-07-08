# Fase 1 — Refactorización y ecosistema profesional

## 1. Diagnóstico inicial

El repositorio auditado tenía una API protegida y una recuperación Compose válida,
pero seguía siendo un MVP: una tabla simple, monitor HTTP monolítico, una única
acción de remediación, evidencia no relacionada y dashboard tabular. No existían
heartbeat, series métricas, MTTD/MTTR, motor de reglas ni auditoría de estrategias.

## 2. Cambios realizados

- Creación del paquete `observability/` con configuración, dominio, logging JSON,
  cliente API, sondas, reglas, evidencias, remediación, orquestación y continuidad.
- Sustitución de scripts de 365/501 líneas por adaptadores CLI pequeños.
- API v2 con health de plataforma, eventos, métricas, heartbeat, servicios,
  evidencias, remediaciones y resumen; endpoints heredados siguen disponibles.
- Modelo MySQL normalizado en seis tablas y con índices/relaciones.
- Dashboard Dockerizado con estado, disponibilidad, incidentes, MTTD, MTTR,
  remediaciones, servicios y tendencia.
- Catálogo configurable de 23 reglas y cinco estrategias de respuesta.
- Evidencia por evento en JSON/HTML/PNG/log, SHA-256 y asociación en MySQL.
- Pruebas unitarias del catálogo, simultaneidad, seguridad, cooldown, intentos,
  revalidación, evidencia, escape HTML y alertas SMTP/simuladas.

## 3. Justificación técnica

La separación de dominio/infraestructura permite probar decisiones sin Docker,
Playwright ni MySQL. Un único `Observation` normaliza telemetría heterogénea; el
`RuleEngine` transforma hechos en detecciones; `RemediationEngine` solo acepta
estrategias y servicios registrados; `ObservationOrchestrator` conserva trazabilidad
desde observación hasta cierre. Esto reduce acoplamiento y permite incorporar nuevas
sondas o acciones sin modificar FastAPI ni Rocketbot.

## 4. Cobertura de detección

| Regla | Estado | Respuesta |
| --- | --- | --- |
| HTTP 4xx / 404 | activa | validar despliegue y escalar |
| HTTP 5xx | activa | recrear servicio y revalidar |
| timeout | activa | recrear servicio y revalidar |
| DNS caído | activa | escalar; no cambiar DNS automáticamente |
| SSL inválido / próximo a expirar | activa para HTTPS | escalar |
| latencia elevada | activa | recrear servicio y revalidar |
| puerto cerrado / servicio detenido | activa | iniciar servicio y revalidar |
| contenedor detenido | activa | iniciar servicio permitido |
| error de aplicación | activa | recrear servicio |
| página modificada / contenido inesperado | activa | escalar/validar despliegue |
| error de login | implementada, deshabilitada | requiere escenario y credenciales seguras |
| API / MySQL caídos | activa | reiniciar API o levantar MySQL |
| recursos críticos web | implementada, deshabilitada | habilitar tras definir recursos obligatorios |
| CPU / memoria / disco | activa | escalar; la telemetría actual es del host |
| conexiones saturadas | implementada, deshabilitada | requiere capacidad real del entorno |
| Docker caído | activa | escalar; el propio motor no puede reiniciar Docker |
| SSH fallido | implementada, deshabilitada | banner TCP únicamente; sin comando remoto |

## 5. Cobertura de auto-remediación

| Estrategia | Automatizada | Protección |
| --- | --- | --- |
| `restart_service` | sí | lista blanca y `--force-recreate` |
| `start_service` | sí | lista blanca |
| `restart_api` | sí | objetivo fijo `api` |
| `start_mysql` | sí | objetivo fijo `mysql` |
| `activate_backup` | sí | perfil fijo `continuidad` |
| `validate_deployment` | no | escalamiento sin mutación |
| `escalate` | no | registra y solicita intervención |

Antes de mutar se exige una segunda observación que confirme la misma falla. Cada
acción respeta máximo de intentos, cooldown, timeout y revalidación. No se mata
procesos, libera puertos, borra archivos, cambia DNS ni modifica certificados porque
esas acciones no son seguras sin un runbook y contexto empresarial específico.

## 6. Bitácora y métricas

Cada evento persiste ID, UTC, servidor, servicio, tipo, nivel, severidad, causa,
diagnóstico, acción, resultado, tiempos de detección/ejecución/recuperación, usuario,
robot, estado final, hash/ruta y observación. El resumen calcula disponibilidad a
partir de heartbeat, incidentes activos, MTTD, MTTR, cantidad y éxito de remediación,
inventario y tendencia diaria.

## 7. Validación ejecutada

| Validación | Resultado |
| --- | --- |
| Compilación de módulos Python | aprobada |
| 13 pruebas unitarias | 13/13 aprobadas |
| `docker compose config --quiet` | aprobado |
| Servicios Compose detectados | MySQL, API, dashboard y sitio vigilado |
| Versiones Playwright/psutil | verificadas en PyPI |
| Instalación local de dependencias | bloqueada: `pip` no produjo descarga |
| Ejecución Docker end-to-end | bloqueada: daemon Docker detenido |
| SMTP real | no configurado en esta fase |
| Rocketbot Studio visual | requiere aplicación/licencia externa |

No se declara aprobada ninguna prueba bloqueada.

## 8. Riesgos restantes

- `create_all` sirve para el prototipo, pero una PyME debe incorporar Alembic y un
  procedimiento de rollback de migraciones.
- La clave técnica no sustituye identidad, RBAC, TLS ni rotación centralizada.
- CPU/RAM/disco son métricas del host que ejecuta el monitor; en despliegue distribuido
  se requiere un agente por host.
- La línea base de contenido necesita un proceso formal de aprobación tras despliegues.
- Un solo MySQL/API no ofrece alta disponibilidad ni define RPO/RTO empresarial.
- MTTD depende de la frecuencia con que Rocketbot o el scheduler ejecute el monitor.
- Las rutas de evidencia son locales; almacenamiento compartido exige objeto/S3/NAS.

## 9. Recomendaciones de evolución

1. Alembic, CI con MySQL y navegador, y pruebas end-to-end de fallas inyectadas.
2. TLS, OAuth2/JWT o mTLS, gestor de secretos y auditoría de identidades.
3. Prometheus/OpenTelemetry para series de alta cardinalidad y trazas distribuidas.
4. Scheduler persistente, colas de trabajo y bloqueo distribuido de remediaciones.
5. Runbooks firmados por servicio, aprobación humana para acciones de riesgo y SLO.
6. Backups con restauración ensayada, replicación y medición formal de RTO/RPO.

## 10. Preguntas defendibles ante comisión

- ¿Por qué una regla puede detectar varias fallas pero solo una gobierna la acción?
- ¿Cómo se evita un bucle de remediación?
- ¿Por qué disco, DNS y SSL se escalan en vez de modificarse automáticamente?
- ¿Cómo se calculan MTTD, MTTR y disponibilidad, y qué sesgos tienen?
- ¿Qué demuestra el hash de evidencia y qué no demuestra?
- ¿Qué diferencia existe entre continuidad del frontend y continuidad transaccional?
- ¿Qué aporta Rocketbot frente a ejecutar directamente Python?
