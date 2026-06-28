# Plan de pruebas funcionales

| ID | Prueba | Criterio de aceptación |
| --- | --- | --- |
| PF01 | `GET /` | HTTP 200 y `estado=ok` |
| PF02 | `GET /health/db` | HTTP 200 solo si `SELECT 1` responde; 503 en caso contrario |
| PF03 | POST sin/incorrecta `X-API-Key` | HTTP 401 |
| PF04 | POST válido | HTTP 201 y evento persistido |
| PF05 | payload vacío, extra, largo o estado desconocido | HTTP 422 |
| PF06 | paginación | máximo 100, orden descendente y `total` independiente de la página |
| PF07 | monitor normal | HTTP/contenido válidos, código de salida 0 |
| PF08 | monitor anómalo | código 1, POST de error y PNG cuando la página es capturable |
| PF09 | remediación | solo recrea `sitio-vigilado`; rechaza cualquier otro nombre |
| PF10 | continuidad normal | no remedia ni activa respaldo |
| PF11 | recuperación | remedia y vuelve a validar antes de decidir |
| PF12 | contingencia | inicia perfil `continuidad`, valida respaldo y registra evidencia |
| PF13 | dashboard | timeout, error visible, escape HTML, total y 20 eventos recientes |
| PF14 | Rocketbot | propaga códigos, conserva stdout/stderr y genera JSON |
| PF15 | SMTP | TLS, éxito y fallo dejan trazabilidad sin exponer contraseña |

## Ejecución realizada el 2026-06-28

- `unittest`: 6/6 pruebas de decisiones, lista blanca y readiness aprobadas.
- `compileall`: todos los módulos compilan.
- JSON histórico: todos los archivos se pueden deserializar.
- `docker compose config --quiet`: configuración válida.
- End-to-end Docker, MySQL, navegador y SMTP: no ejecutado porque el daemon Docker
  de la estación no estaba iniciado y no existían credenciales SMTP de prueba.

Un componente no se marca como funcional solo por compilar: PF01-PF15 deben
ejecutarse con Docker activo antes de la defensa y conservar su evidencia fechada.
