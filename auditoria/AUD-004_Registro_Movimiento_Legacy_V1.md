# AUD-004 — Registro de Movimiento Legacy V1

## 1. Identificación

- Código: AUD-004
- Nombre: Registro de Movimiento Legacy V1
- Estado: Ejecutado
- Fecha: 2026-07-08
- Repositorio: `C:\Users\bryan\OneDrive\Desktop\Nuevo Proyecto\prototipo`
- Tag histórico local creado: `BL-HIST-001`
- Commit referenciado por el tag: `4d0fb0cf753cb6bb1338e897d834a8ea4458c89c`

## 2. Decisión ejecutada

Se movió físicamente el material histórico de la V1 a:

`legacy/proyecto-v1/`

El objetivo fue dejar visible una raíz limpia para la reconstrucción V2, manteniendo trazabilidad histórica y evitando eliminación destructiva.

## 3. Elementos conservados en la raíz

- `.git/`
- `.gitignore`
- `README.md`
- `auditoria/`
- `docs/`
- `legacy/`
- `v2/`

## 4. Elementos movidos a legacy

- `.dockerignore`
- `requirements.txt`
- `requirements-api.txt`
- `api/`
- `config/`
- `continuidad/`
- `dashboard/`
- `demo/`
- `docker/`
- `evidencias/`
- `observability/`
- `playwright-monitor/`
- `remediacion/`
- `rocketbot/`
- `security-gateway/`
- `Sitio-prueba/`
- `Sitio-respaldo/`
- `tests/`
- `venv/`
- documentación histórica ubicada directamente en `docs/`

## 5. Elementos no movidos

- Estructura SGDP nueva dentro de `docs/`.
- Documentos de auditoría nuevos.
- Raíz limpia `v2/`.
- Carpeta `legacy/` y sus README.

## 6. Advertencia

Este movimiento no aprueba automáticamente el contenido de V1 como parte de la V2. Todo componente histórico que quiera reingresar a `v2/` debe cumplir la checklist de entrada definida en:

`v2/CHECKLIST_ENTRADA_COMPONENTES.md`

## 7. Estado Git posterior esperado

Git mostrará eliminaciones de las rutas antiguas y archivos nuevos bajo `legacy/proyecto-v1/`. Esa situación es normal antes de hacer `git add`, porque Git todavía no ha inferido las renombraciones.

No se realizó commit ni push.
