# backend/tests/test_email_service.py
"""
Tests for EmailService templates and message construction.

Groups:
  - Template content: links, brand elements, expiry notes present in HTML/plain
  - Message structure: MIME parts, From display name, Subject
  - Integration (Mailpit): real SMTP send against local Mailpit, verified via HTTP API
    Skipped automatically when Mailpit is unreachable.
"""

from email.mime.multipart import MIMEMultipart
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_service import (
    EmailService,
    _email_change_html,
    _email_change_plain,
    _password_reset_html,
    _password_reset_plain,
    _verification_html,
    _verification_plain,
    _wrap,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_LINK = "https://lingvopal.com/verify?token=abc123"
FAKE_RESET_LINK = "https://lingvopal.com/auth/reset-password?token=xyz789"
FAKE_CHANGE_LINK = "https://lingvopal.com/auth/change-email?token=def456"
FAKE_NEW_EMAIL = "new@example.com"


def _make_settings(smtp_host: str = "localhost", smtp_port: int = 1025) -> MagicMock:
    s = MagicMock()
    s.SMTP_HOST = smtp_host
    s.SMTP_PORT = smtp_port
    s.SMTP_TLS = False
    s.SMTP_USER = ""
    s.SMTP_PASSWORD = ""
    s.SMTP_FROM = "noreply@lingvopal.com"
    s.FRONTEND_URL = "https://lingvopal.com"
    return s


# ---------------------------------------------------------------------------
# _wrap
# ---------------------------------------------------------------------------


class TestWrap:
    def test_contains_lingvopal_brand(self) -> None:
        html = _wrap("<p>body</p>")
        assert "Lingvo" in html
        assert "Pal" in html

    def test_preview_text_included(self) -> None:
        html = _wrap("<p>body</p>", preview_text="Preview goes here")
        assert "Preview goes here" in html

    def test_no_preview_text_when_empty(self) -> None:
        html = _wrap("<p>body</p>", preview_text="")
        assert "display:none" not in html

    def test_is_valid_html_structure(self) -> None:
        html = _wrap("<p>body</p>")
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html


# ---------------------------------------------------------------------------
# Verification templates
# ---------------------------------------------------------------------------


class TestVerificationTemplates:
    def test_html_contains_link(self) -> None:
        html = _verification_html(FAKE_LINK)
        assert FAKE_LINK in html

    def test_html_contains_verify_heading(self) -> None:
        html = _verification_html(FAKE_LINK)
        assert "Verify" in html

    def test_html_mentions_24_hours(self) -> None:
        html = _verification_html(FAKE_LINK)
        assert "24 hours" in html

    def test_html_mentions_spam(self) -> None:
        html = _verification_html(FAKE_LINK)
        assert "spam" in html.lower()

    def test_plain_contains_link(self) -> None:
        plain = _verification_plain(FAKE_LINK)
        assert FAKE_LINK in plain

    def test_plain_contains_expiry(self) -> None:
        plain = _verification_plain(FAKE_LINK)
        assert "24 hours" in plain


# ---------------------------------------------------------------------------
# Password reset templates
# ---------------------------------------------------------------------------


class TestPasswordResetTemplates:
    def test_html_contains_link(self) -> None:
        html = _password_reset_html(FAKE_RESET_LINK)
        assert FAKE_RESET_LINK in html

    def test_html_mentions_1_hour(self) -> None:
        html = _password_reset_html(FAKE_RESET_LINK)
        assert "1 hour" in html

    def test_html_reassures_if_not_requested(self) -> None:
        html = _password_reset_html(FAKE_RESET_LINK)
        assert "did not request" in html.lower()

    def test_plain_contains_link(self) -> None:
        plain = _password_reset_plain(FAKE_RESET_LINK)
        assert FAKE_RESET_LINK in plain

    def test_plain_mentions_expiry(self) -> None:
        plain = _password_reset_plain(FAKE_RESET_LINK)
        assert "1 hour" in plain


# ---------------------------------------------------------------------------
# Email change templates
# ---------------------------------------------------------------------------


class TestEmailChangeTemplates:
    def test_html_contains_link(self) -> None:
        html = _email_change_html(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert FAKE_CHANGE_LINK in html

    def test_html_contains_new_email(self) -> None:
        html = _email_change_html(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert FAKE_NEW_EMAIL in html

    def test_html_mentions_24_hours(self) -> None:
        html = _email_change_html(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert "24 hours" in html

    def test_html_security_warning(self) -> None:
        html = _email_change_html(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert "secure" in html.lower()

    def test_plain_contains_link(self) -> None:
        plain = _email_change_plain(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert FAKE_CHANGE_LINK in plain

    def test_plain_contains_new_email(self) -> None:
        plain = _email_change_plain(FAKE_CHANGE_LINK, FAKE_NEW_EMAIL)
        assert FAKE_NEW_EMAIL in plain


# ---------------------------------------------------------------------------
# EmailService._make_message
# ---------------------------------------------------------------------------


class TestMakeMessage:
    def setup_method(self) -> None:
        self.svc = EmailService(_make_settings())

    def test_returns_mime_multipart(self) -> None:
        msg = self.svc._make_message("to@test.com", "Subject", "plain", "<p>html</p>")
        assert isinstance(msg, MIMEMultipart)

    def test_subject(self) -> None:
        msg = self.svc._make_message("to@test.com", "Hello World", "plain", "<p>html</p>")
        assert msg["Subject"] == "Hello World"

    def test_from_contains_display_name(self) -> None:
        msg = self.svc._make_message("to@test.com", "Sub", "plain", "<p>html</p>")
        assert "LingvoPal" in msg["From"]
        assert "noreply@lingvopal.com" in msg["From"]

    def test_to_field(self) -> None:
        msg = self.svc._make_message("user@example.com", "Sub", "plain", "<p>html</p>")
        assert msg["To"] == "user@example.com"

    def test_has_two_parts(self) -> None:
        msg = self.svc._make_message("to@test.com", "Sub", "plain text", "<p>html</p>")
        parts = msg.get_payload()
        assert len(parts) == 2

    def test_first_part_is_plain(self) -> None:
        msg = self.svc._make_message("to@test.com", "Sub", "plain text body", "<p>html</p>")
        plain_part = msg.get_payload(0)
        assert plain_part.get_content_type() == "text/plain"

    def test_second_part_is_html(self) -> None:
        msg = self.svc._make_message("to@test.com", "Sub", "plain", "<p>html body</p>")
        html_part = msg.get_payload(1)
        assert html_part.get_content_type() == "text/html"


# ---------------------------------------------------------------------------
# EmailService public methods (mock SMTP)
# ---------------------------------------------------------------------------


class TestEmailServiceSendMethods:
    def setup_method(self) -> None:
        self.svc = EmailService(_make_settings())

    @pytest.mark.asyncio
    async def test_send_verification_calls_smtp(self) -> None:
        with patch(
            "app.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await self.svc.send_verification("user@example.com", "token123")
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "Verify" in msg["Subject"]
        assert "user@example.com" == msg["To"]

    @pytest.mark.asyncio
    async def test_send_verification_link_contains_token(self) -> None:
        with patch(
            "app.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await self.svc.send_verification("user@example.com", "mytoken")
        msg = mock_send.call_args[0][0]
        html_payload = msg.get_payload(1).get_payload(decode=True).decode()
        assert "mytoken" in html_payload

    @pytest.mark.asyncio
    async def test_send_password_reset_calls_smtp(self) -> None:
        with patch(
            "app.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await self.svc.send_password_reset("user@example.com", "resettoken")
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "Reset" in msg["Subject"]

    @pytest.mark.asyncio
    async def test_send_email_change_calls_smtp(self) -> None:
        with patch(
            "app.services.email_service.aiosmtplib.send", new_callable=AsyncMock
        ) as mock_send:
            await self.svc.send_email_change_verification("new@example.com", "changetoken")
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert "Confirm" in msg["Subject"]


# ---------------------------------------------------------------------------
# Integration — Mailpit (skipped when unavailable)
# ---------------------------------------------------------------------------


def _mailpit_available() -> bool:
    import socket

    try:
        s = socket.create_connection(("localhost", 1025), timeout=1)
        s.close()
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _mailpit_available(), reason="Mailpit not running on localhost:1025")
class TestMailpitIntegration:
    """Sends real emails to Mailpit and verifies via its HTTP API."""

    BASE_URL = "http://localhost:8025/api/v1"

    def setup_method(self) -> None:
        import httpx

        # Clear inbox before each test
        httpx.delete(f"{self.BASE_URL}/messages")
        self.svc = EmailService(_make_settings())

    def _latest_message(self) -> dict:
        import httpx

        r = httpx.get(f"{self.BASE_URL}/messages")
        r.raise_for_status()
        messages = r.json().get("messages", [])
        assert messages, "No email received in Mailpit"
        return messages[0]

    def _get_message_html(self, msg_id: str) -> str:
        import httpx

        r = httpx.get(f"{self.BASE_URL}/message/{msg_id}")
        r.raise_for_status()
        return r.json().get("HTML", "")

    @pytest.mark.asyncio
    async def test_verification_email_received(self) -> None:
        await self.svc.send_verification("test@example.com", "verifytoken999")
        msg = self._latest_message()
        assert msg["To"][0]["Address"] == "test@example.com"
        assert "Verify" in msg["Subject"]
        assert "LingvoPal" in msg["From"]["Name"]

    @pytest.mark.asyncio
    async def test_verification_email_html_contains_token(self) -> None:
        await self.svc.send_verification("test@example.com", "uniquetoken42")
        msg = self._latest_message()
        html = self._get_message_html(msg["ID"])
        assert "uniquetoken42" in html

    @pytest.mark.asyncio
    async def test_verification_email_html_has_brand(self) -> None:
        await self.svc.send_verification("test@example.com", "tok")
        msg = self._latest_message()
        html = self._get_message_html(msg["ID"])
        assert "Lingvo" in html
        assert "Pal" in html

    @pytest.mark.asyncio
    async def test_password_reset_email_received(self) -> None:
        await self.svc.send_password_reset("reset@example.com", "resettoken999")
        msg = self._latest_message()
        assert msg["To"][0]["Address"] == "reset@example.com"
        assert "Reset" in msg["Subject"]

    @pytest.mark.asyncio
    async def test_email_change_email_received(self) -> None:
        await self.svc.send_email_change_verification("change@example.com", "changetoken999")
        msg = self._latest_message()
        assert msg["To"][0]["Address"] == "change@example.com"
        assert "Confirm" in msg["Subject"]
