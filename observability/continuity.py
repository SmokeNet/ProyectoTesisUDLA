"""Caso de uso de continuidad posterior a una remediacion fallida."""

import logging
from dataclasses import asdict, replace

from .config import Settings
from .domain import Observation
from .monitoring import SyntheticProbe
from .orchestrator import ObservationOrchestrator

LOGGER = logging.getLogger(__name__)


class ContinuityManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.orchestrator = ObservationOrchestrator(settings)

    def run(self) -> int:
        result = self.orchestrator.run(notify_on_failure=False)
        if result == 0:
            return 0
        observation = self.orchestrator.last_observation
        recoverable_outage = observation and (
            observation.port_open is False
            or observation.error_kind in {"timeout", "service_stopped", "application"}
            or (observation.http_status is not None and observation.http_status >= 500)
        )
        if not recoverable_outage:
            self.orchestrator.notifier.send(
                "Alerta: incidente no remediable automaticamente",
                "La politica exige escalamiento especializado.",
            )
            LOGGER.error("Contingencia no aplica; el incidente requiere escalamiento especializado")
            return 2

        backup_settings = replace(
            self.settings,
            monitored_url="http://127.0.0.1:8081/",
            service_name="sitio-respaldo",
            expected_text="Sitio de respaldo operativo",
        )
        backup_probe = SyntheticProbe(backup_settings)
        fallback = self.orchestrator.remediation.execute(
            "activate_backup",
            "sitio-respaldo",
            observation if observation else Observation("sitio-vigilado", "localhost", ""),
            backup_probe.observe,
            attempt_count=1,
        )
        event_id = self.orchestrator.primary_event_id
        if event_id:
            artifact = self.orchestrator.evidence.write_json(
                event_id,
                asdict(fallback),
                "continuidad",
            )
            self.orchestrator._safe_api(
                self.orchestrator.api.create_evidence,
                event_id,
                {
                    "kind": artifact.kind,
                    "path": str(artifact.path),
                    "sha256": artifact.sha256,
                    "content_type": artifact.content_type,
                },
            )
            notification = self.orchestrator.notifier.send(
                "Contingencia activada" if fallback.success else "Fallo critico de continuidad",
                fallback.reason,
            )
            notification_artifact = self.orchestrator.evidence.write_json(
                event_id,
                notification,
                "notificacion_continuidad",
            )
            self.orchestrator._safe_api(
                self.orchestrator.api.create_evidence,
                event_id,
                {
                    "kind": notification_artifact.kind,
                    "path": str(notification_artifact.path),
                    "sha256": notification_artifact.sha256,
                    "content_type": notification_artifact.content_type,
                },
            )
            self.orchestrator._safe_api(
                self.orchestrator.api.create_remediation,
                event_id,
                {
                    "strategy": fallback.strategy,
                    "attempt": 2,
                    "attempted": fallback.attempted,
                    "success": fallback.success,
                    "escalated": fallback.escalated,
                    "reason": fallback.reason,
                    "action": fallback.action,
                    "duration_ms": fallback.duration_ms,
                    "state_before": fallback.state_before,
                    "state_after": fallback.state_after,
                },
            )
        return 0 if fallback.success else 2
