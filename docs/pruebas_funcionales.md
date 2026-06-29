# Pruebas funcionales Fase 1

## Automatizadas y ejecutadas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q api observability playwright-monitor remediacion continuidad rocketbot tests
docker compose -f docker/docker-compose.yml config --quiet
```

Las 13 pruebas cubren 23 reglas, fallas simultáneas, ausencia de falsos positivos sin
telemetría, escalamiento SSL/DNS, lista blanca, no uso de shell, revalidación,
cooldown, límite de intentos y evidencia con hash/escape HTML.

## Matriz end-to-end obligatoria antes de defensa

1. Arranque y health de API/MySQL/dashboard/sitio.
2. Heartbeat saludable y disponibilidad mayor que cero.
3. HTTP 500, 404, timeout, DNS inválido y contenido modificado.
4. Latencia sobre umbral y recursos CPU/RAM/disco inyectados en ambiente aislado.
5. Contenedor detenido, recuperación, segunda validación y MTTR.
6. Remediación fallida, segundo intento bloqueado/cooldown y escalamiento.
7. Activación de respaldo únicamente después de recuperación fallida.
8. JSON, HTML, captura y hash relacionados al mismo UUID en MySQL.
9. Dashboard actualizado con eventos, servicios, MTTD, MTTR y tendencia.
10. Rocketbot Studio invocando el adaptador y propagando el código final.

Esta matriz no fue ejecutada en la estación actual porque Docker Desktop no tiene
daemon activo y la instalación de dependencias no completó la descarga.
