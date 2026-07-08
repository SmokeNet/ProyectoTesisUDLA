# Comandos de defensa Fase 1

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/services
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/events?limit=20'
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/metrics/summary?hours=24'
.\rocketbot\ejecutar_monitor.bat
.\rocketbot\ejecutar_flujo_completo.bat
python -m unittest discover -s tests -v
```

Dashboard: `http://127.0.0.1:5500/`. No mostrar `docker/.env` ni contraseñas durante
la presentación.
