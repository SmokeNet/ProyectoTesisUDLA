# Integración Rocketbot

`ejecutar_flujo_completo.bat` es el punto de entrada para Rocketbot Studio. Invoca
el adaptador Python, que levanta Compose, valida API/sitio, sirve y abre el dashboard,
ejecuta Playwright, consulta incidentes y delega la decisión al gestor de continuidad.

```bat
rocketbot\ejecutar_flujo_completo.bat
```

Cada subproceso tiene timeout, captura código/stdout/stderr y contribuye al estado
final. Se crea `evidencias/rocketbot/evidencia_rocketbot_*.json`. La evidencia prueba
la ejecución del adaptador; para demostrar Rocketbot Studio debe conservarse además
una captura o exportación real del robot visual configurado para ejecutar el `.bat`.

El flujo anterior ejecutaba una comprobación Paramiko incondicional que solo hacía
`echo`; fue retirada porque no representaba auto-remediación. La recuperación actual
se ejecuta condicionalmente y recrea el servicio objetivo mediante Compose.
