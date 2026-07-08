# Continuidad operacional

El adaptador ejecuta el motor de observabilidad y remediación. Si una caída recuperable
persiste, activa `sitio-respaldo` mediante el perfil Compose `continuidad`, lo valida,
registra un segundo intento y genera alerta SMTP o evidencia de alerta simulada.

```powershell
.\rocketbot\ejecutar_continuidad.bat
```

DNS, SSL, disco y otros incidentes especializados no activan automáticamente el
respaldo: se escalan porque requieren un runbook distinto.
