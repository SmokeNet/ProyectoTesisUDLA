# Informe de auditoría técnica integral

> Documento histórico de la auditoría anterior. La arquitectura vigente y la
> validación de Fase 1 se encuentran en `FASE1_IMPLEMENTACION.md`.

**Fecha:** 2026-06-28
**Alcance:** 46 archivos funcionales, de configuración y documentales; se excluyó
únicamente la metadata interna de Git.
**Método:** inspección línea por línea, búsqueda de secretos y duplicidades,
compilación, pruebas unitarias, validación de JSON y validación de Compose. Un
resultado no ejecutado se identifica como tal.

## 1. Resumen ejecutivo

El proyecto tenía una base comprensible, pero dos afirmaciones centrales no
coincidían con su comportamiento: la supuesta remediación SSH solo ejecutaba `echo`
y el respaldo arrancaba siempre, aunque la tesis lo describía como contingencia.
También existían credenciales versionadas, CORS global, escrituras anónimas, un
healthcheck que no consultaba MySQL y consultas sin límite.

Se reemplazó la remediación ficticia por recuperación real y limitada del servicio,
se hizo condicional el respaldo, se endurecieron API/Docker/datos, se añadieron
pruebas y se reescribió la documentación para que cada afirmación sea demostrable.
El resultado es defendible como prototipo de laboratorio; no se certifica como
producción porque el end-to-end no pudo ejecutarse con el daemon Docker detenido.

## 2. Estado general

| Área | Estado auditado |
| --- | --- |
| Arquitectura | responsabilidades claras; host conserva control de Compose |
| API | validada, autenticada para escritura, paginada y con errores consistentes |
| MySQL | red interna, pool, constraints, índices y readiness real |
| Docker | Compose válido, healthchecks, reinicio, loopback y API no-root |
| Monitor | valida HTTP/contenido, captura evidencia y propaga fallo |
| Remediación | acción real con lista blanca; no acepta shell arbitrario |
| Continuidad | revalida antes de respaldo; perfil activado bajo demanda |
| Dashboard | timeout, contrato, escape HTML, total y límite de 20 |
| Rocketbot | adaptador trazable; configuración visual externa no incluida |
| Evidencias | JSON histórico válido; generación excluida de Git |
| Pruebas | unitarias/estáticas aprobadas; integración pendiente de Docker activo |

## 3. Problemas encontrados por criticidad

### Crítica

1. **Remediación no funcional:** Paramiko ejecutaba un mensaje sin modificar el
   servicio. La tesis podía afirmar recuperación donde solo había conectividad.
2. **Contingencia permanentemente activa:** `sitio-respaldo` carecía del perfil que
   la documentación decía utilizar, invalidando la demostración de activación.

### Alta

1. Credenciales MySQL/SSH débiles y versionadas en código, Compose y comandos.
2. POST de incidentes sin autenticación y CORS `*`.
3. `/health/db` exponía configuración y retornaba éxito sin consultar la base.
4. El monitor terminaba con código 0 incluso al detectar una caída.
5. La API devolvía todos los incidentes, con degradación creciente de memoria/latencia.
6. El flujo ejecutaba remediación incondicionalmente, incluso con servicio sano.

### Media

1. Entradas truncadas silenciosamente en vez de rechazarse por contrato.
2. Falta de rollback y respuesta explícita ante errores SQLAlchemy.
3. MySQL publicado en el host; imágenes/servicios sin varias defensas de ejecución.
4. Monitor verificaba transporte, pero no semántica del contenido ni capturas.
5. Dashboard sin timeout, validación de esquema ni integridad del CDN.
6. Scripts `.bat` no propagaban todos los códigos de salida.
7. Dependencias de ejecución API mezcladas con Playwright y paquetes sin usar.
8. Documentación duplicada, rutas personales, mojibake y afirmaciones contradictorias.

### Baja

1. `print` disperso en módulos y funciones largas de orquestación.
2. Nombres históricos referían SSH donde la responsabilidad era continuidad.
3. Evidencias históricas no tenían esquema/versionado formal.

## 4. Correcciones aplicadas

- API key obligatoria (mínimo 24 caracteres) y comparación en tiempo constante.
- Modelos Pydantic con campos cerrados, longitudes, extras prohibidos y HTTP 201.
- GET paginado, máximo 100, conteo separado y orden reciente primero.
- Readiness `SELECT 1`, HTTP 503 ante fallo y mensajes sin datos de conexión.
- Rollback transaccional, pool pre-ping/recycle y URL de conexión con escape seguro.
- Índices y `CHECK` aplicados también a una tabla existente al iniciar.
- Secretos retirados de archivos versionados; `docker/.env` local queda ignorado.
- Evidencias heredadas contenían una antigua contraseña o correspondían al flujo SSH
  fallido; fueron eliminadas del workspace y deben regenerarse con el flujo corregido.
- MySQL aislado en red interna; puertos públicos enlazados solo a loopback.
- API en contenedor no-root, filesystem de solo lectura, tmpfs y build multietapa.
- Respaldo bajo perfil `continuidad` y healthchecks/restart policies.
- Monitor con contenido esperado, captura PNG, autenticación y código 1 en falla.
- Remediador Compose con argumentos estructurados y lista blanca de un servicio.
- Continuidad con TLS SMTP, excepciones acotadas y segunda validación real.
- Rocketbot dejó de remediar incondicionalmente y ya no incrusta contraseñas.
- Dashboard usa timeout, valida contrato y carga Bootstrap con SRI.
- Lanzadores propagan códigos; documentación y diagramas se alinearon al código.

