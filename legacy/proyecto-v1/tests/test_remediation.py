import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from observability.domain import Observation
from observability.remediation import RemediationEngine, RemediationPolicy


class RemediationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        state_file = Path(self.temporary.name) / "state.json"
        self.engine = RemediationEngine(
            Path("docker/docker-compose.yml"),
            RemediationPolicy(2, 300, 10),
            state_file=state_file,
        )
        self.before = Observation("sitio-vigilado", "localhost", "http://localhost", port_open=False)

    def test_estrategia_peligrosa_solo_escala(self):
        result = self.engine.execute("escalate", "sitio-vigilado", self.before, Mock())
        self.assertFalse(result.attempted)
        self.assertTrue(result.escalated)

    def test_bloquea_servicio_no_permitido(self):
        result = self.engine.execute("restart_service", "servicio-inyectado", self.before, Mock())
        self.assertFalse(result.attempted)

    def test_impide_bucle_por_intentos(self):
        result = self.engine.execute("restart_service", "sitio-vigilado", self.before, Mock(), attempt_count=2)
        self.assertIn("limite", result.reason)

    def test_respeta_cooldown(self):
        result = self.engine.execute(
            "restart_service",
            "sitio-vigilado",
            self.before,
            Mock(),
            last_attempt_at=datetime.now(timezone.utc),
        )
        self.assertIn("cooldown", result.reason)

    def test_ejecuta_sin_shell_y_revalida(self):
        process = Mock(returncode=0, stdout="ok", stderr="")
        after = Observation("sitio-vigilado", "localhost", "http://localhost", port_open=True, http_status=200)
        with patch("observability.remediation.subprocess.run", return_value=process) as run:
            result = self.engine.execute("restart_service", "sitio-vigilado", self.before, lambda: after)
        self.assertTrue(result.success)
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertIn("--force-recreate", run.call_args.args[0])

    def test_cooldown_persiste_entre_instancias(self):
        process = Mock(returncode=1, stdout="", stderr="fallo")
        with patch("observability.remediation.subprocess.run", return_value=process):
            first = self.engine.execute(
                "restart_service",
                "sitio-vigilado",
                self.before,
                Mock(),
            )
        second_engine = RemediationEngine(
            Path("docker/docker-compose.yml"),
            RemediationPolicy(2, 300, 10),
            state_file=self.engine.state_file,
        )
        second = second_engine.execute(
            "restart_service",
            "sitio-vigilado",
            self.before,
            Mock(),
        )
        self.assertTrue(first.attempted)
        self.assertIn("cooldown", second.reason)


if __name__ == "__main__":
    unittest.main()
