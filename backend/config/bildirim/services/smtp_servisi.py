"""SMTP okuma / test / ham gönderim — parola asla loglanmaz."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, get_connection

from bildirim.models import SmtpSettings
from bildirim.services.crypto_servisi import seal_password, unseal_password

logger = logging.getLogger(__name__)

MASK = "******"


def get_or_create_singleton() -> SmtpSettings:
    obj, _ = SmtpSettings.objects.get_or_create(pk=1)
    return obj


def set_password(smtp: SmtpSettings, plain: str | None) -> None:
    """Boş/None → mevcut sealed korunur; MASK → dokunma; diğer → seal."""
    if plain is None:
        return
    plain = str(plain).strip()
    if plain == "" or plain == MASK:
        return
    smtp.password_sealed = seal_password(plain)


def password_is_set(smtp: SmtpSettings) -> bool:
    return bool(smtp.password_sealed)


def _django_email_kwargs(smtp: SmtpSettings) -> dict[str, Any]:
    """DB SMTP doluysa connection kwargs; değilse env/Django defaults."""
    if smtp.enabled and smtp.host:
        use_tls = smtp.encryption == SmtpSettings.Encryption.STARTTLS
        use_ssl = smtp.encryption == SmtpSettings.Encryption.SSL
        return {
            "backend": "django.core.mail.backends.smtp.EmailBackend",
            "host": smtp.host,
            "port": smtp.port,
            "username": smtp.username or None,
            "password": unseal_password(smtp.password_sealed) or None,
            "use_tls": use_tls,
            "use_ssl": use_ssl,
        }
    return {}


def resolve_from_email(smtp: SmtpSettings | None = None) -> tuple[str, str]:
    smtp = smtp or get_or_create_singleton()
    email = (smtp.from_email or "").strip() or getattr(
        settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"
    )
    name = (smtp.from_name or "").strip()
    return name, email


def send_raw(
    *,
    to: list[str],
    subject: str,
    body_html: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: list[str] | None = None,
) -> None:
    """Ham HTML e-posta. Parola/log yok."""
    to = [e.strip() for e in (to or []) if e and str(e).strip()]
    if not to:
        raise ValidationError("Alıcı (to) zorunlu.")
    smtp = get_or_create_singleton()
    name, from_email = resolve_from_email(smtp)
    from_hdr = f"{name} <{from_email}>" if name else from_email
    kwargs = _django_email_kwargs(smtp)
    connection = get_connection(**kwargs) if kwargs else get_connection()
    msg = EmailMultiAlternatives(
        subject=subject,
        body="",  # text fallback boş; HTML alternatif
        from_email=from_hdr,
        to=to,
        cc=[e for e in (cc or []) if e],
        bcc=[e for e in (bcc or []) if e],
        reply_to=reply_to
        or ([smtp.reply_to] if smtp.reply_to else None),
        connection=connection,
    )
    msg.attach_alternative(body_html, "text/html")
    try:
        msg.send(fail_silently=False)
    except Exception:
        logger.exception("smtp send_raw failed to_count=%s", len(to))
        raise


def test_connection(*, to_email: str) -> str:
    """Bağlantı + test maili. Hata mesajı döner veya 'ok'."""
    to_email = (to_email or "").strip()
    if not to_email:
        raise ValidationError("Test alıcısı zorunlu.")
    smtp = get_or_create_singleton()
    if smtp.enabled and smtp.host:
        password = unseal_password(smtp.password_sealed)
        try:
            if smtp.encryption == SmtpSettings.Encryption.SSL:
                server = smtplib.SMTP_SSL(smtp.host, smtp.port, timeout=15)
            else:
                server = smtplib.SMTP(smtp.host, smtp.port, timeout=15)
                if smtp.encryption == SmtpSettings.Encryption.STARTTLS:
                    server.starttls()
            if smtp.username:
                server.login(smtp.username, password or "")
            mime = MIMEMultipart("alternative")
            name, from_email = resolve_from_email(smtp)
            mime["Subject"] = "Kuyumbank SMTP test"
            mime["From"] = f"{name} <{from_email}>" if name else from_email
            mime["To"] = to_email
            mime.attach(MIMEText("<p>SMTP test OK</p>", "html", "utf-8"))
            server.sendmail(from_email, [to_email], mime.as_string())
            server.quit()
        except Exception as exc:  # noqa: BLE001
            logger.info("smtp test_connection failed: %s", type(exc).__name__)
            raise ValidationError(f"SMTP test başarısız: {exc}") from exc
        return "ok"
    # Env / console fallback
    send_raw(
        to=[to_email],
        subject="Kuyumbank SMTP test (env/console)",
        body_html="<p>SMTP test OK (Django EMAIL_* / console)</p>",
    )
    return "ok"
