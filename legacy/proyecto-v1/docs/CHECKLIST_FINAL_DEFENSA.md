# Checklist de defensa Fase 1

- [ ] Los cuatro servicios base están `healthy`.
- [ ] API v2 y MySQL responden; dashboard muestra los mismos datos.
- [ ] Heartbeat crea servicios y métricas de disponibilidad.
- [ ] Se demuestra una falla, su regla, evento, evidencia y hash.
- [ ] La acción usa lista blanca, se revalida y actualiza MTTR.
- [ ] Un segundo intento queda bloqueado por límite o cooldown.
- [ ] Una acción riesgosa escala sin mutar el host.
- [ ] El respaldo no estaba activo antes de la contingencia.
- [ ] Rocketbot Studio muestra la invocación y el código final.
- [ ] Las 13 pruebas pasan frente a la comisión.
- [ ] Las limitaciones de `FASE1_IMPLEMENTACION.md` se explican sin ocultarlas.
