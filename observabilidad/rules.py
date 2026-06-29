"""Motor configurable de deteccion sin dependencias de transporte."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .domain import Detection, Observation, Severity


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    enabled: bool
    incident_type: str
    severity: Severity
    strategy: str
    predicate: Callable[[Observation, dict[str, Any]], bool]
    cause: Callable[[Observation], str]
    diagnosis: Callable[[Observation], str]


def _is_false(field: str) -> Callable[[Observation, dict[str, Any]], bool]:
    return lambda observation, _: getattr(observation, field) is False


def _above(field: str, threshold_key: str) -> Callable[[Observation, dict[str, Any]], bool]:
    return lambda observation, config: (
        getattr(observation, field) is not None
        and float(getattr(observation, field)) >= float(config[threshold_key])
    )


def _http_range(start: int, end: int) -> Callable[[Observation, dict[str, Any]], bool]:
    return lambda observation, _: (
        observation.http_status is not None and start <= observation.http_status <= end
    )


class RuleEngine:
    """Evalua todas las reglas habilitadas y conserva detecciones simultaneas."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.rules = self._build_rules()

    @classmethod
    def from_file(cls, path: Path) -> "RuleEngine":
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)

    def _enabled(self, rule_id: str) -> bool:
        return bool(self.config.get("enabled", {}).get(rule_id, True))

    def _rule(
        self,
        rule_id: str,
        incident_type: str,
        severity: Severity,
        strategy: str,
        predicate: Callable[[Observation, dict[str, Any]], bool],
        cause: str,
        diagnosis: str,
    ) -> Rule:
        return Rule(
            id=rule_id,
            enabled=self._enabled(rule_id),
            incident_type=incident_type,
            severity=severity,
            strategy=strategy,
            predicate=predicate,
            cause=lambda _: cause,
            diagnosis=lambda observation: (
                f"{diagnosis} Detalle: {observation.error_detail or 'sin detalle'}"
            ),
        )

    def _build_rules(self) -> list[Rule]:
        rules = [
            self._rule(
                "http_4xx", "http_4xx", Severity.MEDIUM, "validate_deployment",
                _http_range(400, 499), "Respuesta HTTP cliente", "Revisar ruta y despliegue.",
            ),
            self._rule(
                "http_5xx", "http_5xx", Severity.HIGH, "restart_service",
                _http_range(500, 599), "Respuesta HTTP servidor",
                "La aplicacion fallo al procesar la solicitud.",
            ),
            self._rule(
                "timeout", "timeout", Severity.HIGH, "restart_service",
                lambda o, _: o.error_kind == "timeout", "Tiempo de espera agotado",
                "El servicio excedio el timeout configurado.",
            ),
            self._rule(
                "dns", "dns_caido", Severity.CRITICAL, "escalate", _is_false("dns_ok"),
                "Resolucion DNS fallida", "No se pudo resolver el host.",
            ),
            self._rule(
                "ssl_invalid", "ssl_invalido", Severity.CRITICAL, "escalate",
                _is_false("ssl_valid"), "Certificado SSL invalido",
                "La cadena o vigencia TLS no es valida.",
            ),
            self._rule(
                "ssl_expiring", "ssl_por_expirar", Severity.HIGH, "escalate",
                lambda o, c: o.ssl_days_remaining is not None
                and o.ssl_days_remaining <= int(c["ssl_expiry_days"]),
                "Certificado proximo a expirar", "Renovar certificado antes del vencimiento.",
            ),
            self._rule(
                "latency", "latencia_elevada", Severity.MEDIUM, "restart_service",
                _above("latency_ms", "latency_ms"), "Latencia sobre umbral",
                "La respuesta excedio el objetivo operacional.",
            ),
            self._rule(
                "port", "puerto_cerrado", Severity.HIGH, "start_service",
                _is_false("port_open"), "Puerto de servicio cerrado",
                "No fue posible establecer TCP.",
            ),
            self._rule(
                "service", "servicio_detenido", Severity.HIGH, "start_service",
                lambda o, _: o.error_kind == "service_stopped", "Servicio detenido",
                "El proceso esperado no responde.",
            ),
            self._rule(
                "container", "contenedor_detenido", Severity.HIGH, "start_service",
                _is_false("container_running"), "Contenedor detenido",
                "Docker informa que el contenedor no esta activo.",
            ),
            self._rule(
                "application", "error_aplicacion", Severity.HIGH, "restart_service",
                lambda o, _: o.error_kind == "application", "Error de aplicacion",
                "Se detecto una excepcion funcional.",
            ),
            self._rule(
                "page_changed", "pagina_modificada", Severity.MEDIUM, "escalate",
                lambda o, _: o.content_changed is True, "Hash de contenido modificado",
                "La pagina difiere de la linea base.",
            ),
            self._rule(
                "content", "contenido_inesperado", Severity.HIGH, "validate_deployment",
                _is_false("content_expected"), "Contenido esperado ausente",
                "HTTP respondio, pero la validacion semantica fallo.",
            ),
            self._rule(
                "login", "error_login", Severity.HIGH, "escalate", _is_false("login_ok"),
                "Login sintetico fallido", "No se completo el flujo de autenticacion.",
            ),
            self._rule(
                "database", "base_datos_caida", Severity.CRITICAL, "start_mysql",
                _is_false("database_ok"), "Base de datos no disponible",
                "La consulta de readiness fallo.",
            ),
            self._rule(
                "api", "api_caida", Severity.CRITICAL, "restart_api", _is_false("api_ok"),
                "API no disponible", "El endpoint de readiness no respondio.",
            ),
            self._rule(
                "critical_resource", "recurso_critico_no_disponible", Severity.CRITICAL,
                "escalate", _is_false("critical_resources_ok"), "Recurso critico ausente",
                "Un recurso requerido por la pagina no cargo.",
            ),
            self._rule(
                "cpu", "cpu_elevada", Severity.HIGH, "escalate",
                _above("cpu_percent", "cpu_percent"), "CPU sobre umbral",
                "Uso sostenido elevado de CPU.",
            ),
            self._rule(
                "memory", "memoria_elevada", Severity.HIGH, "escalate",
                _above("memory_percent", "memory_percent"), "Memoria sobre umbral",
                "Uso de memoria sobre el limite.",
            ),
            self._rule(
                "disk", "disco_elevado", Severity.CRITICAL, "escalate",
                _above("disk_percent", "disk_percent"), "Disco sobre umbral",
                "No se elimina informacion automaticamente.",
            ),
            self._rule(
                "connections", "conexiones_saturadas", Severity.HIGH, "escalate",
                _above("connections_percent", "connections_percent"),
                "Pool de conexiones saturado", "La ocupacion excede el limite.",
            ),
            self._rule(
                "docker", "docker_caido", Severity.CRITICAL, "escalate",
                _is_false("docker_ok"), "Motor Docker no disponible",
                "El host no puede administrar contenedores.",
            ),
            self._rule(
                "ssh", "ssh_fallido", Severity.HIGH, "escalate", _is_false("ssh_ok"),
                "Comprobacion SSH fallida", "No se habilita ejecucion remota arbitraria.",
            ),
        ]
        return rules

    def evaluate(self, observation: Observation) -> list[Detection]:
        detections: list[Detection] = []
        thresholds = self.config.get("thresholds", {})
        for rule in self.rules:
            if rule.enabled and rule.predicate(observation, thresholds):
                detections.append(
                    Detection(
                        rule_id=rule.id,
                        incident_type=rule.incident_type,
                        severity=rule.severity,
                        cause=rule.cause(observation),
                        diagnosis=rule.diagnosis(observation),
                        strategy=rule.strategy,
                    )
                )
        return detections
