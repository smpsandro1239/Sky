import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_trip_invitation_email(
    *,
    to_email: str,
    trip_name: str,
    inviter_name: str,
    role: str,
    accept_url: str,
) -> bool:
    """Envia um convite por SMTP; devolve False quando não está configurado ou falha."""
    if not settings.smtp_host or not settings.smtp_from_email:
        return False
    if settings.smtp_username and not settings.smtp_password:
        logger.warning("SMTP não enviado: falta SMTP_PASSWORD.")
        return False

    role_label = "editor" if role == "editor" else "leitor"
    message = EmailMessage()
    message["Subject"] = f"Convite para a viagem {trip_name} no SKY"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(
        f"{inviter_name} convidou-te para colaborar na viagem \"{trip_name}\" no SKY.\n\n"
        f"Permissão atribuída: {role_label}.\n"
        f"Este convite é válido durante 7 dias e só pode ser utilizado pela conta "
        f"registada com este endereço de email.\n\n"
        f"Para aceitar o convite, abre: {accept_url}\n"
    )

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as smtp:
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password or "")
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                if settings.smtp_starttls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password or "")
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Falha ao enviar convite SKY para %s.", to_email)
        return False
    return True
