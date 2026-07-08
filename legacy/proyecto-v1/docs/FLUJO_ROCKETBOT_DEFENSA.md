# Flujo Rocketbot para defensa

Configure en Rocketbot Studio un robot `Robot_Observabilidad_Tesis` con una acción de
comando externo que ejecute, desde la raíz del repositorio:

```bat
rocketbot\ejecutar_flujo_completo.bat
```

## Secuencia observable

1. Compose levanta API, MySQL y sitio principal.
2. Se valida readiness y sitio.
3. Se inicia/abre el dashboard.
4. Playwright comprueba HTTP y contenido.
5. Se consultan los eventos persistidos.
6. El gestor decide si remediar y, solo si corresponde, activar respaldo.
7. Se genera evidencia JSON y se propaga un código distinto de cero ante errores.

## Evidencia mínima

- captura del robot visual y su log;
- `docker compose ps` con healthchecks;
- respuestas 401, 201 y 200/503 de la API;
- captura del monitor en escenario fallido;
- evento persistido y dashboard actualizado;
- JSON final sin credenciales;
- prueba de recuperación o de contingencia, indicando cuál se ejecutó.

La ruta se resuelve desde el `.bat`; no se debe configurar una ruta absoluta personal.
Rocketbot es la capa de orquestación visual, mientras Python contiene lógica testeable
y auditable. Esta separación es deliberada y evita esconder reglas en acciones RPA.
