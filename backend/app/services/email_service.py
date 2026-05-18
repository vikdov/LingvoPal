# backend/app/services/email_service.py
"""SMTP email sending — stateless, config-driven."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_verification(self, to_email: str, token: str) -> None:
        """Send verification email. Raises on SMTP failure — caller should handle."""
        link = f"{self._settings.FRONTEND_URL}/verify?token={token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your LingvoPal email"
        msg["From"] = self._settings.SMTP_FROM
        msg["To"] = to_email

        plain = (
            f"Verify your LingvoPal email address by clicking the link below:\n\n"
            f"{link}\n\n"
            f"This link expires in 24 hours. If you did not register, ignore this email."
        )
        html = (
            f"<p>Click the link below to verify your LingvoPal email address:</p>"
            f'<p><a href="{link}">Verify Email</a></p>'
            f"<p>Or copy this link into your browser: {link}</p>"
            f"<p>This link expires in 24 hours. If you did not register, ignore this email.</p>"
        )

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        smtp_kwargs: dict = {
            "hostname": self._settings.SMTP_HOST,
            "port": self._settings.SMTP_PORT,
            "start_tls": self._settings.SMTP_TLS,
        }
        if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
            smtp_kwargs["username"] = self._settings.SMTP_USER
            smtp_kwargs["password"] = self._settings.SMTP_PASSWORD

        await aiosmtplib.send(msg, **smtp_kwargs)
        logger.info("verification_email_sent", extra={"email": to_email})

    async def send_password_reset(self, to_email: str, token: str) -> None:
        """Send password reset email. Raises on SMTP failure — caller should handle."""
        link = f"{self._settings.FRONTEND_URL}/auth/reset-password?token={token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your LingvoPal password"
        msg["From"] = self._settings.SMTP_FROM
        msg["To"] = to_email

        plain = (
            f"Reset your LingvoPal password by clicking the link below:\n\n"
            f"{link}\n\n"
            f"This link expires in 1 hour. If you did not request a reset, ignore this email."
        )
        html = (
            f"<p>Click the link below to reset your LingvoPal password:</p>"
            f'<p><a href="{link}">Reset Password</a></p>'
            f"<p>Or copy this link into your browser: {link}</p>"
            f"<p>This link expires in 1 hour. If you did not request a reset, ignore this email.</p>"
        )

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        smtp_kwargs: dict = {
            "hostname": self._settings.SMTP_HOST,
            "port": self._settings.SMTP_PORT,
            "start_tls": self._settings.SMTP_TLS,
        }
        if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
            smtp_kwargs["username"] = self._settings.SMTP_USER
            smtp_kwargs["password"] = self._settings.SMTP_PASSWORD

        await aiosmtplib.send(msg, **smtp_kwargs)
        logger.info("password_reset_email_sent", extra={"email": to_email})

    async def send_email_change_verification(self, to_email: str, token: str) -> None:
        """Send email change verification to the new address. Raises on SMTP failure."""
        link = f"{self._settings.FRONTEND_URL}/auth/change-email?token={token}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirm your new LingvoPal email"
        msg["From"] = self._settings.SMTP_FROM
        msg["To"] = to_email

        plain = (
            f"Confirm your new LingvoPal email address by clicking the link below:\n\n"
            f"{link}\n\n"
            f"This link expires in 24 hours. If you did not request this change, ignore this email."
        )
        html = (
            f"<p>Click the link below to confirm your new LingvoPal email address:</p>"
            f'<p><a href="{link}">Confirm Email Change</a></p>'
            f"<p>Or copy this link into your browser: {link}</p>"
            f"<p>This link expires in 24 hours. If you did not request this change, ignore this email.</p>"
        )

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))

        smtp_kwargs: dict = {
            "hostname": self._settings.SMTP_HOST,
            "port": self._settings.SMTP_PORT,
            "start_tls": self._settings.SMTP_TLS,
        }
        if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
            smtp_kwargs["username"] = self._settings.SMTP_USER
            smtp_kwargs["password"] = self._settings.SMTP_PASSWORD

        await aiosmtplib.send(msg, **smtp_kwargs)
        logger.info("email_change_verification_sent", extra={"email": to_email})


__all__ = ["EmailService"]
