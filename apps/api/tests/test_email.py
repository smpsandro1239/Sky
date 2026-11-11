from unittest.mock import MagicMock

from app.core import email as email_service
from app.core.config import settings


def test_invitation_email_is_skipped_when_smtp_is_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from_email", None)
    smtp = MagicMock()
    monkeypatch.setattr(email_service.smtplib, "SMTP", smtp)

    sent = email_service.send_trip_invitation_email(
        to_email="guest@example.com",
        trip_name="Férias",
        inviter_name="Organizador",
        role="viewer",
        accept_url="https://sky.example/invitations/accept?token=secret-token",
    )

    assert sent is False
    smtp.assert_not_called()


def test_invitation_email_uses_starttls_and_sends_message(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_from_email", "sky@example.com")
    monkeypatch.setattr(settings, "smtp_username", "sky-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-password")
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)

    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(email_service.smtplib, "SMTP", MagicMock(return_value=smtp))

    sent = email_service.send_trip_invitation_email(
        to_email="guest@example.com",
        trip_name="Férias",
        inviter_name="Organizador",
        role="editor",
        accept_url="https://sky.example/invitations/accept?token=secret-token",
    )

    assert sent is True
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("sky-user", "smtp-password")
    smtp.send_message.assert_called_once()
    message = smtp.send_message.call_args.args[0]
    assert message["To"] == "guest@example.com"
    assert "editor" in message.get_content()
    assert "secret-token" in message.get_content()


def test_invitation_email_failure_is_reported_without_raising(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "sky@example.com")
    smtp = MagicMock()
    smtp.__enter__.side_effect = OSError("SMTP indisponível")
    monkeypatch.setattr(email_service.smtplib, "SMTP", MagicMock(return_value=smtp))

    sent = email_service.send_trip_invitation_email(
        to_email="guest@example.com",
        trip_name="Férias",
        inviter_name="Organizador",
        role="viewer",
        accept_url="https://sky.example/invitations/accept?token=secret-token",
    )

    assert sent is False


def test_invitation_email_supports_implicit_tls(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 465)
    monkeypatch.setattr(settings, "smtp_from_email", "sky@example.com")
    monkeypatch.setattr(settings, "smtp_username", None)
    monkeypatch.setattr(settings, "smtp_password", None)
    monkeypatch.setattr(settings, "smtp_starttls", False)
    monkeypatch.setattr(settings, "smtp_use_ssl", True)

    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", MagicMock(return_value=smtp))

    sent = email_service.send_trip_invitation_email(
        to_email="guest@example.com",
        trip_name="Férias",
        inviter_name="Organizador",
        role="viewer",
        accept_url="https://sky.example/invitations/accept?token=secret-token",
    )

    assert sent is True
    smtp.starttls.assert_not_called()
    smtp.send_message.assert_called_once()


def test_invitation_subject_sanitizes_newlines_in_trip_name(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_from_email", "sky@example.com")
    monkeypatch.setattr(settings, "smtp_username", None)
    monkeypatch.setattr(settings, "smtp_password", None)
    monkeypatch.setattr(settings, "smtp_starttls", True)
    monkeypatch.setattr(settings, "smtp_use_ssl", False)

    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(email_service.smtplib, "SMTP", MagicMock(return_value=smtp))

    sent = email_service.send_trip_invitation_email(
        to_email="guest@example.com",
        trip_name="Férias\r\nBcc: attacker@example.com",
        inviter_name="Organizador",
        role="viewer",
        accept_url="https://sky.example/invitations/accept?token=secret-token",
    )

    assert sent is True
    subject = smtp.send_message.call_args.args[0]["Subject"]
    assert "\r" not in subject and "\n" not in subject
    assert "attacker@example.com" not in subject
