import uuid

from django.db import migrations


def forwards(apps, schema_editor):
    Firma = apps.get_model("firmalar", "Firma")
    Kullanici = apps.get_model("firmalar", "Kullanici")
    Group = apps.get_model("auth", "Group")

    platform = Firma.objects.filter(platform_mu=True).first()
    if platform is None:
        platform = Firma.objects.filter(firma_kodu="PLATFORM").first()
    if platform is None:
        platform = Firma.objects.create(
            ad="Kuyumbank Platform",
            unvan="Kuyumbank Platform",
            firma_kodu="PLATFORM",
            platform_mu=True,
            aktif=True,
            onay_durumu="onayli",
        )
    elif not platform.firma_kodu:
        platform.firma_kodu = "PLATFORM"
        platform.save(update_fields=["firma_kodu"])

    for firma in Firma.objects.filter(firma_kodu__isnull=True):
        firma.firma_kodu = f"F{firma.pk:05d}"
        firma.save(update_fields=["firma_kodu"])
    for firma in Firma.objects.filter(firma_kodu=""):
        firma.firma_kodu = f"F{firma.pk:05d}"
        firma.save(update_fields=["firma_kodu"])

    # Unique çakışma koruması
    seen = set()
    for firma in Firma.objects.exclude(firma_kodu__isnull=True).exclude(firma_kodu=""):
        if firma.firma_kodu in seen:
            firma.firma_kodu = f"{firma.firma_kodu}-{uuid.uuid4().hex[:6]}"
            firma.save(update_fields=["firma_kodu"])
        seen.add(firma.firma_kodu)

    # Firmasız kullanıcılar: yalnız rolü BOŞ superuser/staff platforma bağlanır.
    # Rolü dolu (veya normal kullanıcı) firmasızsa → migration DURUR.
    bindable = []
    blocked = []
    for user in Kullanici.objects.filter(firma__isnull=True):
        rol = (user.rol or "").strip()
        if not rol and (user.is_superuser or user.is_staff):
            bindable.append(user)
        else:
            blocked.append(user)

    if blocked:
        names = ", ".join(sorted(u.username for u in blocked))
        raise RuntimeError(
            "Firmasız kullanıcı(lar) platform firmasına otomatik bağlanamaz "
            f"(rolü dolu veya staff/superuser değil): {names}. "
            "Önce `python manage.py audit_user_assignments` çalıştırın; "
            "çıktıdaki firma/rol eksiklerini düzeltip migration'ı yeniden deneyin."
        )

    for user in bindable:
        user.firma = platform
        user.rol = "platform_super"
        user.save(update_fields=["firma", "rol"])

    for user in Kullanici.objects.filter(rol=""):
        user.rol = "platform_super" if user.firma_id == platform.id else user.rol
        if not user.rol:
            raise RuntimeError(
                f"Boş rollü kullanıcı backfill edilemedi: {user.username}. "
                "Önce `python manage.py audit_user_assignments` çalıştırın."
            )
        user.save(update_fields=["rol"])

    # Rol grup iskeleti (permission seed migrate sonrası komutla dolar)
    for code, _label in [
        ("platform_super", ""),
        ("platform_admin", ""),
        ("platform_ops", ""),
        ("platform_finance", ""),
        ("platform_catalog", ""),
        ("platform_quality", ""),
        ("platform_logistics", ""),
        ("platform_support", ""),
    ]:
        Group.objects.get_or_create(name=f"rol:{code}")


def backwards(apps, schema_editor):
    # Veri geri alınmaz; güvenli no-op
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("firmalar", "0002_faz1_kimlik_rbac"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
