# Continuidad operacional

El gestor valida el principal, registra la falla, recrea el servicio mediante Docker
Compose y vuelve a validarlo. Solo si continúa caído inicia el perfil `continuidad`,
comprueba el respaldo, notifica por SMTP (si está configurado) y genera JSON.

```powershell
.\venv\Scripts\python.exe continuidad\gestor_continuidad.py
```

Variables opcionales: `INTENTOS_VALIDACION`, `SEGUNDOS_ENTRE_INTENTOS`,
`TIMEOUT_HTTP`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
`SMTP_FROM` y `SMTP_TO`. La clave de escritura se carga desde `docker/.env` para la
ejecución local. Sin SMTP se registra una notificación simulada, claramente marcada;
eso no constituye evidencia de entrega de correo.
