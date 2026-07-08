# Modelo de datos operacional

| Tabla | Responsabilidad |
| --- | --- |
| `servicios` | inventario, estado y último heartbeat |
| `eventos_operacionales` | bitácora completa de detección a cierre |
| `metricas` | series de disponibilidad, latencia y recursos |
| `evidencias` | ruta, tipo, MIME y SHA-256 asociados al evento |
| `intentos_remediacion` | estrategia, intento, estado antes/después y resultado |
| `incidentes` | contrato heredado compatible con la primera versión |

Los eventos usan UUID, UTC e índices por servicio/fecha y estado/severidad. Evidencia
y remediación poseen claves foráneas con borrado en cascada. La observación completa
se conserva como JSON para auditoría sin perder los campos normalizados necesarios
para consultas y métricas.
