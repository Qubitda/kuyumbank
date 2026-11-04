"""Ürün formundaki basit seçim listeleri. Hiçbirini fiyat motoru okumaz.

Hepsi aynı şekilde (kod, ad, sıra, aktif) olduğu için tek dosyada tutuldu; her biri
yine ayrı tablodur, böylece bir alana yanlış listeden değer bağlanamaz.
"""
from .taban import KatalogTanimTaban


class Koleksiyon(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Koleksiyon"
        verbose_name_plural = "Koleksiyonlar"


class Renk(KatalogTanimTaban):
    """Metalin rengi (sarı, beyaz, rose...). Varyant ekseni."""

    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Renk"
        verbose_name_plural = "Renkler"


class YasGrubu(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Yaş grubu"
        verbose_name_plural = "Yaş grupları"


class Teknik(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Teknik"
        verbose_name_plural = "Teknikler"


class Stil(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Stil"
        verbose_name_plural = "Stiller"


class OzelGun(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Özel gün"
        verbose_name_plural = "Özel günler"


class ZincirTipi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Zincir tipi"
        verbose_name_plural = "Zincir tipleri"


class KopcaTipi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Kopça tipi"
        verbose_name_plural = "Kopça tipleri"


class TasTipi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Taş tipi"
        verbose_name_plural = "Taş tipleri"


class TasKesimi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Taş kesimi"
        verbose_name_plural = "Taş kesimleri"


class MihlamaTipi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Mıhlama tipi"
        verbose_name_plural = "Mıhlama tipleri"


class TasMensei(KatalogTanimTaban):
    """Doğal / laboratuvar üretimi / simülant. Yasal etiketleme için ayrı tutulur."""

    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Taş menşei"
        verbose_name_plural = "Taş menşeleri"


class SertifikaKurumu(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Sertifika kurumu"
        verbose_name_plural = "Sertifika kurumları"


class Berraklik(KatalogTanimTaban):
    """Sıra önemli: FL en yüksek, I1 en düşük. `sira` alanını bozma."""

    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Berraklık"
        verbose_name_plural = "Berraklıklar"


class RenkDerecesi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Renk derecesi"
        verbose_name_plural = "Renk dereceleri"


class KesimKalitesi(KatalogTanimTaban):
    class Meta(KatalogTanimTaban.Meta):
        verbose_name = "Kesim kalitesi"
        verbose_name_plural = "Kesim kaliteleri"
