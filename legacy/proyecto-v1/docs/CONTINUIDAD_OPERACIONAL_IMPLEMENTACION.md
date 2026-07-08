# Continuidad operacional Fase 1

La continuidad es una política posterior a detección, remediación y revalidación.
Solo las caídas recuperables del servicio web pueden activar el perfil de respaldo.
DNS, SSL, seguridad y recursos del host se escalan a su runbook correspondiente.

```text
observar -> detectar -> registrar -> remediar -> revalidar
  ├─ recuperado: cerrar y calcular MTTR
  ├─ caída persistente aplicable: activar respaldo -> validar -> alertar
  └─ incidente especializado: escalar -> alertar
```

La activación, verificación y notificación quedan asociadas al UUID del evento como
intentos y evidencias independientes.
