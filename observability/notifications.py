"""Canal de alerta humana con resultado auditable."""

import smtplib
import ssl
from email.message import EmailMessage

from .config import Settings


class Notifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, subject: str, body: str) -> dict[str, str]:
        if not (
            self.settings.smtp_host
            and self.settings.smtp_from
            and self.settings.smtp_to
        ):
            return {
                "status": "simulated",
                "reason": "SMTP no configurado; alerta conservada solo como evidencia",
                "subject": subject,
            }
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = self.settings.smtp_to
        message.set_content(body)
        try:
            with smtplib.SMTP(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=20,
            ) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                if self.settings.smtp_user and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_user, self.settings.smtp_password)
                smtp.send_message(message)
            return {"status": "sent", "recipient": self.settings.smtp_to}
        except (OSError, smtplib.SMTPException) as error:
            return {"status": "error", "reason": str(error), "subject": subject}
