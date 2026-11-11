"""Sandbox soft-launch (yol A) hazırlık kontrolü — secret değeri yazmaz."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Sandbox soft-launch checklist: DEBUG/cache/MFA/fake/SMTP/cron komutları. "
        "Secret değer basılmaz."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Uyarıları da exit code 1 yap (CI/staging kapısı).",
        )
        parser.add_argument(
            "--require-mfa",
            action="store_true",
            help="MFA_ENFORCE_PLATFORM=False → fail (prod soft-launch).",
        )
        parser.add_argument(
            "--allow-fake",
            action="store_true",
            help="Sandbox A: fake ödeme/kargo bilinçli kabul (uyarı değil bilgi).",
        )

    def handle(self, *args, **options):
        strict = bool(options["strict"])
        require_mfa = bool(options["require_mfa"])
        allow_fake = bool(options["allow_fake"])
        errors: list[str] = []
        warnings: list[str] = []
        infos: list[str] = []

        debug = bool(getattr(settings, "DEBUG", False))
        if debug:
            warnings.append("DEBUG=True (sandbox OK; prod soft-launch için False).")
        else:
            infos.append("DEBUG=False")

        hosts = getattr(settings, "ALLOWED_HOSTS", None) or []
        if not debug and not hosts:
            errors.append("ALLOWED_HOSTS boş (DEBUG=False).")
        else:
            infos.append(f"ALLOWED_HOSTS count={len(hosts)}")

        # Cache backend
        caches = getattr(settings, "CACHES", {}) or {}
        backend = str((caches.get("default") or {}).get("BACKEND") or "")
        locmem = "locmem" in backend.lower()
        if locmem:
            if debug:
                infos.append("Cache=LocMem (DEBUG).")
            elif getattr(settings, "ALLOW_LOCMEM_CACHE", False):
                warnings.append("Cache=LocMem + ALLOW_LOCMEM_CACHE (bilinçli).")
            else:
                errors.append("Cache=LocMem prod'da yasak → DatabaseCache + createcachetable.")
        else:
            infos.append(f"Cache backend={backend.rsplit('.', 1)[-1]}")
            # smoke set/get
            try:
                cache.set("soft_launch_ping", "1", 5)
                if cache.get("soft_launch_ping") != "1":
                    warnings.append("Cache set/get doğrulanamadı.")
                else:
                    infos.append("Cache set/get OK")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Cache erişim hatası: {type(exc).__name__}")

        # MFA
        mfa = bool(getattr(settings, "MFA_ENFORCE_PLATFORM", False))
        if mfa:
            infos.append("MFA_ENFORCE_PLATFORM=True")
        elif require_mfa:
            errors.append("MFA_ENFORCE_PLATFORM=False (--require-mfa).")
        else:
            warnings.append("MFA_ENFORCE_PLATFORM=False (platform/act-as tek faktör).")

        # Fake providers
        pay = (getattr(settings, "PAYMENT_PROVIDER", "") or "").lower()
        car = (getattr(settings, "CARRIER_PROVIDER", "") or "").lower()
        allow_fake_setting = bool(getattr(settings, "ALLOW_FAKE_PROVIDERS", False))
        if pay == "fake" or car == "fake":
            msg = f"PAYMENT_PROVIDER={pay} CARRIER_PROVIDER={car}"
            if allow_fake or allow_fake_setting:
                infos.append(f"Sandbox fake providers OK ({msg}).")
            elif not debug:
                errors.append(
                    f"Fake provider prod: {msg}. ALLOW_FAKE_PROVIDERS=1 (yol A) "
                    "veya gerçek adaptör (yol B)."
                )
            else:
                infos.append(f"DEBUG fake providers ({msg}).")

        # SMTP / email
        email_backend = str(getattr(settings, "EMAIL_BACKEND", "") or "")
        if "console" in email_backend.lower():
            warnings.append(
                "EMAIL_BACKEND=console — reset/MFA/order mailleri yalnız log."
            )
        else:
            infos.append(f"EMAIL_BACKEND={email_backend.rsplit('.', 1)[-1]}")

        reset_base = (getattr(settings, "PASSWORD_RESET_BASE_URL", "") or "").strip()
        if not reset_base:
            warnings.append("PASSWORD_RESET_BASE_URL boş — reset linki göreli/API notu.")
        else:
            infos.append("PASSWORD_RESET_BASE_URL set")

        # Cron commands registered
        from django.core.management import get_commands

        cmds = get_commands()
        for name in (
            "process_outbox",
            "process_email_queue",
            "expire_stale_reservations",
            "purge_expired_tokens",
            "purge_idempotency_records",
        ):
            if name in cmds:
                infos.append(f"cmd OK: {name}")
            else:
                errors.append(f"Management command eksik: {name}")

        # Secret presence only (no value)
        sk = getattr(settings, "SECRET_KEY", "") or ""
        if not sk or sk.startswith("change-me"):
            errors.append("SECRET_KEY zayıf/placeholder.")
        else:
            infos.append("SECRET_KEY set (değer yazılmaz)")

        for line in infos:
            self.stdout.write(self.style.SUCCESS(f"OK  {line}"))
        for line in warnings:
            self.stdout.write(self.style.WARNING(f"WARN {line}"))
        for line in errors:
            self.stdout.write(self.style.ERROR(f"ERR  {line}"))

        self.stdout.write("")
        self.stdout.write(
            f"soft_launch_check: errors={len(errors)} warnings={len(warnings)} "
            f"infos={len(infos)}"
        )
        if errors or (strict and warnings):
            raise CommandError("soft_launch_check failed")
