# Modelo de datos

La tabla `incidentes` representa eventos inmutables de los componentes.

| Campo | Tipo | Regla |
| --- | --- | --- |
| `id` | INTEGER | clave primaria |
| `servicio` | VARCHAR(100) | requerido; índice compuesto con estado |
| `estado` | VARCHAR(50) | requerido; conjunto cerrado |
| `mensaje` | VARCHAR(1000) | requerido |
| `fecha_hora` | DATETIME UTC | requerido; índice compuesto con id |

Estados: `abierto`, `error`, `ok`, `resuelto`, `pendiente`,
`contingencia_activa` y `error_critico`. Pydantic valida antes de persistir y el
modelo declara además un `CHECK`. MySQL se alcanza solo desde la red `datos`; para
administración se usa `docker compose exec mysql`, no un puerto publicado.

El prototipo tiene una sola entidad y no necesita claves foráneas. Para un sistema
mayor convendría separar incidentes, servicios y transiciones, pero hacerlo aquí
añadiría complejidad sin una relación de dominio que la justifique.
