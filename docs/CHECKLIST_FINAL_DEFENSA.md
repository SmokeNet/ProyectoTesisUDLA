# Checklist Final de Defensa

## Validacion tecnica

| Punto | Comando | Evidencia esperada |
| --- | --- | --- |
| Docker activo | `docker compose -f docker/docker-compose.yml ps` | API, MySQL, sitio vigilado y SSH en estado `Up` |
| API activa | `curl http://127.0.0.1:8000/` | JSON con `estado: ok` |
| API usando MySQL | `curl http://127.0.0.1:8000/health/db` | `engine=mysql` |
| MySQL con tabla incidentes | `docker exec -it observabilidad-mysql mysql -u observabilidad -pobservabilidad123 observabilidad -e "SELECT * FROM incidentes ORDER BY id DESC LIMIT 5;"` | Registros recientes |
| Sitio vigilado OK | `curl http://127.0.0.1:8080/` | Texto `Servicio web vigilado operativo` |
| Playwright OK | `$env:URL_MONITOREADA="http://127.0.0.1:8080/"; .\venv\Scripts\python.exe playwright-monitor\monitor.py` | Estado OK y latencia |
| Playwright ERROR | `$env:URL_MONITOREADA="http://dominio-invalido-tesis.local/"; .\venv\Scripts\python.exe playwright-monitor\monitor.py` | Incidente registrado en API |
| Dashboard visible | `cd dashboard; ..\venv\Scripts\python.exe -m http.server 5500` | Tabla de incidentes en `http://127.0.0.1:5500/` |
| Paramiko SSH real | `.\venv\Scripts\python.exe remediacion\remediador.py` | Registro `remediacion-paramiko` en API |
| Rocketbot | `.\rocketbot\ejecutar_flujo_completo.bat` | Evidencia JSON en `evidencias\rocketbot` |

## Demo de 5 minutos

1. Mostrar `docker compose -f docker/docker-compose.yml ps`.
2. Mostrar `/health/db` con `engine=mysql`.
3. Abrir `http://127.0.0.1:8080/` y explicar sitio vigilado.
4. Ejecutar Playwright OK.
5. Detener `sitio-vigilado` y ejecutar Playwright ERROR.
6. Abrir dashboard y mostrar el incidente.
7. Ejecutar `remediacion/remediador.py` contra SSH Docker.
8. Ejecutar `rocketbot/ejecutar_flujo_completo.bat` y abrir la evidencia JSON.

## No tocar durante la defensa

- No cambiar credenciales en vivo.
- No borrar el volumen MySQL salvo que se quiera reiniciar datos.
- No cambiar puertos `8000`, `8080`, `3306`, `2222` o `5500`.
- No cerrar Docker Desktop.
- No ejecutar `docker compose down -v` durante la demo.
