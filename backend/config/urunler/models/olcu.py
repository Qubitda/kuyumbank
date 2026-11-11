from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class OlcuDegeri(models.Model):
    """Ölçü değeri (yüzük numarası, bilezik boyu, zincir uzunluğu...).

    Tasarım notları:
    - `sayisal_deger` ile `deger` (görünen metin) tutarlı olmalıdır. `clean()`
      bu tutarlılığı denetler: yüzük için "14 No" ile 14.00 uyumlu olmalı;
      cm ölçülerde "45 cm" ile 45.00 uyumlu olmalı.
    - `sayisal_deger` DB seviyesinde de pozitif olmaya zorlanır.
    - `Meta.ordering` artık yalnızca `tip` + `sayisal_deger` üzerinden çalışır;
      `sira` alanı sadece admin/liste düzeninde görsel öncelik sağlar. Bu sayede
      kullanıcı `sira`'yı unutsa bile liste doğru sırada görünür.
    - `mm_cevre` ve `us_olcu` dönüşümleri **Türkiye yüzük ölçüsü standardı**
      varsayımıyla çalışır (TR: çevre mm = numara + 40). Başka ülke standardı
      gerekiyorsa ayrı bir `standart` alanı eklenmelidir.
    """

    TIP = [
        ("yuzuk_no", _("Yüzük numarası")),
        ("bilezik_boyu", _("Bilezik boyu (cm)")),
        ("zincir_uzunlugu", _("Zincir / kolye uzunluğu (cm)")),
        ("bileklik_boyu", _("Bileklik boyu (cm)")),
    ]

    # Tipe göre beklenen metin formatı (clean() doğrulaması için)
    _BEKLENEN_BIRIM = {
        "yuzuk_no": ("No", "numara", "no"),
        "bilezik_boyu": ("cm",),
        "zincir_uzunlugu": ("cm",),
        "bileklik_boyu": ("cm",),
    }

    tip = models.CharField(_("Ölçü tipi"), max_length=15, choices=TIP)

    sayisal_deger = models.DecimalField(
        _("Sayısal Değer"),
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Örn: 14.00, 19.00, 45.00"),
    )

    deger = models.CharField(
        _("Görüntü Değeri"),
        max_length=20,
        help_text=_("Örn: 14 No, 19 cm, 45 cm"),
    )

    sira = models.PositiveIntegerField(_("Sıra"), default=0)
    aktif = models.BooleanField(_("Aktif"), default=True)

    entegrasyon_kodu = models.CharField(
        _("ERP / Entegrasyon Kodu"),
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Ölçü değeri")
        verbose_name_plural = _("Ölçü değerleri")
        # `sira` yerine `sayisal_deger` öncelikli: kullanıcı sira'yı unutsa da
        # liste doğru sırada gelsin.
        ordering = ["tip", "sayisal_deger", "sira"]
        constraints = [
            models.UniqueConstraint(
                fields=["tip", "sayisal_deger"],
                name="benzersiz_olcu_tip_sayisal",
            ),
            models.CheckConstraint(
                condition=models.Q(sayisal_deger__gt=0),
                name="olcu_sayisal_deger_pozitif",
            ),
        ]

    # ------------------------------------------------------------------ #
    # Validasyon
    # ------------------------------------------------------------------ #
    def clean(self):
        super().clean()
        errors = {}

        # 1) Görünen metni normalize et
        if self.deger:
            self.deger = self.deger.strip()

        # 2) sayisal_deger geçerli mi?
        if self.sayisal_deger is None:
            errors["sayisal_deger"] = "Sayısal değer zorunludur."
        else:
            try:
                sayisal = Decimal(self.sayisal_deger)
                if sayisal <= 0:
                    errors["sayisal_deger"] = "Sayısal değer sıfırdan büyük olmalıdır."
            except (InvalidOperation, TypeError):
                errors["sayisal_deger"] = "Sayısal değer geçerli bir sayı olmalıdır."

        # 3) tip ↔ deger formatı uyumu
        if self.tip and self.deger and "sayisal_deger" not in errors:
            beklenen = self._BEKLENEN_BIRIM.get(self.tip, ())
            deger_lower = self.deger.lower()
            # Metin, sayısal değeri içermeli (14, 45 vb.)
            # Örn: sayisal=14.00, deger="14 No" → "14" içerir ✅
            # Örn: sayisal=14.00, deger="16 No" → uyumsuz ❌
            sayisal_str_varyantlari = {
                str(int(self.sayisal_deger)),
                f"{self.sayisal_deger.normalize()}",
                f"{self.sayisal_deger:.0f}",
                f"{self.sayisal_deger:.2f}".rstrip("0").rstrip("."),
            }
            if not any(s in self.deger for s in sayisal_str_varyantlari):
                errors["deger"] = (
                    f"Görünen değer, sayısal değerle ({self.sayisal_deger}) uyumlu olmalı "
                    f"(örn. '{self.sayisal_deger:.0f} No' veya '{self.sayisal_deger:.0f} cm')."
                )
            elif beklenen and not any(birim in deger_lower for birim in beklenen):
                errors["deger"] = (
                    f"Bu ölçü tipi için beklenen birim: {', '.join(beklenen)}. "
                    f"Örn: '{self.sayisal_deger:.0f} {beklenen[0]}'."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # NOT: full_clean() bilinçli olarak çağrılmıyor. Validasyon form/servis
        # katmanında yapılır; böylece bulk_create ve veri migration'ları engellenmez.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tip_display()}: {self.deger}"

    # ------------------------------------------------------------------ #
    # Dönüşümler (Türkiye yüzük ölçüsü standardı varsayımıyla)
    # ------------------------------------------------------------------ #
    @property
    def mm_cevre(self):
        """Yüzük iç çevresi (mm). TR standardı: çevre = numara + 40."""
        if self.tip == "yuzuk_no" and self.sayisal_deger is not None:
            return self.sayisal_deger + Decimal("40")
        return None

    @property
    def us_olcu(self):
        """ABD yüzük ölçüsüne yaklaşık dönüşüm (Decimal; vitrin bilgisi).

        Not: kesin dönüşüm üreticiye göre değişir; sipariş/faturalamada
        TR numarası esas alınmalıdır.
        """
        if self.tip == "yuzuk_no" and self.sayisal_deger is not None:
            # ((n * 0.83) - 4.80) 1/4 adımına yuvarla
            raw = (self.sayisal_deger * Decimal("0.83")) - Decimal("4.80")
            return (raw * 4).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            ) / Decimal("4")
        return None