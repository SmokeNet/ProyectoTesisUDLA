# Limitaciones y riesgos reales

- No es invulnerable ni garantiza detección total.
- No sustituye WAF, SIEM, EDR, IDS/IPS ni SOC.
- No analiza reputación IP ni ataques distribuidos.
- No termina TLS; en producción requiere reverse proxy administrado.
- Los contadores no se comparten entre réplicas y el bloqueo se pierde al reiniciar.
- Las expresiones regulares básicas admiten falsos positivos y negativos.
- SHA-256 detecta alteración, pero no aporta por sí solo autoría o cadena de custodia.
- La clave en variables de entorno debe migrarse a un gestor de secretos.

| Riesgo | Mitigación actual | Evolución productiva |
|---|---|---|
| Evasión de firmas | correlación y escalamiento | WAF con OWASP CRS |
| Flood distribuido | límite por origen | CDN/DDoS y Redis |
| Pérdida de estado | bitácora MySQL | Redis/cluster con TTL |
| Manipulación de evidencia | SHA-256 | WORM, firma y timestamp |
| Secreto en runtime | `.env` ignorado | Vault/KMS y rotación |
| Falla del gateway | restart policy | réplicas y balanceador |

Las únicas acciones automáticas son reinicio controlado, activación de respaldo, rate limit y bloqueo temporal local. Borrado de datos, firewall permanente, comandos arbitrarios y explotación quedan fuera de alcance.
