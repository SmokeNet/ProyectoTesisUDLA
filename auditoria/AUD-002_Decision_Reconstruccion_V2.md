# AUD-002 — Decisión de Reconstrucción V2

## 1. Identificación

- Código: AUD-002
- Nombre: Decisión de Reconstrucción V2
- Estado: Ejecutado parcialmente — movimiento V1 aprobado
- Fecha de elaboración: 2026-07-08
- Proyecto: Diseño e implementación de un ecosistema de observabilidad sintética y auto-remediación autónoma de servicios críticos mediante tecnología RPA y persistencia SQL

## 2. Decisión

Se decide reconstruir el repositorio mediante una versión oficial V2, separada de la V1 histórica, sin eliminar información anterior y sin presentar el material heredado como línea base oficial nueva hasta que sea revisado, trazado y validado.

## 3. Motivo de la reconstrucción

La auditoría técnica y la observación del profesor guía evidenciaron inconsistencias entre documentación, código, demostración y capacidades declaradas. Entre los principales puntos detectados se encuentran:

- afirmaciones sobre Paramiko/SSH no demostradas en el código vigente;
- uso de Rocketbot como lanzador/adaptador, no como robot visual central exportado;
- continuidad operacional limitada a un sitio estático de respaldo;
- ausencia de campaña formal de medición MTTD/MTTR;
- evidencias antiguas sin codificación EVD formal;
- pruebas sin estructura TEST/CP completa;
- documentación que puede sobreprometer capacidades;
- necesidad de separar el ciclo metodológico del flujo operacional.

La V2 permite conservar el aprendizaje acumulado y reconstruir una solución defendible, incremental y trazable.

## 4. Qué se conserva

Se conserva como conocimiento heredado:

- título oficial del proyecto;
- objetivo general y objetivos específicos;
- estructura SGDP;
- nomenclatura documental;
- hallazgos de auditoría;
- observaciones del profesor guía;
- componentes técnicos útiles, siempre que sean revalidados;
- historial Git y evidencias históricas.

## 5. Qué se mueve a legacy

El movimiento físico de archivos a `legacy/proyecto-v1/` fue aprobado por el responsable del proyecto y ejecutado el 2026-07-08. Se preservó el material histórico sin eliminación destructiva.

Se trasladaron a legacy:

- código y documentación previa que no estaba trazada a requisitos V2;
- documentos con afirmaciones pendientes de revalidación;
- evidencias antiguas no normalizadas;
- scripts o adaptadores previos;
- material usado en defensa previa que requiere corrección o contextualización;
- cambios técnicos locales no aprobados como baseline V2.

## 6. Qué se reconstruye

La V2 reconstruirá gradualmente:

- API;
- dashboard;
- Docker;
- observability core;
- monitor sintético;
- remediación segura;
- continuidad operacional;
- integración/adaptador Rocketbot;
- persistencia MySQL;
- pruebas automatizadas;
- evidencias con hash;
- documentación SGDP;
- guía de demo y límites reales del prototipo.

## 7. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---:|---|
| Confundir V1 histórica con V2 oficial | Alto | Separar README, auditoría, legacy y raíz `v2/`. |
| Declarar capacidades no demostradas | Alto | Exigir requisito, diseño, prueba y evidencia antes de incorporar. |
| Perder trazabilidad histórica | Alto | No borrar ni sobrescribir archivos históricos. |
| Arrastrar desorden técnico a V2 | Medio | Migración gradual mediante matriz de herencia. |
| Generar ramas/tags sin acuerdo | Medio | Requerir confirmación antes de acciones Git estructurales. |

## 8. Criterios de aceptación

La reconstrucción V2 será aceptable si:

- nada histórico se pierde;
- existe separación clara entre V1 y V2;
- `v2/` mantiene una raíz limpia;
- `legacy/` queda claramente identificado;
- no se declaran capacidades no demostradas;
- el título oficial y objetivos oficiales se mantienen;
- el ciclo metodológico y el flujo operacional no se confunden;
- existe matriz de herencia;
- existe acta de decisión V2;
- cada componente que ingrese a V2 cumple requisito, diseño, implementación, prueba, evidencia y documentación.

## 9. Relación con observaciones del profesor

La V2 responde directamente a las observaciones del profesor guía, especialmente en los puntos donde la documentación o la defensa previa pudieron sugerir capacidades que no estaban implementadas o probadas de forma suficiente.

La reconstrucción no busca ocultar esas inconsistencias, sino convertirlas en hallazgos gestionados y en criterios explícitos de aceptación para la nueva línea técnica.

## 10. Decisiones pendientes de aprobación humana

- Crear rama `rebuild/v2`.
- Publicar tag histórico `BL-HIST-001` si se decide subirlo a GitHub.
- Crear rama de preservación `legacy/proyecto-v1` si se decide mantenerla remotamente.
- Registrar formalmente nuevos documentos en DOC-000.
- Definir qué componentes V1 serán reimplementados primero en V2.
