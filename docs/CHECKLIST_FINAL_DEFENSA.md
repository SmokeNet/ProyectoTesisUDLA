# Checklist de defensa

- [ ] Docker Desktop activo y `docker compose ... ps` con servicios `healthy`.
- [ ] `GET /health/db` retorna HTTP 200; mostrar también un 503 controlado.
- [ ] POST sin clave retorna 401 y POST válido retorna 201.
- [ ] MySQL persiste tras recrear la API.
- [ ] Playwright demuestra éxito, fallo de contenido y captura PNG.
- [ ] Dashboard muestra total, últimos eventos y error de conexión comprensible.
- [ ] Caída del principal ejecuta recuperación real y segunda validación.
- [ ] Fallo de recuperación activa exclusivamente el perfil de respaldo.
- [ ] Evidencias JSON no contienen secretos y tienen inicio, fin, pasos y códigos.
- [ ] Correo se presenta como real solo con evidencia de entrega; si no, como simulado.
- [ ] Rocketbot Studio muestra la acción que invoca el `.bat`; el adaptador solo no
  demuestra la interfaz RPA propietaria.
- [ ] Ejecutar `python -m unittest discover -s tests -v` frente a la comisión.
- [ ] No editar credenciales, borrar volúmenes ni improvisar cambios durante la demo.
