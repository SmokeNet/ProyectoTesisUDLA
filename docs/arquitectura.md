# Arquitectura Fase 1

```mermaid
flowchart LR
    R["Rocketbot / Scheduler"] --> O["ObservationOrchestrator"]
    O --> P["SyntheticProbe"]
    P --> W["Web / DNS / TLS / TCP"]
    P --> I["CPU / RAM / disco / Docker / SSH"]
    O --> E["RuleEngine / 23 reglas"]
    E --> B["Bitácora operacional"]
    B --> A["FastAPI v2"]
    A --> D[("MySQL")]
    O --> V["EvidenceStore"]
    V --> F["JSON / HTML / PNG / SHA-256"]
    O --> M["RemediationEngine"]
    M --> C["Compose / lista blanca"]
    C --> P
    M --> X["Continuidad o escalamiento"]
    Q["Dashboard"] --> A
```

## Capas

1. **Dominio:** observaciones, detecciones, eventos y resultados, sin FastAPI.
2. **Aplicación:** orquestación, continuidad y políticas de remediación.
3. **Infraestructura:** Playwright, psutil, sockets, Docker, HTTP, evidencia y MySQL.
4. **Adaptadores:** API, dashboard, CLI, `.bat` y Rocketbot Studio.

La lógica privilegiada vive fuera de los contenedores para evitar montar el socket
Docker. Las reglas pueden detectar múltiples fallas en una observación y la estrategia
de mayor severidad gobierna la acción automática. Todas las detecciones conservan su
propio evento y evidencia.
