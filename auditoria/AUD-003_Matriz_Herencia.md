# AUD-003 — Matriz de Herencia V1 → V2

Estado: Borrador controlado
Fecha: 2026-07-08

Esta matriz define cómo tratar artefactos y componentes heredados. Ningún componente ingresa a la V2 como capacidad oficial sin revalidación técnica, documental y de evidencia.

| Artefacto o componente | Estado V1 | Decisión | Motivo | Destino | Condición para ingresar a V2 |
|---|---|---|---|---|---|
| Título oficial | Vigente | Heredar | Alineado con documentos rectores | `v2/README.md` | Mantener redacción oficial |
| Objetivo general | Vigente | Heredar | Base conceptual del proyecto | Documentación V2 | Validar con BP-001/DOC-01 actualizado |
| Estructura SGDP | Vigente parcial | Heredar | Ordena trazabilidad documental | `docs/` | Registrar artefactos y versiones |
| DOC-000 | Vigente como referencia | Heredar con actualización | Catálogo maestro aún no registra todos los nuevos artefactos | `docs/01-documentos-rectores/` | Incorporar BL-001, AUD-002, AUD-003 y artefactos V2 |
| EST-001 | Vigente como referencia | Heredar | Define nomenclatura y trazabilidad | `docs/02-estandares/` | Aplicar códigos REQ/TEST/EVD/RGO |
| DOC-00 | Vigente con ajuste requerido | Heredar condicionado | Contiene contradicción metodológica detectada | `docs/01-documentos-rectores/` | Corregir distinción entre ciclo metodológico y flujo operacional |
| BP-001 | Vigente como blueprint | Heredar | Marco de alto nivel | `docs/00-blueprints/` | Alinear alcance V2 |
| BL-001 | Antecedente de auditoría | Referenciar, no aprobar como baseline final V2 | Está en revisión y no aprobada | `docs/01-documentos-rectores/` | Convertir a baseline V2 aprobada tras criterios BL-AC |
| API FastAPI | Implementada en V1 | Revalidar antes de migrar | Puede ser útil, pero debe alinearse a contratos V2 | `v2/api/` | REQ, diseño API, tests, evidencia |
| MySQL/persistencia | Implementada en V1 | Revalidar antes de migrar | Requiere modelo normalizado y bitácora formal | `v2/api/` / `v2/docker/` | Modelo ER, migraciones, pruebas CRUD |
| Dashboard | Implementado en V1 | Revalidar antes de migrar | Debe diferenciar operacional, seguridad, remediación y escalamiento | `v2/dashboard/` | Diseño UI, datos reales, prueba funcional |
| Docker Compose | Implementado en V1 | Revalidar antes de migrar | Debe quedar reproducible y limpio | `v2/docker/` | Build limpio, servicios mínimos, healthchecks |
| Observability core | Implementado en V1 | Reutilizar selectivamente | Contiene lógica útil | `v2/observability/` | Pruebas unitarias y trazabilidad de reglas |
| Monitor Playwright | Implementado en V1 | Revalidar antes de migrar | Debe generar evidencias EVD trazadas | `v2/playwright-monitor/` | Caso TEST, evidencia hash, revalidación |
| Remediación | Implementada parcialmente | Revalidar con límites | No debe ejecutar acciones peligrosas | `v2/remediacion/` | Lista blanca, rollback, revalidación, escalamiento |
| Continuidad/sitio respaldo | Parcial | Redefinir alcance | Sitio estático no equivale a continuidad integral | `v2/sitio-respaldo/` | Definir alcance honesto y prueba de activación |
| Rocketbot BAT | Adaptador existente | Heredar como adaptador, no RPA central | No demuestra robot visual exportado | `v2/rocketbot/` | Evidencia de ejecución o robot exportado si se declara RPA |
| Paramiko/SSH | No demostrado | Excluir temporalmente | Observación crítica del profesor | Excluido | Implementación segura, entorno controlado, pruebas |
| Security Watcher local | Cambio no confirmado | Excluir temporalmente de baseline oficial | Está en worktree no commiteado | Pendiente | Diseño, pruebas, evidencias, aprobación de alcance |
| Evidencias antiguas | Existentes/ignoradas | Conservar como histórico | No tienen codificación EVD formal | `legacy/` o `docs/06-evidencias/legacy` | Normalizar metadatos sin sobrescribir |
| Tests V1 | Parciales | Revalidar | Requieren identificación TEST/CP | `v2/tests/` | Cobertura por escenario y reporte |
| Documentos de defensa previos | Heredados | Conservar como histórico | Pueden contener sobrepromesas | `legacy/` | Corrección formal antes de reutilizar |
| Métricas MTTD/MTTR | Declaradas sin campaña formal | Excluir temporalmente como resultado oficial | Requiere medición reproducible | Pendiente V2 | Campaña, muestra, cálculo y evidencia |
| Evaluación económica VAN/TIR | No verificada | Excluir temporalmente | Observación del profesor | Pendiente documental | Flujos, supuestos, VAN/TIR numéricos |

## Regla de uso

Cuando exista duda, el componente se conserva como histórico y no se promueve a V2 hasta cumplir la checklist de entrada.
