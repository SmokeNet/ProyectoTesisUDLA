# Proyecto de título — Reconstrucción oficial V2

Título oficial:

“Diseño e implementación de un ecosistema de observabilidad sintética y auto-remediación autónoma de servicios críticos mediante tecnología RPA y persistencia SQL”

Este repositorio entra en una reconstrucción controlada denominada V2. La V2 no borra el trabajo anterior ni lo oculta: lo separa conceptualmente para conservar trazabilidad histórica, corregir inconsistencias y reconstruir una línea técnica defendible, gradual y alineada con la documentación SGDP vigente.

## Estado del repositorio

- La versión histórica V1 corresponde al material existente antes de la reconstrucción V2.
- La carpeta `v2/` será la raíz limpia de la nueva versión oficial.
- La carpeta `legacy/` conserva el material histórico V1 ya separado físicamente.
- La carpeta `auditoria/` contiene decisiones técnicas y matrices de trazabilidad que justifican la reconstrucción.
- La carpeta `docs/` se reorganiza con estructura SGDP para documentación oficial, evidencias, pruebas y gestión.

## Diferencia entre V1 histórica y V2 oficial

La V1 se conserva como antecedente técnico, académico y documental. Puede contener componentes útiles, pero no debe presentarse automáticamente como línea base oficial de la V2.

La V2 solo incorporará componentes cuando exista:

1. requisito asociado;
2. diseño documentado;
3. implementación;
4. prueba;
5. evidencia esperada;
6. documentación;
7. trazabilidad.

## Reglas de trazabilidad

- No se deben borrar evidencias históricas.
- No se deben sobrescribir artefactos antiguos sin control de versión.
- No se deben declarar capacidades no demostradas.
- Paramiko/SSH, RPA visual, continuidad integral, métricas MTTD/MTTR y evidencias antiguas solo podrán entrar a V2 si son revalidadas.
- Toda incorporación técnica a `v2/` debe quedar vinculada a requisito, prueba y evidencia.

## Ciclos oficiales

El ciclo metodológico del proyecto es:

`Identificar → Analizar → Diseñar → Implementar → Evaluar`

El flujo operacional del sistema es:

`Observación → Detección → Registro → Remediación → Revalidación → Evidencia`

Estos dos flujos no deben confundirse: el primero organiza el desarrollo del proyecto; el segundo describe el comportamiento funcional del ecosistema en ejecución.

## Estructura objetivo

```text
legacy/
  README_LEGACY.md
  proyecto-v1/              # material histórico V1 preservado

v2/
  README.md
  api/
  dashboard/
  docker/
  observability/
  rocketbot/
  playwright-monitor/
  remediacion/
  sitio-vigilado/
  sitio-respaldo/
  tests/
  scripts/

docs/
  00-blueprints/
  01-documentos-rectores/
  02-estandares/
  03-requisitos/
  04-arquitectura/
  05-pruebas/
  06-evidencias/
  07-manuales/
  08-informe-defensa/
  09-gestion/

auditoria/
  AUD-001_Auditoria_General.md
  AUD-002_Decision_Reconstruccion_V2.md
  AUD-003_Matriz_Herencia.md
```

## Documentos rectores para la V2

La reconstrucción toma como referencia:

- DOC-000 — Catálogo Maestro de Artefactos del Proyecto.
- EST-001 — Estándar de Identificación, Nomenclatura, Versionado y Trazabilidad.
- DOC-00 — Modelo de Gobierno del Proyecto.
- BP-001 — Blueprint Project Charter.
- BL-001 — Línea Base Oficial del Proyecto, como antecedente de auditoría y no como baseline aprobada definitiva de la V2.

## Trabajo pendiente antes de aprobar la V2

- Confirmar si se creará rama `rebuild/v2`.
- Confirmar si se generará tag histórico `BL-HIST-001`.
- Seleccionar qué componentes históricos podrán reingresar a V2 tras revalidación.
- Registrar formalmente los documentos V2 en el catálogo maestro.
- Ejecutar validación funcional y documental antes de cualquier commit/push final.
