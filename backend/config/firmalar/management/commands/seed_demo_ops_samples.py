"""Her ana operasyon adımı için 1 örnek kayıt (portal inceleme).

Önkoşul: seed_demo_portals + seed_tanimlar + seed_urunler (+ seed_demo_commerce çağrılır).
Idempotent: DEMO-* anahtarları / idempotency key ile tekrar güvenli.
"""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from firmalar import roles
from firmalar.models import Firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import PriceQuote, TedarikciTeklif
from fiyatlama.services import pricing_service
from siparis.models import CartLine, CheckoutAttempt, Order, RFQ, RFQEslestirme, RFQLine
from siparis.services import (
    cart_servisi,
    checkout_servisi,
    order_servisi,
    rfq_eslestirme_servisi,
    rfq_servisi,
)
from stok.models import StockBalance, StockMovement, Warehouse
from stok.services import ledger_servisi, warehouse_servisi
from tanimlar.models import SatisKanali
from urunler.models import Urun, Varyant

User = get_user_model()

ORDER_KEY = "demo-sample-order-v1"
CART_KEY = "demo-sample-cart-v1"
RFQ_BASLIK = "DEMO · örnek RFQ"


class Command(BaseCommand):
    help = "Operasyon adımları için tek örnek veri (sepet, sipariş, RFQ, eşleştirme, stok)."

    def handle(self, *args, **options):
        call_command("seed_demo_commerce")

        alici = Firma.objects.get(firma_kodu="DEMO_ALICI")
        ted = Firma.objects.get(firma_kodu="DEMO_TEDARIKCI")
        buyer = User.objects.get(username="demo_alici")
        supplier = User.objects.get(username="demo_tedarikci")
        ops = User.objects.get(username="demo_ops")

        # İnceleme: admin tüm ops yüzeyi (eşleştirme dahil approve_eslestirme)
        if ops.rol != roles.PLATFORM_ADMIN:
            ops.rol = roles.PLATFORM_ADMIN
            ops.is_staff = True
            ops.save(update_fields=["rol", "is_staff"])
            sync_user_role_groups(ops)

        # Depo yetkisi: satış rolü manage_own_warehouse taşımayabilir → sahip
        if supplier.rol != roles.TEDARIKCI_SAHIP:
            supplier.rol = roles.TEDARIKCI_SAHIP
            supplier.save(update_fields=["rol"])
            sync_user_role_groups(supplier)

        urun = Urun.objects.filter(platform_kodu="DEMO-YZK-001").first()
        if urun is None:
            self.stderr.write("Demo ürün yok.")
            return
        varyantlar = list(
            Varyant.objects.filter(urun=urun, aktif=True).order_by("pk")
        )
        if len(varyantlar) < 2:
            self.stderr.write("En az 2 demo varyant gerekli.")
            return
        v_order, v_cart, v_rfq = varyantlar[0], varyantlar[1], varyantlar[0]

        kanal = (
            SatisKanali.objects.filter(kod="KUYUMCU_PANEL").first()
            or SatisKanali.objects.filter(aktif=True).order_by("pk").first()
        )
        if kanal is None or not kanal.quote_ttl_saniye:
            self.stderr.write("Satış kanalı / TTL yok.")
            return

        # --- Stok / depo ---
        wh = Warehouse.objects.filter(sahip_firma=ted, kod="DEMOWH").first()
        if wh is None:
            wh = warehouse_servisi.olustur_warehouse(
                actor=supplier,
                sahip_firma=ted,
                kod="DEMOWH",
                ad="Demo tedarikçi depo",
            )
        teklifler = list(
            TedarikciTeklif.objects.filter(
                tedarikci=ted, varyant__urun=urun, durum=TedarikciTeklif.Durum.YAYINDA
            )
        )
        for teklif in teklifler:
            bal = StockBalance.objects.filter(warehouse=wh, teklif=teklif).first()
            if bal is None or bal.on_hand < Decimal("20"):
                ledger_servisi.kaydet_hareket(
                    actor=supplier,
                    warehouse=wh,
                    teklif=teklif,
                    tip=StockMovement.Tip.GIRIS,
                    miktar=Decimal("50"),
                )

        # --- 1) Açık sepet satırı (ikinci varyant) ---
        if not CartLine.objects.filter(
            cart__alici_firma=alici, varyant=v_cart
        ).exists():
            q_cart = pricing_service.quote(
                alici_firma=alici,
                satis_kanali=kanal,
                varyant=v_cart,
                kullanici=buyer,
            )
            cart_servisi.satir_ekle(
                actor=buyer, price_quote=q_cart, miktar=Decimal("1")
            )
            self.stdout.write(f"  Sepet satırı · quote #{q_cart.pk} · varyant {v_cart.sku}")
        else:
            self.stdout.write("  Sepet satırı · zaten var")

        # --- 2) Sipariş (checkout → order) ---
        order = Order.objects.filter(idempotency_key=ORDER_KEY).first()
        if order is None:
            q_ord = pricing_service.quote(
                alici_firma=alici,
                satis_kanali=kanal,
                varyant=v_order,
                kullanici=buyer,
            )
            # Ayrı sepet satırı olarak ekle (checkout tüm sepeti alır — önce cart temizliği riskli)
            # Mevcut açık sepeti bozmamak için: yalnız sipariş için temporary approach —
            # checkout sepetin tamamını işler. Bu yüzden önce cart satırlarını not al.
            existing_line_ids = list(
                CartLine.objects.filter(cart__alici_firma=alici).values_list(
                    "pk", flat=True
                )
            )
            cart_servisi.satir_ekle(
                actor=buyer, price_quote=q_ord, miktar=Decimal("1")
            )
            # Sipariş için yalnızca yeni satırı bırak: diğerlerini geçici sil
            cart = cart_servisi.al_veya_olustur_sepet(actor=buyer)
            for ln in list(cart.lines.all()):
                if ln.price_quote_id != q_ord.pk:
                    cart_servisi.satir_sil(actor=buyer, line=ln)
            result = checkout_servisi.checkout(
                actor=buyer, idempotency_key=f"{ORDER_KEY}-co"
            )
            if result.attempt.durum != CheckoutAttempt.Durum.BASARILI:
                self.stderr.write(f"Checkout başarısız: {result.attempt.durum}")
            else:
                order = order_servisi.olustur_from_checkout(
                    actor=buyer,
                    checkout_attempt=result.attempt,
                )
                Order.objects.filter(pk=order.pk).update(idempotency_key=ORDER_KEY)
                order.refresh_from_db()
                self.stdout.write(f"  Sipariş #{order.pk} · durum {order.durum}")
            # Sepet örneğini geri koy
            if not CartLine.objects.filter(
                cart__alici_firma=alici, varyant=v_cart
            ).exists():
                q_cart2 = pricing_service.quote(
                    alici_firma=alici,
                    satis_kanali=kanal,
                    varyant=v_cart,
                    kullanici=buyer,
                )
                cart_servisi.satir_ekle(
                    actor=buyer, price_quote=q_cart2, miktar=Decimal("1")
                )
            _ = existing_line_ids  # lint
        else:
            self.stdout.write(f"  Sipariş #{order.pk} · zaten var")

        # --- 3) RFQ katalog satırı (gönderilmiş) ---
        rfq = RFQ.objects.filter(alici_firma=alici, baslik=RFQ_BASLIK).first()
        if rfq is None:
            rfq = rfq_servisi.olustur(
                actor=buyer,
                baslik=RFQ_BASLIK,
                line_specs=[
                    {
                        "aciklama": "Demo RFQ · kataloglu satır",
                        "miktar": Decimal("2"),
                        "birim": "ADET",
                        "varyant": v_rfq,
                    }
                ],
                talep_tipi=RFQ.TalepTipi.STANDART,
            )
            rfq = rfq_servisi.gonder(actor=buyer, rfq=rfq)
            self.stdout.write(f"  RFQ #{rfq.pk} · {rfq.durum}")
        else:
            if rfq.durum == RFQ.Durum.TASLAK:
                rfq = rfq_servisi.gonder(actor=buyer, rfq=rfq)
            self.stdout.write(f"  RFQ #{rfq.pk} · {rfq.durum}")

        # --- 4) RFQ katalog-dışı + admin eşleştirme ---
        rfq_match_baslik = "DEMO · eşleştirme RFQ"
        rfq_m = RFQ.objects.filter(
            alici_firma=alici, baslik=rfq_match_baslik
        ).first()
        if rfq_m is None:
            rfq_m = rfq_servisi.olustur(
                actor=buyer,
                baslik=rfq_match_baslik,
                line_specs=[
                    {
                        "aciklama": "Katalog dışı · 14K ~2.5g yüzük aranıyor",
                        "miktar": Decimal("1"),
                        "birim": "ADET",
                        # varyant yok → ops eşleştirme
                    }
                ],
                talep_tipi=RFQ.TalepTipi.STANDART,
            )
            rfq_m = rfq_servisi.gonder(actor=buyer, rfq=rfq_m)
            self.stdout.write(f"  RFQ (eşleştirme) #{rfq_m.pk} · {rfq_m.durum}")
        else:
            if rfq_m.durum == RFQ.Durum.TASLAK:
                rfq_m = rfq_servisi.gonder(actor=buyer, rfq=rfq_m)
            self.stdout.write(f"  RFQ (eşleştirme) #{rfq_m.pk} · {rfq_m.durum}")

        line = (
            RFQLine.objects.filter(rfq=rfq_m, varyant__isnull=True)
            .order_by("pk")
            .first()
        )
        if line is not None:
            match = RFQEslestirme.objects.filter(rfq_line=line).first()
            if match is None:
                match = rfq_eslestirme_servisi.oner(
                    actor=ops,
                    rfq_line=line,
                    varyant=v_rfq,
                    skor=80,
                    kanit={"kaynak": "seed_demo_ops_samples"},
                )
                self.stdout.write(
                    f"  RFQ eşleştirme #{match.pk} · durum {match.durum}"
                )
            else:
                self.stdout.write(f"  RFQ eşleştirme #{match.pk} · zaten var")
        else:
            self.stdout.write("  RFQ eşleştirme · katalog-dışı satır yok")

        # --- 5) Tedarikçi taslak teklif (ek örnek, gönderilmemiş) ---
        draft_sku_var = varyantlar[-1]
        draft = TedarikciTeklif.objects.filter(
            tedarikci=ted,
            varyant=draft_sku_var,
            tedarikci_kodu="DEMO-DRAFT",
        ).first()
        if draft is None:
            from datetime import date, timedelta

            bas, bit = date.today(), date.today() + timedelta(days=60)
            draft = TedarikciTeklif.objects.create(
                varyant=draft_sku_var,
                tedarikci=ted,
                tedarikci_kodu="DEMO-DRAFT",
                fiyat_modeli=TedarikciTeklif.FiyatModeli.METAL_BAZLI,
                gram=draft_sku_var.gram,
                durum=TedarikciTeklif.Durum.TASLAK,
                gecerlilik_baslangic=bas,
                gecerlilik_bitis=bit,
                eslestirme_durumu="onaylandi",
                hedef_urun=urun,
                oncelik=1,
                iscilik_override=Decimal("70.00"),
            )
            self.stdout.write(f"  Tedarikçi taslak teklif #{draft.pk}")
        else:
            self.stdout.write(f"  Tedarikçi taslak teklif #{draft.pk} · zaten var")

        # Özet
        self.stdout.write(self.style.SUCCESS("seed_demo_ops_samples tamam."))
        self.stdout.write("")
        self.stdout.write("İnceleme haritası (şifre: DemoPortal1!):")
        self.stdout.write("  demo_alici   → /buyer/catalog · /buyer/cart · /buyer/orders · /buyer/rfqs")
        self.stdout.write("  demo_tedarikci → /supplier/offers · /supplier/stock · /supplier/rfqs")
        self.stdout.write("  demo_ops    → /admin/orders · /admin/rfq-match · /admin/offers")
        self.stdout.write(
            f"  quote sayısı={PriceQuote.objects.filter(alici_firma=alici).count()} · "
            f"now={timezone.now().isoformat()}"
        )
