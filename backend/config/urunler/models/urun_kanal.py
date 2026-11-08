from django.core.exceptions import ValidationError
from django.db import models


class UrunKanal(models.Model):
    """Ürünün hangi satış kanalında yayında olduğu.

    Tasarım notları:
    - `clean()`, ürün yayındayken (aktif/yakinda) **son aktif kanalın**
      kapatılmasını engeller. Aksi halde `Urun.yayin_durumu="aktif"` kalır
      ama ürün hiçbir kanalda satılamaz → "hayalet ürün".
    - Admin'de silme yerine pasifleştirme tercih edilir; böylece `clean()`
      her değişiklikte çalışır. `can_delete=False` admin tarafında ayarlanır.
    - Programatik `delete()` / `objects.create()` bu kontrolü atlayabilir;
      kritik geçişler `servisler` üzerinden yapılmalıdır. Bu kural form
      katmanında (admin + ileride API serializer) zorunludur.
    """

    urun = models.ForeignKey(
        "urunler.Urun", verbose_name="Ürün", related_name="kanallar",
        on_delete=models.CASCADE,
    )
    kanal = models.ForeignKey(
        "tanimlar.SatisKanali", verbose_name="Kanal", related_name="urun_kanallari",
        on_delete=models.PROTECT,
    )
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Ürün kanalı"
        verbose_name_plural = "Ürün kanalları"
        constraints = [
            models.UniqueConstraint(fields=["urun", "kanal"], name="benzersiz_urun_kanal"),
        ]

    def clean(self):
        super().clean()
        errors = {}

        # Sadece pasifleştirme senaryosunda kontrol et
        if not self.aktif and self.urun_id:
            urun = self.urun

            # Ürün yayındaysa ve bu son aktif kanal ise engelle
            if urun.yayin_durumu in ("aktif", "yakinda"):
                diger_aktif = urun.kanallar.filter(aktif=True)
                if self.pk:
                    diger_aktif = diger_aktif.exclude(pk=self.pk)

                if not diger_aktif.exists():
                    errors["aktif"] = (
                        "Bu, ürünün tek aktif satış kanalı. Önce ürünü pasife alın "
                        "veya başka bir kanal açın."
                    )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.urun.platform_kodu} → {self.kanal}"