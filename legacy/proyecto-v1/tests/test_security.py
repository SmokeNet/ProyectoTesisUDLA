"""Pruebas deterministas del Security Watcher sin emitir trafico ofensivo real."""

import unittest
from datetime import datetime, timedelta, timezone

from observability.security import HttpAccessEvent, SecurityPolicy, SecurityWatcher


class SecurityWatcherTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.watcher = SecurityWatcher(SecurityPolicy(
            flood_requests=3,
            brute_force_attempts=3,
            scan_unique_paths=3,
            temporary_block_seconds=30,
        ))

    def event(self, **changes):
        values = {
            "source_ip": "demo:qa",
            "method": "GET",
            "path": "/",
            "occurred_at": self.now,
        }
        values.update(changes)
        return HttpAccessEvent(**values)

    def test_trafico_normal_no_genera_alerta(self):
        self.assertEqual([], self.watcher.evaluate(self.event()))

    def test_evidencia_redacta_credenciales(self):
        event = self.event(
            path="/?token=valor-sensible",
            body_sample="usuario=demo&password=supersecreto&clave=otra",
        )
        serialized = str(event.safe_dict())
        self.assertNotIn("valor-sensible", serialized)
        self.assertNotIn("supersecreto", serialized)
        self.assertNotIn("otra", serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_detecta_sqli_y_aplica_bloqueo_temporal(self):
        detections = self.watcher.evaluate(self.event(path="/?id=1%20UNION%20SELECT%20password"))
        self.assertIn("sqli_basic", {item.rule_id for item in detections})
        self.assertIsNotNone(self.watcher.blocked_until("demo:qa", self.now))
        self.assertIsNone(
            self.watcher.blocked_until("demo:qa", self.now + timedelta(seconds=31))
        )

    def test_detecta_xss_basico(self):
        detections = self.watcher.evaluate(self.event(path="/?q=<script>alert(1)</script>"))
        self.assertIn("xss_basic", {item.rule_id for item in detections})

    def test_detecta_user_agent_sospechoso_sin_afirmar_compromiso(self):
        detections = self.watcher.evaluate(self.event(user_agent="sqlmap/1.8"))
        item = next(item for item in detections if item.rule_id == "suspicious_user_agent")
        self.assertEqual("escalate", item.response)

    def test_detecta_flood_por_ventana(self):
        detections = []
        for index in range(4):
            detections = self.watcher.evaluate(self.event(
                path=f"/?n={index}", occurred_at=self.now + timedelta(seconds=index)
            ))
        self.assertIn("http_flood", {item.rule_id for item in detections})

    def test_detecta_escaneo_por_rutas_unicas(self):
        detections = []
        for path in ("/admin", "/backup", "/config"):
            detections = self.watcher.evaluate(self.event(path=path))
        self.assertIn("route_scan", {item.rule_id for item in detections})

    def test_detecta_fuerza_bruta_simulada(self):
        detections = []
        for index in range(3):
            detections = self.watcher.evaluate(self.event(
                method="POST", path="/login", occurred_at=self.now + timedelta(seconds=index)
            ))
        self.assertIn("brute_force", {item.rule_id for item in detections})


if __name__ == "__main__":
    unittest.main()
