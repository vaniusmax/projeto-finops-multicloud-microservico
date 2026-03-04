from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from finops_api.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def send_registration_email(self, *, recipient: str, first_name: str, verification_url: str) -> None:
        subject = "Ative seu acesso ao FinOps Multicloud"
        body = (
            f"Olá, {first_name}.\n\n"
            "Recebemos sua solicitação de acesso ao dashboard FinOps Multicloud.\n"
            "Para concluir o cadastro, acesse o link abaixo e defina sua senha:\n\n"
            f"{verification_url}\n\n"
            "Se você não solicitou o cadastro, ignore este e-mail."
        )
        self._send_email(recipient=recipient, subject=subject, body=body)

    def _send_email(self, *, recipient: str, subject: str, body: str) -> None:
        if not settings.smtp_host:
            logger.info("SMTP_HOST não configurado. E-mail seria enviado para %s com assunto %s", recipient, subject)
            logger.debug("Corpo do e-mail: %s", body)
            return

        message = EmailMessage()
        message["From"] = settings.auth_email_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
