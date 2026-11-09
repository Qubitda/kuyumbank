"""Document — tenant’lı belge metadata (F6-012 / F6-K10). Binary storage yok."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Document(models.Model):
    class Tip(models.TextChoices):
        TAS_SERTIFIKA = "TAS_SERTIFIKA", "Taş sertifikası"
        DIGER = "DIGER", "Diğer"

    firma = models.ForeignKey(
        "firmalar.Firma",
        on_delete=models.PROTECT,
        related_name="documents",
        help_text="Tenant sahibi; client firma_id güvenilmez.",
    )
    tip = models.CharField(max_length=32, choices=Tip.choices)
    baslik = models.CharField(max_length=120)
    storage_key = models.CharField(
        max_length=255,
        help_text="Harici object key / URI; dosya binary bu tabloda yok (K-014).",
    )
    content_type = models.CharField(max_length=64, blank=True)
    byte_size = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    olusturan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="olusturdugu_documents",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Belge"
        verbose_name_plural = "Belgeler"
        ordering = ["-olusturma_tarihi", "-pk"]
        permissions = [
            ("manage_document", "Belge metadata yönetebilir"),
        ]
        indexes = [
            models.Index(fields=["firma", "tip"]),
            models.Index(fields=["storage_key"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tip__in=["TAS_SERTIFIKA", "DIGER"]),
                name="document_tip_gecerli",
            ),
            models.CheckConstraint(
                condition=~models.Q(storage_key=""),
                name="document_storage_key_dolu",
            ),
        ]

    def __str__(self) -> str:
        return f"DOC#{self.pk or '?'} {self.tip} {self.baslik}"

    def clean(self):
        super().clean()
        if not (self.storage_key or "").strip():
            raise ValidationError({"storage_key": "storage_key zorunlu."})
        if not (self.baslik or "").strip():
            raise ValidationError({"baslik": "Başlık zorunlu."})

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Document metadata append-ish; UPDATE yasak (F6-012). Yeniden bağlayın."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Document silinemez (F6-012).")
