# backend/app/services/email_service.py
"""SMTP email sending — stateless, config-driven."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared layout helpers
# ---------------------------------------------------------------------------

_BRAND_BLUE = "#0069a8"
_BRAND_DARK = "#30404d"
_BODY_BG = "#f4f6f8"
_CARD_BG = "#ffffff"
_TEXT_MAIN = "#2d3748"
_TEXT_MUTED = "#718096"
_BORDER = "#e2e8f0"


def _logo_html() -> str:
    return (
        f'<span style="font-family:Arial,sans-serif;font-size:24px;font-weight:700;'
        f'letter-spacing:-0.5px;">'
        f'<span style="color:{_BRAND_DARK};">Lingvo</span>'
        f'<span style="color:{_BRAND_BLUE};">Pal</span>'
        f"</span>"
    )


def _wrap(body_content: str, preview_text: str = "") -> str:
    """Wrap content in a full responsive email layout."""
    preview = (
        f'<div style="display:none;max-height:0;overflow:hidden;'
        f'mso-hide:all;font-size:1px;color:{_BODY_BG};">{preview_text}</div>'
        if preview_text
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>LingvoPal</title>
</head>
<body style="margin:0;padding:0;background-color:{_BODY_BG};font-family:Arial,Helvetica,sans-serif;">
{preview}
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background-color:{_BODY_BG};padding:40px 16px;">
  <tr>
    <td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="max-width:560px;">

        <!-- HEADER -->
        <tr>
          <td align="center" style="padding-bottom:24px;">
            {_logo_html()}
          </td>
        </tr>

        <!-- CARD -->
        <tr>
          <td style="background-color:{_CARD_BG};border-radius:12px;
                     border:1px solid {_BORDER};padding:40px 40px 32px;">
            {body_content}
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td align="center" style="padding-top:24px;
                font-size:12px;color:{_TEXT_MUTED};line-height:1.6;">
            LingvoPal &mdash; Language Learning Platform<br />
            If you did not request this email, you can safely ignore it.<br />
            <span style="color:{_BORDER};">&#8203;</span>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""


def _cta_button(url: str, label: str) -> str:
    return (
        f'<table cellpadding="0" cellspacing="0" border="0" style="margin:32px auto;">'
        f"<tr>"
        f'<td align="center" style="border-radius:8px;background-color:{_BRAND_BLUE};">'
        f'<a href="{url}" target="_blank" '
        f'style="display:inline-block;padding:14px 32px;font-size:15px;font-weight:700;'
        f"color:#ffffff;text-decoration:none;border-radius:8px;"
        f'font-family:Arial,Helvetica,sans-serif;">'
        f"{label}"
        f"</a>"
        f"</td>"
        f"</tr>"
        f"</table>"
    )


def _fallback_link(url: str) -> str:
    return (
        f'<p style="font-size:12px;color:{_TEXT_MUTED};word-break:break-all;'
        f'text-align:center;margin-top:0;">'
        f"Or copy this link into your browser:<br />"
        f'<a href="{url}" style="color:{_BRAND_BLUE};">{url}</a>'
        f"</p>"
    )


def _h1(text: str) -> str:
    return (
        f'<h1 style="margin:0 0 12px;font-size:22px;font-weight:700;'
        f'color:{_BRAND_DARK};font-family:Arial,Helvetica,sans-serif;">{text}</h1>'
    )


def _p(text: str) -> str:
    return (
        f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;'
        f'color:{_TEXT_MAIN};font-family:Arial,Helvetica,sans-serif;">{text}</p>'
    )


def _divider() -> str:
    return f'<hr style="border:none;border-top:1px solid {_BORDER};margin:24px 0;" />'


# ---------------------------------------------------------------------------
# Per-email template builders
# ---------------------------------------------------------------------------


def _verification_html(link: str) -> str:
    body = (
        _h1("Verify your email address")
        + _p(
            "Thanks for signing up for LingvoPal! To get started, please confirm "
            "your email address by clicking the button below."
        )
        + _cta_button(link, "Verify Email Address")
        + _fallback_link(link)
        + _divider()
        + f'<p style="margin:0;font-size:12px;color:{_TEXT_MUTED};line-height:1.6;">'
        + "This link expires in <strong>24 hours</strong>. "
        + "Don't see this email? Check your spam or junk folder."
        + "</p>"
    )
    return _wrap(body, preview_text="Confirm your email to start learning with LingvoPal.")


def _verification_plain(link: str) -> str:
    return (
        "Verify your LingvoPal email address\n"
        "=====================================\n\n"
        "Thanks for signing up! Please verify your email address by visiting:\n\n"
        f"{link}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you did not create a LingvoPal account, you can safely ignore this email.\n\n"
        "— The LingvoPal Team"
    )


def _password_reset_html(link: str) -> str:
    body = (
        _h1("Reset your password")
        + _p(
            "We received a request to reset the password for your LingvoPal account. "
            "Click the button below to choose a new password."
        )
        + _cta_button(link, "Reset Password")
        + _fallback_link(link)
        + _divider()
        + f'<p style="margin:0;font-size:12px;color:{_TEXT_MUTED};line-height:1.6;">'
        + "This link expires in <strong>1 hour</strong>. "
        + "If you did not request a password reset, no action is needed — "
        + "your password will remain unchanged."
        + "</p>"
    )
    return _wrap(body, preview_text="Reset your LingvoPal password — link expires in 1 hour.")


def _password_reset_plain(link: str) -> str:
    return (
        "Reset your LingvoPal password\n"
        "===============================\n\n"
        "We received a request to reset your password. Visit the link below:\n\n"
        f"{link}\n\n"
        "This link expires in 1 hour.\n\n"
        "If you did not request a password reset, you can safely ignore this email.\n\n"
        "— The LingvoPal Team"
    )


def _email_change_html(link: str, new_email: str) -> str:
    body = (
        _h1("Confirm your new email address")
        + _p(
            f"You requested to change your LingvoPal email to "
            f'<strong style="color:{_BRAND_DARK};">{new_email}</strong>. '
            "Click the button below to confirm this change."
        )
        + _cta_button(link, "Confirm Email Change")
        + _fallback_link(link)
        + _divider()
        + f'<p style="margin:0;font-size:12px;color:{_TEXT_MUTED};line-height:1.6;">'
        + "This link expires in <strong>24 hours</strong>. "
        + "If you did not request this change, please secure your account immediately."
        + "</p>"
    )
    return _wrap(body, preview_text=f"Confirm your new LingvoPal email address: {new_email}")


def _email_change_plain(link: str, new_email: str) -> str:
    return (
        "Confirm your new LingvoPal email address\n"
        "==========================================\n\n"
        f"You requested to change your email to: {new_email}\n\n"
        "Confirm this change by visiting:\n\n"
        f"{link}\n\n"
        "This link expires in 24 hours.\n\n"
        "If you did not request this change, please secure your account immediately.\n\n"
        "— The LingvoPal Team"
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _make_message(self, to_email: str, subject: str, plain: str, html: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"LingvoPal <{self._settings.SMTP_FROM}>"
        msg["To"] = to_email
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html, "html"))
        return msg

    async def _send(self, msg: MIMEMultipart) -> None:
        smtp_kwargs: dict = {
            "hostname": self._settings.SMTP_HOST,
            "port": self._settings.SMTP_PORT,
            "start_tls": self._settings.SMTP_TLS,
        }
        if self._settings.SMTP_USER and self._settings.SMTP_PASSWORD:
            smtp_kwargs["username"] = self._settings.SMTP_USER
            smtp_kwargs["password"] = self._settings.SMTP_PASSWORD
        await aiosmtplib.send(msg, **smtp_kwargs)

    async def send_verification(self, to_email: str, token: str) -> None:
        link = f"{self._settings.FRONTEND_URL}/verify?token={token}"
        msg = self._make_message(
            to_email,
            subject="Verify your LingvoPal email",
            plain=_verification_plain(link),
            html=_verification_html(link),
        )
        await self._send(msg)
        logger.info("verification_email_sent", extra={"email": to_email})

    async def send_password_reset(self, to_email: str, token: str) -> None:
        link = f"{self._settings.FRONTEND_URL}/auth/reset-password?token={token}"
        msg = self._make_message(
            to_email,
            subject="Reset your LingvoPal password",
            plain=_password_reset_plain(link),
            html=_password_reset_html(link),
        )
        await self._send(msg)
        logger.info("password_reset_email_sent", extra={"email": to_email})

    async def send_email_change_verification(self, to_email: str, token: str) -> None:
        link = f"{self._settings.FRONTEND_URL}/auth/change-email?token={token}"
        msg = self._make_message(
            to_email,
            subject="Confirm your new LingvoPal email",
            plain=_email_change_plain(link, to_email),
            html=_email_change_html(link, to_email),
        )
        await self._send(msg)
        logger.info("email_change_verification_sent", extra={"email": to_email})


__all__ = ["EmailService"]
