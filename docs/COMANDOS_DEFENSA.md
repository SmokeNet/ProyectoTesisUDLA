# Comandos de defensa

Ejecutar desde la raíz:

```powershell
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/health/db
Invoke-RestMethod 'http://127.0.0.1:8000/incidentes?limit=20&offset=0'
```

```powershell
.\venv\Scripts\python.exe playwright-monitor\monitor.py
.\venv\Scripts\python.exe remediacion\remediador.py
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
.\rocketbot\ejecutar_flujo_completo.bat
```

```powershell
python -m unittest discover -s tests -v
docker compose -f docker/docker-compose.yml config --quiet
```

La creación autenticada y la consulta SQL sin secretos visibles están documentadas
en el README. No coloque contraseñas como argumentos de consola ni las copie a las
diapositivas.
