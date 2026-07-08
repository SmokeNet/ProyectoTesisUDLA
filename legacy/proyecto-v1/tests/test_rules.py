import unittest

from observability.domain import Observation
from observability.rules import RuleEngine


CONFIG = {
    "thresholds": {
        "latency_ms": 1000,
        "ssl_expiry_days": 30,
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "connections_percent": 90,
    },
    "enabled": {},
}


class RuleEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuleEngine(CONFIG)

    def types(self, observation):
        return {item.incident_type for item in self.engine.evaluate(observation)}

    def test_cubre_catalogo_profesional(self):
        ids = {rule.id for rule in self.engine.rules}
        self.assertEqual(len(ids), 23)
        self.assertTrue({"http_4xx", "http_5xx", "dns", "ssl_invalid", "cpu", "memory", "disk", "ssh"} <= ids)

    def test_detecta_multiples_fallas_simultaneas(self):
        observation = Observation(
            "web",
            "srv",
            "http://web",
            http_status=500,
            latency_ms=2500,
            content_expected=False,
            cpu_percent=95,
        )
        detected = self.types(observation)
        self.assertTrue({"http_5xx", "latencia_elevada", "contenido_inesperado", "cpu_elevada"} <= detected)

    def test_no_inventa_fallas_sin_telemetria(self):
        self.assertEqual(self.engine.evaluate(Observation("web", "srv", "http://web")), [])

    def test_ssl_y_dns_escalan(self):
        detections = self.engine.evaluate(Observation("web", "srv", "https://web", dns_ok=False, ssl_valid=False))
        self.assertTrue(all(item.strategy == "escalate" for item in detections))


if __name__ == "__main__":
    unittest.main()
