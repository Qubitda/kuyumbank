"""O2: urun_kimlik_ab_anahtar_uniq — reddedildi hariç (ADR-0006).

İleri yön daha gevşek (reddedildi çiftlerine izin); mevcut veriyi bozmaz.
Reverse: eski sıkı kısıta dönüş; çakışma varsa satır silmeden durur.
"""

from django.db import migrations, models
from django.db.models import Count


def _noop_forward(apps, schema_editor):
    # İleri yön veri silmez / dönüştürmez; kısıt gevşemesi güvenli.
    pass


def _reverse_check_no_collision(apps, schema_editor):
    """Eski (reddedildi dahil) unique geri gelmeden önce çakışma kontrolü."""
    Urun = apps.get_model("urunler", "Urun")
    dupes = (
        Urun.objects.filter(kimlik_sinifi__in=["A", "B"])
        .exclude(kimlik_anahtari="")
        .values("kimlik_sinifi", "kimlik_anahtari")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    if dupes.exists():
        raise RuntimeError(
            "Kimlik kısıtı geri alınamaz; çakışan kayıtlar var. "
            "Satır silinmedi. Veriyi düzeltip tekrar deneyin."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("urunler", "0006_faz2_index_names"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="urun",
            name="urun_kimlik_ab_anahtar_uniq",
        ),
        migrations.AddConstraint(
            model_name="urun",
            constraint=models.UniqueConstraint(
                condition=(
                    models.Q(kimlik_sinifi__in=["A", "B"])
                    & ~models.Q(kimlik_anahtari="")
                    & ~models.Q(onay_durumu="reddedildi")
                ),
                fields=("kimlik_sinifi", "kimlik_anahtari"),
                name="urun_kimlik_ab_anahtar_uniq",
            ),
        ),
        # Reverse sırası: önce bu reverse_code → sonra yeni kısıt kalkar → eski kısıt eklenir.
        # check, yeni kısıt hâlâ varken çalışır; veri çakışmasını tespit eder.
        migrations.RunPython(_noop_forward, _reverse_check_no_collision),
    ]
