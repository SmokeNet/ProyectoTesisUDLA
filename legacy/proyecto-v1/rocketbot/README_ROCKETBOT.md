# Integración Rocketbot

Rocketbot Studio debe ejecutar `rocketbot/ejecutar_flujo_completo.bat`. El adaptador:

1. levanta Compose;
2. espera readiness API/MySQL;
3. registra heartbeat de Rocketbot;
4. abre el dashboard opcionalmente;
5. ejecuta observación, reglas, evidencia, remediación y continuidad;
6. propaga el código final y genera evidencia con UUID.

La lógica permanece en `observability/`, donde puede probarse sin la interfaz
propietaria. Para la defensa se requiere además captura o exportación real del robot
visual; ejecutar Python por sí solo no demuestra integración con Rocketbot Studio.
