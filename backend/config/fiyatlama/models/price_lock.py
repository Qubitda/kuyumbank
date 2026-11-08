"""PriceLock — değişmez PriceQuote referansının geçerlilik/kilit kaydı (ADR-0008 / ADR-0010).

Sipariş FK yok (Faz 4). Yeniden fiyat hesaplamaz.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PriceLock(models.Model):
    """Kabul edilmiş PriceQuote fiyatının kilit başlığı (proforma kilit)."""

    class Durum(models.TextChoices):
        AKTIF = "AKTIF", "Aktif"
        SURESI_DOLDU = "SURESI_DOLDU", "Süresi doldu"

    quote = models.OneToOneField(
        "fiyatlama.PriceQuote",
        on_delete=models.PROTECT,
        related_name="price_lock",
    )
    alici_firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="price_locks",
        help_text="Denormalize tenant scope; quote.alici_firma ile eşit olmalı.",
    )

    # Snapshot tutarlılık kopyası (yeniden hesap yok; quote ile birebir)
    toplam_vergisiz = models.DecimalField(max_digits=18, decimal_places=2)
    para_birimi = models.CharField(max_length=3)

    kilit_zamani = models.DateTimeField()
    gecerlilik_sonu = models.DateTimeField(
        help_text="Quote penceresi ile aynı; uzatılamaz (L-04)."
    )
    durum = models.CharField(
        max_length=16,
        choices=Durum.choices,
        default=Durum.AKTIF,
    )
    idempotency_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="İsteğe bağlı istemci anahtarı; firma içinde unique.",
    )

    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_price_locks",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    # Servis bayrağı: yalnız AKTIF→SURESI_DOLDU geçişine izin
    _allow_expire_transition = False

    class Meta:
        verbose_name = "Fiyat kilidi"
        verbose_name_plural = "Fiyat kilitleri"
        ordering = ["-kilit_zamani", "-pk"]
        permissions = [
            ("lock_quote", "Kendi firma PriceQuote kayıtları için PriceLock oluşturabilir"),
            (
                "lock_quote_on_behalf",
                "Alıcı firma adına PriceLock oluşturabilir (platform on-behalf)",
            ),
        ]
        indexes = [
            models.Index(fields=["alici_firma", "-kilit_zamani"]),
            models.Index(fields=["durum", "gecerlilik_sonu"]),
            models.Index(fields=["gecerlilik_sonu"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(toplam_vergisiz__gte=0),
                name="pricelock_toplam_vergisiz_negatif_degil",
            ),
            models.CheckConstraint(
                condition=models.Q(durum__in=["AKTIF", "SURESI_DOLDU"]),
                name="pricelock_durum_gecerli",
            ),
            models.CheckConstraint(
                condition=models.Q(kilit_zamani__lte=models.F("gecerlilik_sonu")),
                name="pricelock_kilit_le_gecerlilik",
            ),
            models.UniqueConstraint(
                fields=["alici_firma", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False)
                & ~models.Q(idempotency_key=""),
                name="pricelock_firma_idempotency_uniq",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"PL#{self.pk or '?'} Q#{self.quote_id} "
            f"{self.durum} {self.toplam_vergisiz} {self.para_birimi}"
        )

    def is_gecerli(self, *, now=None) -> bool:
        """Aktif ve süre dolmamış. Zaman çelişkisinde False (durum güncellemesi ayrı)."""
        now = now or timezone.now()
        if self.durum != self.Durum.AKTIF:
            return False
        return now < self.gecerlilik_sonu

    def clean(self):
        """L-04: gecerlilik_sonu ve alici_firma quote ile birebir eşit olmalı."""
        super().clean()
        if not self.quote_id:
            return

        quote = getattr(self, "quote", None)
        if quote is None or getattr(quote, "pk", None) != self.quote_id:
            from fiyatlama.models import PriceQuote

            try:
                quote = PriceQuote.objects.only(
                    "pk", "gecerlilik_sonu", "alici_firma_id"
                ).get(pk=self.quote_id)
            except PriceQuote.DoesNotExist as exc:
                raise ValidationError({"quote": "PriceQuote bulunamadı."}) from exc

        errors = {}
        if self.gecerlilik_sonu != quote.gecerlilik_sonu:
            errors["gecerlilik_sonu"] = (
                "PriceLock.gecerlilik_sonu Quote ile eşit olmalı (ADR-0010 L-04)."
            )
        if (
            self.alici_firma_id
            and self.alici_firma_id != quote.alici_firma_id
        ):
            errors["alici_firma"] = (
                "PriceLock.alici_firma Quote ile eşit olmalı (ADR-0010 L-04)."
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean()
            super().save(*args, **kwargs)
            return

        if self._allow_expire_transition:
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and set(update_fields) <= {"durum"}:
                super().save(*args, **kwargs)
                return
            raise ValidationError(
                "PriceLock expire geçişi yalnız durum alanı ile yapılır (ADR-0010 L-08)."
            )

        raise ValidationError(
            "PriceLock değişmez; UPDATE yasak (yalnız servis expire) (ADR-0010 L-08)."
        )

    def delete(self, *args, **kwargs):
        raise ValidationError("PriceLock değişmez; DELETE yasak (ADR-0010 L-08).")
