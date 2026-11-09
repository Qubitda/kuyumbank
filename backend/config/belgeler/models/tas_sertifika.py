"""TasSertifikaBelgesi — Document ↔ taş satırı bağı (F6-012)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class TasSertifikaBelgesi(models.Model):
    """Tam olarak bir taş satırına (katalog veya teklif) bağlanır."""

    document = models.OneToOneField(
        "belgeler.Document",
        on_delete=models.PROTECT,
        related_name="tas_sertifika",
    )
    urun_tasi = models.ForeignKey(
        "urunler.UrunTasi",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sertifika_belgeleri",
    )
    teklif_tas = models.ForeignKey(
        "fiyatlama.TeklifTasMaliyeti",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sertifika_belgeleri",
    )
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Taş sertifika belgesi"
        verbose_name_plural = "Taş sertifika belgeleri"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(urun_tasi__isnull=False, teklif_tas__isnull=True)
                    | models.Q(urun_tasi__isnull=True, teklif_tas__isnull=False)
                ),
                name="tassertifikabelgesi_tek_hedef",
            ),
        ]
        indexes = [
            models.Index(fields=["urun_tasi"]),
            models.Index(fields=["teklif_tas"]),
        ]

    def __str__(self) -> str:
        hedef = (
            f"UT#{self.urun_tasi_id}"
            if self.urun_tasi_id
            else f"TT#{self.teklif_tas_id}"
        )
        return f"TSB#{self.pk or '?'} DOC#{self.document_id} → {hedef}"

    def clean(self):
        super().clean()
        has_u = self.urun_tasi_id is not None
        has_t = self.teklif_tas_id is not None
        if has_u == has_t:
            raise ValidationError(
                "Tam olarak biri: urun_tasi veya teklif_tas (F6-012)."
            )
        if self.document_id and self.document.tip != "TAS_SERTIFIKA":
            raise ValidationError(
                {"document": "Document tipı TAS_SERTIFIKA olmalı."}
            )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("TasSertifikaBelgesi değişmez (F6-012).")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("TasSertifikaBelgesi silinemez.")
