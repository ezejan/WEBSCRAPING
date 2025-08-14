"""Cliente SMTP para envío de invitaciones."""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from string import Template
from typing import Dict

from scraping.directory import Provider


class EmailClient:
    """Envía correos de invitación a los proveedores."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str | None,
        password: str | None,
        from_addr: str,
        subject: str,
        template_path: str,
    ) -> None:
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.subject = subject
        self.template_path = Path(template_path)
        self.template = Template(self.template_path.read_text(encoding="utf-8"))

    def send(self, provider: Provider, test_recipient: str | None = None) -> None:
        """Envía un correo a ``provider``.

        Si ``test_recipient`` está definido, el correo se enviará a esa dirección
        en lugar de a la del proveedor. Esto facilita pruebas sin generar SPAM.
        """

        to_addr = test_recipient or provider.email
        if not to_addr:
            logging.info(
                "No se envió correo a %s por falta de dirección.", provider.nombre
            )
            return

        body = self.template.safe_substitute(
            nombre=provider.nombre, servicio=provider.servicio, zona=provider.zona
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["From"] = self.from_addr
        msg["To"] = to_addr
        msg["Subject"] = self.subject

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.from_addr, [to_addr], msg.as_string())
            logging.info("Correo enviado a %s", to_addr)
        except Exception as exc:  # pragma: no cover - manejo básico
            logging.error("No se pudo enviar correo a %s: %s", to_addr, exc)
