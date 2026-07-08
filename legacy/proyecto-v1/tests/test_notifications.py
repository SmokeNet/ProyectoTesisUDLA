import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from observability.notifications import Notifier


class NotificationTests(unittest.TestCase):
    def test_sin_smtp_queda_explicito_como_simulada(self):
        settings = SimpleNamespace(smtp_host="", smtp_from="", smtp_to="")
        result = Notifier(settings).send("Alerta", "Detalle")
        self.assertEqual(result["status"], "simulated")

    def test_smtp_usa_tls_y_envio(self):
        settings = SimpleNamespace(
            smtp_host="smtp.example.test",
            smtp_port=587,
            smtp_user="robot",
            smtp_password="secret",
            smtp_from="robot@example.test",
            smtp_to="ops@example.test",
        )
        client = MagicMock()
        context = MagicMock()
        context.__enter__.return_value = client
        with patch("observability.notifications.smtplib.SMTP", return_value=context):
            result = Notifier(settings).send("Alerta", "Detalle")
        self.assertEqual(result["status"], "sent")
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("robot", "secret")
        client.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
