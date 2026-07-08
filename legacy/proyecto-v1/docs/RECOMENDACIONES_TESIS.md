# Recomendaciones para el informe de tesis

Presentar el aporte como un **prototipo avanzado de observabilidad sintética y respuesta defensiva segura**, destinado a disminuir MTTD/MTTR y mejorar trazabilidad. No afirmar prevención total.

## Estructura sugerida

1. Problema: detección tardía, respuesta manual y evidencia dispersa.
2. Objetivo: correlacionar disponibilidad, integridad, seguridad básica y continuidad.
3. Arquitectura: gateway, monitor, reglas, API, MySQL, evidencias y remediador.
4. Metodología: escenarios controlados y criterios de aceptación.
5. Resultados: detección, MTTD, MTTR, disponibilidad y remediaciones.
6. Seguridad: mínimo privilegio, allowlist, cooldown, revalidación y escalamiento.
7. Limitaciones y amenazas a la validez.
8. Trabajo futuro: WAF/OWASP CRS, Redis, OpenTelemetry, SIEM y WORM.

## Evidencia cuantitativa

- 20 pruebas automatizadas;
- matriz escenario → regla → evidencia → respuesta;
- tiempos de detección y recuperación;
- tasa de remediación exitosa;
- verificación independiente de SHA-256;
- falsos positivos y límites documentados.

Preguntas clave: esto no es un WAF porque carece de catálogo industrial y operación distribuida; las remediaciones se limitan mediante allowlist, intentos, cooldown y revalidación; el hash demuestra integridad, no autoría; ante incertidumbre el sistema registra y escala.
