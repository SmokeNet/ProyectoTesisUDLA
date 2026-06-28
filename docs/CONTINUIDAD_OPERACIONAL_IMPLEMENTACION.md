# Implementación de continuidad operacional

```text
validar principal
  ├─ disponible -> registrar estado y terminar
  └─ caído -> registrar -> recrear servicio permitido -> volver a validar
       ├─ recuperado -> registrar resuelto y notificar
       └─ caído -> iniciar respaldo (perfil continuidad) -> validar
            ├─ disponible -> contingencia activa y notificación
            └─ caído -> error crítico y escalamiento manual
```

La recuperación usa argumentos estructurados de `subprocess` (`shell=False` por
defecto) y una lista blanca; no acepta un comando de remediación aportado por una
solicitud HTTP. El sitio de respaldo no forma parte del arranque normal. Cada rama
terminal genera evidencia JSON y la API recibe estados normalizados.

El correo es real únicamente cuando SMTP está configurado y el resultado es `ok`.
El estado `simulada` significa que existe trazabilidad académica de la intención, no
que un destinatario haya recibido el mensaje.
