"""Caso de uso principal: observar, detectar, evidenciar, remediar y revalidar."""

import logging
from dataclasses import asdict
from datetime import datetime, timezone

from .api_client import ApiClient, ApiClientError
from .config import Settings
from .domain import FinalStatus, OperationalEvent, RemediationResult, Severity
from .evidence import EvidenceStore
from .monitoring import SyntheticProbe
from .notifications import Notifier
from .remediation import RemediationEngine, RemediationPolicy
from .rules import RuleEngine

LOGGER = logging.getLogger(__name__)
SEVERITY_RANK = {Severity.INFO: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3, Severity.CRITICAL: 4}


class ObservationOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.probe = SyntheticProbe(settings)
        self.rules = RuleEngine.from_file(settings.rules_file)
        self.rules.config.setdefault("thresholds", {})["latency_ms"] = (
            settings.latency_threshold_ms
        )
        self.evidence = EvidenceStore(settings.evidence_dir)
        self.api = ApiClient(settings.api_base_url, settings.api_write_key)
        self.remediation = RemediationEngine(
            settings.compose_file,
            RemediationPolicy(settings.max_remediation_attempts, settings.remediation_cooldown_seconds),
        )
        self.notifier = Notifier(settings)
        self.last_observation = None
        self.primary_event_id: str | None = None

    def _safe_api(self, operation, *args):
        try:
            return operation(*args)
        except ApiClientError as error:
            LOGGER.error("API no disponible: %s", error)
            return None

    def _publish_metrics(self, observation) -> None:
        values = {
            "latency_ms": (observation.latency_ms, "ms"),
            "cpu_percent": (observation.cpu_percent, "percent"),
            "memory_percent": (observation.memory_percent, "percent"),
            "disk_percent": (observation.disk_percent, "percent"),
            "ssl_days_remaining": (observation.ssl_days_remaining, "days"),
        }
        for name, (value, unit) in values.items():
            if value is not None:
                self._safe_api(
                    self.api.create_metric,
                    {"service": observation.service, "name": name, "value": value, "unit": unit, "labels": {}},
                )

    def _persist_event(self, event, payload, artifacts) -> bool:
        created = self._safe_api(self.api.create_event, payload)
        if not created:
            return False
        for artifact in artifacts:
            self._safe_api(
                self.api.create_evidence,
                event.id,
                {
                    "kind": artifact.kind,
                    "path": str(artifact.path),
                    "sha256": artifact.sha256,
                    "content_type": artifact.content_type,
                },
            )
        return True

    def _publish_components(self, observation) -> None:
        components = {
            "docker": observation.docker_ok,
            "api": observation.api_ok,
            "mysql": observation.database_ok,
            "playwright": observation.error_detail is None
            or "Playwright no disponible" not in observation.error_detail,
            "ssh": observation.ssh_ok,
        }
        for name, healthy in components.items():
            if healthy is None:
                continue
            self._safe_api(
                self.api.heartbeat,
                {
                    "service": name,
                    "service_type": "plataforma",
                    "server": observation.server,
                    "target": name,
                    "status": "saludable" if healthy else "caido",
                    "timestamp": observation.observed_at.isoformat(),
                },
            )

    def run(self, notify_on_failure: bool = True) -> int:
        observed_started = datetime.now(timezone.utc)
        observation = self.probe.observe()
        self.last_observation = observation
        detections = self.rules.evaluate(observation)
        critical = any(detection.severity == Severity.CRITICAL for detection in detections)
        status = "saludable" if not detections else "caido" if critical else "degradado"
        self._safe_api(
            self.api.heartbeat,
            {
                "service": observation.service,
                "service_type": "web",
                "server": observation.server,
                "target": observation.target,
                "status": status,
                "timestamp": observation.observed_at.isoformat(),
                "latency_ms": observation.latency_ms,
            },
        )
        self._publish_metrics(observation)
        self._publish_components(observation)
        if not detections:
            LOGGER.info("Observacion saludable para %s", observation.service)
            return 0

        events: list[tuple[OperationalEvent, object, dict, list, bool]] = []
        detection_time = (datetime.now(timezone.utc) - observed_started).total_seconds() * 1000
        for detection in detections:
            event = OperationalEvent(
                server=observation.server,
                service=observation.service,
                incident_type=detection.incident_type,
                level="operacional",
                severity=detection.severity,
                cause=detection.cause,
                diagnosis=detection.diagnosis,
                final_status=FinalStatus.OPEN,
                observation=observation.as_dict(),
            )
            payload = event.as_dict()
            payload["detection_time_ms"] = detection_time
            json_artifact = self.evidence.write_json(event.id, payload)
            html_artifact = self.evidence.write_html_report(event.id, payload)
            artifacts = [json_artifact, html_artifact]
            if self.probe.last_screenshot:
                artifacts.append(self.evidence.register_file("screenshot", self.probe.last_screenshot, "image/png"))
            event.evidence_hash = json_artifact.sha256
            event.evidence_path = str(json_artifact.path)
            payload = event.as_dict()
            payload["detection_time_ms"] = detection_time
            persisted = self._persist_event(event, payload, artifacts)
            events.append((event, detection, payload, artifacts, persisted))

        primary = max(events, key=lambda item: SEVERITY_RANK[item[1].severity])
        primary_event, primary_detection = primary[0], primary[1]
        self.primary_event_id = primary_event.id
        if primary_detection.strategy in self.remediation.MUTATING_STRATEGIES:
            confirmation = self.probe.observe()
            confirmed_types = {
                detection.incident_type for detection in self.rules.evaluate(confirmation)
            }
        else:
            confirmation = observation
            confirmed_types = {primary_detection.incident_type}
        if primary_detection.incident_type not in confirmed_types:
            result = RemediationResult(
                strategy=primary_detection.strategy,
                attempted=False,
                success=True,
                escalated=False,
                reason="falla transitoria ausente en la confirmacion",
                action="ninguna",
                duration_ms=0,
                state_before=observation.as_dict(),
                state_after=confirmation.as_dict(),
            )
        else:
            result = self.remediation.execute(
                primary_detection.strategy,
                observation.service,
                confirmation,
                self.probe.observe,
            )
        if result.success:
            for event, _, payload, artifacts, persisted in events:
                if not persisted:
                    self._persist_event(event, payload, artifacts)
        remediation_artifact = self.evidence.write_json(
            primary_event.id,
            asdict(result),
            "remediacion",
        )
        self._safe_api(
            self.api.create_evidence,
            primary_event.id,
            {
                "kind": remediation_artifact.kind,
                "path": str(remediation_artifact.path),
                "sha256": remediation_artifact.sha256,
                "content_type": remediation_artifact.content_type,
            },
        )
        self._safe_api(
            self.api.create_remediation,
            primary_event.id,
            {
                "strategy": result.strategy,
                "attempt": 1,
                "attempted": result.attempted,
                "success": result.success,
                "escalated": result.escalated,
                "reason": result.reason,
                "action": result.action,
                "duration_ms": result.duration_ms,
                "state_before": result.state_before,
                "state_after": result.state_after,
            },
        )
        if result.escalated and notify_on_failure:
            notification = self.notifier.send(
                f"Alerta critica: {primary_detection.incident_type}",
                f"Servicio: {observation.service}\nDiagnostico: {primary_detection.diagnosis}\n"
                f"Remediacion: {result.reason}",
            )
            notification_artifact = self.evidence.write_json(
                primary_event.id,
                notification,
                "notificacion",
            )
            self._safe_api(
                self.api.create_evidence,
                primary_event.id,
                {
                    "kind": notification_artifact.kind,
                    "path": str(notification_artifact.path),
                    "sha256": notification_artifact.sha256,
                    "content_type": notification_artifact.content_type,
                },
            )
        return 0 if result.success else 2 if result.escalated else 1
