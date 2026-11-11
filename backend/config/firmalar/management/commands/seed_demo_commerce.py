"""Demo katalog + teklif + alıcı sözleşme + stok (portal inceleme). Idempotent."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import FiyatSozlesmesi, FiyatSozlesmesiKalemi, TedarikciTeklif
from fiyatlama.services import sozlesme_servisi
from stok.models import StockMovement
from stok.services import ledger_servisi, warehouse_servisi
from tanimlar.models import (
    AyarMilyem,
    KiymetliMetal,
    KurPolitikasi,
    KurSaglayici,
    KurTipi,
    MetalKuru,
    SatisKanali,
)
from urunler.models import Kategori, Renk, Urun, Varyant

User = get_user_model()

DEMO_PASSWORD = "DemoPortal1!"


class Command(BaseCommand):
    help = "DEMO firmalar için yayınlı ürün/varyant/teklif/sözleşme/stok (idempotent)."

    def handle(self, *args, **options):
        seed_role_permissions()
        platform = ensure_platform_firma()
        alici = Firma.objects.filter(firma_kodu="DEMO_ALICI").first()
        ted = Firma.objects.filter(firma_kodu="DEMO_TEDARIKCI").first()
        if alici is None or ted is None:
            self.stderr.write("Önce: python manage.py seed_demo_portals")
            return

        ops = User.objects.filter(username="demo_ops").first()
        if ops is None:
            ops = User(
                username="demo_ops",
                firma=platform,
                rol=roles.PLATFORM_OPS,
                is_staff=True,
            )
            ops.set_password(DEMO_PASSWORD)
            ops.save()
            sync_user_role_groups(ops)

        # Sözleşme aktifleştirme için manage_sozlesme
        finance = User.objects.filter(username="demo_finance").first()
        if finance is None:
            finance = User(
                username="demo_finance",
                firma=platform,
                rol=roles.PLATFORM_FINANCE,
                is_staff=True,
            )
            finance.set_password(DEMO_PASSWORD)
            finance.save()
        else:
            finance.firma = platform
            finance.rol = roles.PLATFORM_FINANCE
            finance.is_active = True
            finance.set_password(DEMO_PASSWORD)
            finance.save()
        sync_user_role_groups(finance)
        if finance.email_verified_at is None:
            finance.email_verified_at = timezone.now()
            finance.save(update_fields=["email_verified_at"])

        buyer = User.objects.filter(username="demo_alici").first()
        supplier = User.objects.filter(username="demo_tedarikci").first()
        if buyer is None or supplier is None:
            self.stderr.write("demo_alici / demo_tedarikci yok — seed_demo_portals.")
            return

        metal = KiymetliMetal.objects.filter(gram_bazli=True).order_by("pk").first()
        ayar = (
            AyarMilyem.objects.filter(metal=metal).order_by("pk").first()
            if metal
            else None
        )
        if metal is None or ayar is None:
            self.stderr.write("Metal/ayar yok — seed_tanimlar.")
            return

        kanal = SatisKanali.objects.filter(aktif=True).order_by("sira", "pk").first()
        if kanal is None:
            self.stderr.write("SatisKanali yok — seed_tanimlar.")
            return
        if not kanal.quote_ttl_saniye:
            kanal.quote_ttl_saniye = 300
            kanal.save(update_fields=["quote_ttl_saniye"])
        SatisKanali.objects.filter(aktif=True).filter(
            quote_ttl_saniye__isnull=True
        ).update(quote_ttl_saniye=300)

        kat = Kategori.objects.order_by("pk").first()
        if kat is None:
            self.stderr.write("Kategori yok — seed_urunler.")
            return

        # Kur feed (quote metal hesabı)
        KurSaglayici.objects.filter(aktif=True).exclude(kod="DEMO_FEED").update(
            aktif=False
        )
        sag, _ = KurSaglayici.objects.update_or_create(
            kod="DEMO_FEED",
            defaults={"ad": "Demo Feed", "aktif": True, "max_gecikme_saniye": 3600},
        )
        KurPolitikasi.objects.get_or_create(
            anahtar="default",
            defaults={
                "alici_kur_tipi": KurTipi.SATIS,
                "tedarikci_kur_tipi": KurTipi.ALIS,
            },
        )
        now = timezone.now()
        for tip, price in ((KurTipi.SATIS, "4200.0000"), (KurTipi.ALIS, "4100.0000")):
            if not MetalKuru.objects.filter(
                metal=metal, saglayici=sag, kur_tipi=tip
            ).exists():
                MetalKuru.objects.create(
                    metal=metal,
                    saglayici=sag,
                    kur_tipi=tip,
                    zaman=now,
                    alinma_zamani=now,
                    saf_birim_fiyat=Decimal(price),
                    kaynak="api",
                )

        urun, created = Urun.objects.get_or_create(
            platform_kodu="DEMO-YZK-001",
            defaults={
                "olusturan_firma": platform,
                "ad": "Demo 14K Yüzük",
                "aciklama": "Portal inceleme ürünü (kör havuz).",
                "kategori": kat,
                "ayar": ayar,
            },
        )
        if not created:
            urun.ad = "Demo 14K Yüzük"
            urun.kategori = kat
            urun.ayar = ayar
            urun.save()
        Urun.objects.filter(pk=urun.pk).update(
            onay_durumu="onayli",
            yayin_durumu="aktif",
            onaylayan_kullanici=ops,
            onay_zamani=now,
        )
        urun.refresh_from_db()

        renkler = list(Renk.objects.order_by("pk")[:5])
        if len(renkler) < 3:
            self.stderr.write("En az 3 Renk gerekli — seed_urunler.")
            return
        # Unique (urun, renk) when beden null — her varyanta ayrı renk.
        variants_spec = [
            ("DEMO-YZK-001-A", Decimal("2.500"), renkler[0]),
            ("DEMO-YZK-001-B", Decimal("3.000"), renkler[1]),
            ("DEMO-YZK-001-C", Decimal("2.500"), renkler[2]),
        ]
        varyantlar = []
        for sku, gram, renk in variants_spec:
            v = Varyant.objects.filter(urun=urun, sku=sku).first()
            if v is None:
                v = Varyant(
                    urun=urun,
                    sku=sku,
                    gram=gram,
                    renk=renk,
                    ek_bedel=Decimal("10.00"),
                    aktif=True,
                )
                v.save()
            else:
                v.gram = gram
                v.renk = renk
                v.aktif = True
                v.save()
            varyantlar.append(v)

        bas, bit = date.today(), date.today() + timedelta(days=90)
        soz = (
            FiyatSozlesmesi.objects.filter(
                firma=alici,
                kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
                satis_kanali=kanal,
            )
            .order_by("-versiyon")
            .first()
        )
        if soz is None:
            soz = FiyatSozlesmesi.objects.create(
                firma=alici,
                kontrat_tipi=FiyatSozlesmesi.KontratTipi.ALICI,
                satis_kanali=kanal,
                gecerlilik_baslangic=bas,
                gecerlilik_bitis=bit,
                durum=FiyatSozlesmesi.Durum.TASLAK,
                olusturan_kullanici=ops,
                versiyon=1,
            )
        if not soz.kalemler.exists():
            FiyatSozlesmesiKalemi.objects.create(
                sozlesme=soz,
                metal=metal,
                ayar=ayar,
                marj_tipi=FiyatSozlesmesiKalemi.MarjTipi.TL_PARCA,
                marj_degeri=Decimal("50.00"),
                iscilik=Decimal("100.00"),
            )
        if soz.durum != FiyatSozlesmesi.Durum.AKTIF:
            sozlesme_servisi.aktif_yap(soz, finance)

        wh = None
        for i, varyant in enumerate(varyantlar):
            teklif = TedarikciTeklif.objects.filter(
                varyant=varyant, tedarikci=ted, durum=TedarikciTeklif.Durum.YAYINDA
            ).first()
            if teklif is None:
                teklif = TedarikciTeklif.objects.create(
                    varyant=varyant,
                    tedarikci=ted,
                    tedarikci_kodu=f"DEMO-{i+1}",
                    fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
                    gram=varyant.gram,
                    durum=TedarikciTeklif.Durum.YAYINDA,
                    gecerlilik_baslangic=bas,
                    gecerlilik_bitis=bit,
                    eslestirme_durumu="onaylandi",
                    hedef_urun=urun,
                    oncelik=10,
                    iscilik_override=Decimal("80.00"),
                )
            if wh is None:
                try:
                    wh = warehouse_servisi.olustur_warehouse(
                        actor=supplier,
                        sahip_firma=ted,
                        kod="DEMOWH",
                        ad="Demo tedarikçi depo",
                    )
                except Exception:
                    from stok.models import Warehouse

                    wh = Warehouse.objects.filter(
                        sahip_firma=ted, kod="DEMOWH"
                    ).first()
            if wh is not None:
                from stok.models import StockBalance

                bal = StockBalance.objects.filter(
                    warehouse=wh, teklif=teklif
                ).first()
                if bal is None or bal.on_hand < Decimal("10"):
                    ledger_servisi.kaydet_hareket(
                        actor=supplier,
                        warehouse=wh,
                        teklif=teklif,
                        tip=StockMovement.Tip.GIRIS,
                        miktar=Decimal("50"),
                    )

        self.stdout.write(self.style.SUCCESS("seed_demo_commerce tamam."))
        self.stdout.write(
            f"  Ürün #{urun.pk} {urun.platform_kodu} · {len(varyantlar)} varyant"
        )
        self.stdout.write(f"  Kanal #{kanal.pk} {kanal.kod} · sözleşme #{soz.pk}")