## 5. Mejoras implementadas

Se separaron dependencias API (`requirements-api.txt`) de herramientas locales; se
añadieron seis pruebas unitarias de las ramas críticas; se documentaron límites de
confianza y criterios de aceptación; y las evidencias distinguen una notificación
SMTP real de una simulada. La remediación queda fuera de contenedores para evitar el
riesgo de montar `/var/run/docker.sock`.

## 6. Riesgos residuales

1. **Integración no ejecutada:** Docker Desktop estaba instalado, pero su daemon no
   respondía. Deben ejecutarse PF01-PF15 antes de la defensa.
2. **Rocketbot propietario:** no existe un robot visual exportado; solo el adaptador
   invocable. La captura/configuración en Studio es evidencia externa necesaria.
3. **SMTP:** sin cuenta de prueba no se verificó entrega; el modo simulado está
   correctamente rotulado.
4. **Disponibilidad:** una sola API y una sola base no constituyen alta disponibilidad.
5. **Autenticación:** la clave técnica protege escritura, pero no sustituye usuarios,
   rotación centralizada, TLS ni RBAC para exposición pública.
6. **Suministro:** las imágenes usan versiones, no digests inmutables; el CDN es una
   dependencia externa aunque tenga SRI.
7. **Evidencia:** falta un esquema JSON versionado y firma/hash para no repudio.

## 7. Recomendaciones adicionales

- En una fase productiva: reverse proxy TLS, gestor de secretos, rotación, métricas
  Prometheus, trazas, alertas, backups/restores ensayados y alta disponibilidad.
- Exportar y versionar el robot Rocketbot real si la licencia/formato lo permite.
- Añadir CI con MySQL de servicio, Playwright y prueba de recuperación completa.
- Definir RTO/RPO medibles; la activación de una página estática no demuestra por sí
  sola continuidad de datos ni de transacciones.

Estas recomendaciones amplían el alcance; no se presentan como funciones actuales.

## 8. Cambios arquitectónicos

```text
ANTES: monitor -> API abierta -> MySQL publicado
       Rocketbot -> SSH echo (siempre) ; respaldo siempre encendido

AHORA: monitor -> API (POST autenticado / GET paginado) -> MySQL interno
       Rocketbot -> gestor de decisión -> remediar servicio permitido
                                      -> revalidar -> respaldo bajo demanda
```

La lógica de decisión permanece en Python testeable y Rocketbot conserva el rol RPA
visual. La acción privilegiada se limita por nombre y ocurre en el host, reduciendo
el acoplamiento y la superficie de ataque.

## 9. Validación funcional por componente

| Validación | Resultado |
| --- | --- |
| `python -m unittest discover -s tests -v` | **6/6 OK** |
| `python -m compileall ...` | **OK** |
| parseo de JSON heredados antes de depurarlos | **OK; luego retirados por obsoletos** |
| `docker compose ... config --quiet` | **OK** |
| búsqueda de secretos históricos conocidos | **sin coincidencias activas** |
| API/MySQL en contenedores | no ejecutada: daemon detenido |
| Playwright/navegador | no ejecutada: dependencias no disponibles localmente |
| recuperación/contingencia end-to-end | no ejecutada: daemon detenido |
| dashboard en navegador | revisión de código; no prueba visual end-to-end |
| SMTP real | no ejecutado: credenciales ausentes |
| Rocketbot Studio | no ejecutado: integración propietaria externa |

## 10. Resultado y puntuación

**Calidad actual: 84/100.**

| Dimensión | Puntos |
| --- | ---: |
| Arquitectura y mantenibilidad | 18/20 |
| Correctitud y manejo de errores | 16/20 |
| Seguridad | 15/20 |
| Datos y rendimiento | 9/10 |
| Docker/operación | 9/10 |
| Pruebas y evidencia | 7/10 |
| Documentación y defensa | 10/10 |

La deducción principal corresponde a ausencia de validación end-to-end en esta
estación, autenticación técnica básica, falta de robot Rocketbot exportado y límites
propios de un único nodo. La puntuación no subirá por documentación adicional: debe
subir con ejecuciones reproducibles y evidencia de los escenarios críticos.

## Preguntas probables de comisión

1. ¿Qué evidencia demuestra que la remediación cambia el estado del servicio?
2. ¿Cómo distingue disponibilidad HTTP 200 de contenido funcionalmente correcto?
3. ¿Por qué el respaldo es continuidad parcial y no alta disponibilidad completa?
4. ¿Qué RTO/RPO se midieron y con qué muestra?
5. ¿Qué ocurre si MySQL falla durante el registro del incidente?
6. ¿Cómo evita comandos arbitrarios o abuso de la credencial de escritura?
7. ¿Qué aporta Rocketbot que no aporta ejecutar Python directamente?
8. ¿Cómo se prueba que el respaldo no estaba activo antes del incidente?
9. ¿Qué evidencia distingue un correo simulado de uno entregado?
10. ¿Cómo migraría este prototipo a múltiples instancias y secretos gestionados?
