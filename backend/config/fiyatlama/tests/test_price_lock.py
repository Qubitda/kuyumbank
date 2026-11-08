"""Dilim 3.7 — PriceLock (ADR-0008 §2.4 / ADR-0010)."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from firmalar import roles
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import (
    FiyatSozlesmesi,
    FiyatSozlesmesiKalemi,
    PriceLock,
    PriceQuote,
    TedarikciTeklif,
)
from fiyatlama.selectors.tenant import scope_price_lock_queryset
from fiyatlama.services import pricing_service, sozlesme_servisi
from fiyatlama.tests.test_price_quote import PriceQuoteFixtureMixin
from tanimlar.models import MetalKuru

User = get_user_model()


class PriceLockServiceTests(PriceQuoteFixtureMixin, TestCase):
    ON_BEHALF_GEREKCE = "Musteri telefon talebi"

    @classmethod
    def _make_user(cls, username, *, firma, rol):
        user = User(username=username, firma=firma, rol=rol, is_staff=True)
        user.set_password("x")
        user.save()
        sync_user_role_groups(user)
        return user

    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()
        cls.buyer = cls._make_user(
            "pl_buyer", firma=cls.alici, rol=roles.ALICI_SATINALMACI
        )
        cls.buyer_yonetici = cls._make_user(
            "pl_buyer_mgr", firma=cls.alici, rol=roles.ALICI_YONETICI
        )
        cls.buyer_onay = cls._make_user(
            "pl_buyer_apr", firma=cls.alici, rol=roles.ALICI_ONAYLAYICI
        )

        cls.alici2 = Firma.objects.create(
            ad="PLAL2", firma_kodu="PLAL2", alici_mi=True
        )
        cls.buyer_other = cls._make_user(
            "pl_buyer2", firma=cls.alici2, rol=roles.ALICI_SATINALMACI
        )
        cls.ted_user = cls._make_user(
            "pl_ted", firma=cls.ted, rol=roles.TEDARIKCI_SAHIP
        )
        cls.platform_admin = cls._make_user(
            "pl_padmin", firma=cls.platform, rol=roles.PLATFORM_ADMIN
        )
        cls.platform_super = cls._make_user(
            "pl_psuper", firma=cls.platform, rol=roles.PLATFORM_SUPER
        )
        # view_all_tenants var; lock_quote_on_behalf yok (L-07)
        cls.platform_ops = cls._make_user(
            "pl_pops", firma=cls.platform, rol=roles.PLATFORM_OPS
        )

    def _quote(self, **kwargs):
        return pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
            **kwargs,
        )

    def _lock(self, pq, *, kullanici=None, **kwargs):
        return pricing_service.lock_quote(
            pq, kullanici=kullanici or self.buyer, **kwargs
        )

    def test_valid_lock_creation(self):
        pq = self._quote()
        lock = pricing_service.lock_quote(pq, kullanici=self.buyer)
        self.assertEqual(lock.quote_id, pq.pk)
        self.assertEqual(lock.alici_firma_id, self.alici.pk)
        self.assertEqual(lock.durum, PriceLock.Durum.AKTIF)
        self.assertEqual(lock.toplam_vergisiz, pq.toplam_vergisiz)
        self.assertEqual(lock.para_birimi, pq.para_birimi)
        self.assertEqual(lock.gecerlilik_sonu, pq.gecerlilik_sonu)
        self.assertTrue(lock.is_gecerli())
        self.assertTrue(
            AuditOlay.objects.filter(
                action="price_lock.create",
                entity_id=str(lock.pk),
                success=True,
            ).exists()
        )

    def test_quote_relationship_and_snapshot_consistency(self):
        pq = self._quote()
        lock = self._lock(pq)
        self.assertEqual(lock.quote.toplam_vergisiz, lock.toplam_vergisiz)
        self.assertEqual(lock.quote.para_birimi, lock.para_birimi)
        self.assertEqual(pq.price_lock.pk, lock.pk)

    def test_quote_immutability_preserved(self):
        pq = self._quote()
        self._lock(pq)
        pq.toplam_vergisiz = Decimal("1.00")
        with self.assertRaises(ValidationError):
            pq.save()

    def test_lock_does_not_recalculate(self):
        pq = self._quote()
        before = pq.toplam_vergisiz
        # Kur değiştir — quote/kilit etkilenmemeli
        MetalKuru.objects.filter(pk=self.metal_satis.pk).update(
            saf_birim_fiyat=Decimal("9999.0000")
        )
        lock = self._lock(pq)
        self.assertEqual(lock.toplam_vergisiz, before)
        self.assertEqual(lock.quote.toplam_vergisiz, before)

    def test_expiration_with_injected_now(self):
        pq = self._quote()
        lock = self._lock(pq)
        after = lock.gecerlilik_sonu + timedelta(seconds=1)
        self.assertFalse(pricing_service.is_lock_gecerli(lock, now=after))
        lock.refresh_from_db()
        self.assertEqual(lock.durum, PriceLock.Durum.SURESI_DOLDU)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="price_lock.expire",
                entity_id=str(lock.pk),
                success=True,
            ).exists()
        )

    def test_expired_quote_cannot_lock(self):
        pq = self._quote()
        after = pq.gecerlilik_sonu + timedelta(seconds=1)
        with self.assertRaises(ValidationError):
            self._lock(pq, now=after)

    def test_boundary_now_equals_gecerlilik_sonu_rejects(self):
        """L-04: now == gecerlilik_sonu → kilit üretilmez (now >= son)."""
        pq = self._quote()
        with self.assertRaises(ValidationError):
            self._lock(pq, now=pq.gecerlilik_sonu)

    def test_clean_rejects_mismatched_ttl(self):
        """L-04: model clean() quote TTL sapmasını reddeder."""
        pq = self._quote()
        lock = PriceLock(
            quote=pq,
            alici_firma=self.alici,
            toplam_vergisiz=pq.toplam_vergisiz,
            para_birimi=pq.para_birimi,
            kilit_zamani=timezone.now(),
            gecerlilik_sonu=pq.gecerlilik_sonu + timedelta(minutes=5),
            durum=PriceLock.Durum.AKTIF,
        )
        with self.assertRaises(ValidationError) as ctx:
            lock.full_clean()
        self.assertIn("gecerlilik_sonu", ctx.exception.message_dict)

    def test_expired_lock_rejects_repeat(self):
        pq = self._quote()
        lock = self._lock(pq)
        after = lock.gecerlilik_sonu + timedelta(seconds=1)
        pricing_service.sync_lock_expiration(lock, now=after)
        with self.assertRaises(ValidationError):
            self._lock(pq, now=after)

    def test_idempotent_duplicate_request(self):
        pq = self._quote()
        a = self._lock(pq, idempotency_key="idem-1")
        b = self._lock(pq, idempotency_key="idem-1")
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(PriceLock.objects.filter(quote=pq).count(), 1)

    def test_idempotent_same_quote_without_key(self):
        pq = self._quote()
        a = self._lock(pq)
        b = pricing_service.lock_quote(
            pq,
            kullanici=self.platform_admin,
            gerekce=self.ON_BEHALF_GEREKCE,
        )
        self.assertEqual(a.pk, b.pk)

    def test_tenant_isolation_selector(self):
        pq = self._quote()
        lock = self._lock(pq)
        qs_buyer = scope_price_lock_queryset(PriceLock.objects.all(), self.buyer)
        qs_other = scope_price_lock_queryset(
            PriceLock.objects.all(), self.buyer_other
        )
        qs_ted = scope_price_lock_queryset(PriceLock.objects.all(), self.ted_user)
        self.assertEqual(list(qs_buyer), [lock])
        self.assertEqual(list(qs_other), [])
        self.assertEqual(list(qs_ted), [])

    def test_unauthorized_supplier(self):
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(pq, kullanici=self.ted_user)

    def test_unauthorized_other_buyer(self):
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(pq, kullanici=self.buyer_other)

    def test_app_level_lock_update_blocked(self):
        pq = self._quote()
        lock = self._lock(pq)
        lock.toplam_vergisiz = Decimal("1.00")
        with self.assertRaises(ValidationError):
            lock.save()

    def test_app_level_lock_delete_blocked(self):
        pq = self._quote()
        lock = self._lock(pq)
        with self.assertRaises(ValidationError):
            lock.delete()

    def test_status_cannot_contradict_via_manual_save(self):
        pq = self._quote()
        lock = self._lock(pq)
        lock.durum = PriceLock.Durum.SURESI_DOLDU
        with self.assertRaises(ValidationError):
            lock.save()

    # --- L-07 / L-10 ---

    def test_l07_satinalmaci_can_lock_own_quote(self):
        pq = self._quote()
        lock = self._lock(pq)
        self.assertEqual(lock.olusturan_id, self.buyer.pk)
        audit = AuditOlay.objects.get(
            action="price_lock.create", entity_id=str(lock.pk), success=True
        )
        self.assertEqual(audit.actor_id, self.buyer.pk)
        self.assertFalse(audit.detail.get("on_behalf"))

    def test_l07_alici_yonetici_default_cannot_lock(self):
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(pq, kullanici=self.buyer_yonetici)
        self.assertTrue(
            AuditOlay.objects.filter(
                action="price_lock.create",
                entity_id=str(pq.pk),
                success=False,
                actor=self.buyer_yonetici,
            ).exists()
        )

    def test_l07_alici_onaylayici_cannot_lock(self):
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(pq, kullanici=self.buyer_onay)

    def test_l07_view_all_only_platform_cannot_lock(self):
        """Ops: view_all_tenants var, lock_quote_on_behalf yok."""
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(
                pq, kullanici=self.platform_ops, gerekce=self.ON_BEHALF_GEREKCE
            )
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(
                pq, kullanici=self.finance, gerekce=self.ON_BEHALF_GEREKCE
            )

    def test_l07_admin_on_behalf_with_gerekce(self):
        pq = self._quote()
        lock = pricing_service.lock_quote(
            pq, kullanici=self.platform_admin, gerekce=self.ON_BEHALF_GEREKCE
        )
        self.assertEqual(lock.alici_firma_id, self.alici.pk)
        self.assertEqual(lock.olusturan_id, self.platform_admin.pk)
        audit = AuditOlay.objects.get(
            action="price_lock.create", entity_id=str(lock.pk), success=True
        )
        self.assertEqual(audit.actor_id, self.platform_admin.pk)
        self.assertTrue(audit.detail.get("on_behalf"))
        self.assertEqual(audit.detail.get("gerekce"), self.ON_BEHALF_GEREKCE)
        self.assertEqual(audit.detail.get("alici_firma_id"), self.alici.pk)

    def test_l07_super_on_behalf_with_gerekce(self):
        pq = self._quote()
        lock = pricing_service.lock_quote(
            pq, kullanici=self.platform_super, gerekce="  Destek kaydi 42  "
        )
        audit = AuditOlay.objects.get(
            action="price_lock.create", entity_id=str(lock.pk), success=True
        )
        self.assertEqual(audit.detail.get("gerekce"), "Destek kaydi 42")
        self.assertEqual(lock.olusturan_id, self.platform_super.pk)

    def test_l07_on_behalf_empty_gerekce_rejected(self):
        pq = self._quote()
        with self.assertRaises(ValidationError):
            pricing_service.lock_quote(
                pq, kullanici=self.platform_admin, gerekce=""
            )
        self.assertTrue(
            AuditOlay.objects.filter(
                action="price_lock.create",
                entity_id=str(pq.pk),
                success=False,
                actor=self.platform_admin,
            ).exists()
        )

    def test_l07_on_behalf_short_gerekce_after_trim_rejected(self):
        pq = self._quote()
        with self.assertRaises(ValidationError):
            pricing_service.lock_quote(
                pq, kullanici=self.platform_admin, gerekce="  kisa  "
            )

    def test_l07_supplier_cannot_lock_on_behalf(self):
        pq = self._quote()
        with self.assertRaises(PermissionDenied):
            pricing_service.lock_quote(
                pq, kullanici=self.ted_user, gerekce=self.ON_BEHALF_GEREKCE
            )


class PriceLockConstraintTests(PriceQuoteFixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_quote_world()
        self.buyer = User(
            username="pl_c_buyer",
            firma=self.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        self.buyer.set_password("x")
        self.buyer.save()
        sync_user_role_groups(self.buyer)

    def test_db_delete_trigger_rejects(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        lock = pricing_service.lock_quote(pq, kullanici=self.buyer)
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as c:
                    c.execute(
                        "DELETE FROM fiyatlama_pricelock WHERE id = %s",
                        [lock.pk],
                    )
        self.assertTrue(PriceLock.objects.filter(pk=lock.pk).exists())

    def test_db_update_snapshot_trigger_rejects(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        lock = pricing_service.lock_quote(pq, kullanici=self.buyer)
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as c:
                    c.execute(
                        "UPDATE fiyatlama_pricelock SET toplam_vergisiz = %s WHERE id = %s",
                        [Decimal("1.00"), lock.pk],
                    )

    def test_db_expire_transition_allowed(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        lock = pricing_service.lock_quote(pq, kullanici=self.buyer)
        after = lock.gecerlilik_sonu + timedelta(seconds=1)
        pricing_service.sync_lock_expiration(lock, now=after)
        lock.refresh_from_db()
        self.assertEqual(lock.durum, PriceLock.Durum.SURESI_DOLDU)

    def test_quote_unique_constraint(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        pricing_service.lock_quote(pq, kullanici=self.buyer)
        with self.assertRaises(Exception):
            PriceLock(
                quote=pq,
                alici_firma=self.alici,
                toplam_vergisiz=pq.toplam_vergisiz,
                para_birimi=pq.para_birimi,
                kilit_zamani=timezone.now(),
                gecerlilik_sonu=pq.gecerlilik_sonu,
                durum=PriceLock.Durum.AKTIF,
            ).save()

    def test_raw_insert_mismatched_ttl_rejected_by_trigger(self):
        """L-04: servis dışı INSERT — gecerlilik_sonu ≠ quote → DB trigger red."""
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        bad_son = pq.gecerlilik_sonu + timedelta(hours=1)
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as c:
                    c.execute(
                        """
                        INSERT INTO fiyatlama_pricelock (
                            toplam_vergisiz, para_birimi, kilit_zamani,
                            gecerlilik_sonu, durum, idempotency_key,
                            olusturma_tarihi, alici_firma_id, olusturan_id,
                            quote_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s
                        )
                        """,
                        [
                            pq.toplam_vergisiz,
                            pq.para_birimi,
                            timezone.now(),
                            bad_son,
                            PriceLock.Durum.AKTIF,
                            timezone.now(),
                            self.alici.pk,
                            self.finance.pk,
                            pq.pk,
                        ],
                    )
        self.assertFalse(PriceLock.objects.filter(quote_id=pq.pk).exists())

    def test_raw_insert_matching_ttl_allowed(self):
        """L-04: servis dışı INSERT — quote ile eşit TTL kabul (guard yalnız eşitlik)."""
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        now = timezone.now()
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO fiyatlama_pricelock (
                    toplam_vergisiz, para_birimi, kilit_zamani,
                    gecerlilik_sonu, durum, idempotency_key,
                    olusturma_tarihi, alici_firma_id, olusturan_id,
                    quote_id
                ) VALUES (
                    %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s
                )
                """,
                [
                    pq.toplam_vergisiz,
                    pq.para_birimi,
                    now,
                    pq.gecerlilik_sonu,
                    PriceLock.Durum.AKTIF,
                    now,
                    self.alici.pk,
                    self.finance.pk,
                    pq.pk,
                ],
            )
        self.assertTrue(PriceLock.objects.filter(quote_id=pq.pk).exists())


class PriceLockConcurrencyTests(PriceQuoteFixtureMixin, TransactionTestCase):
    def setUp(self):
        self._build_quote_world()
        self.buyer = User(
            username="pl_conc_buyer",
            firma=self.alici,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        self.buyer.set_password("x")
        self.buyer.save()
        sync_user_role_groups(self.buyer)
        self.pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )

    def test_concurrent_lock_creates_single_row(self):
        quote_id = self.pq.pk
        user_id = self.buyer.pk

        def worker():
            # Her thread kendi bağlantısını kullanır
            pq = PriceQuote.objects.get(pk=quote_id)
            user = User.objects.get(pk=user_id)
            lock = pricing_service.lock_quote(pq, kullanici=user)
            return lock.pk

        ids = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(worker) for _ in range(8)]
            for f in as_completed(futures):
                ids.append(f.result())

        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(PriceLock.objects.filter(quote_id=quote_id).count(), 1)


class PriceLockRegressionSmokeTests(PriceQuoteFixtureMixin, TestCase):
    """3.4–3.6 duman: quote hâlâ üretir; kör havuz selector bozulmaz."""

    @classmethod
    def setUpTestData(cls):
        cls._build_quote_world()

    def test_quote_still_works(self):
        pq = pricing_service.quote(
            alici_firma=self.alici,
            satis_kanali=self.kanal,
            varyant=self.varyant,
            kullanici=self.finance,
        )
        self.assertEqual(pq.toplam_vergisiz, Decimal("5990.00"))
        self.assertEqual(pq.belge_turu, PriceQuote.BelgeTuru.PROFORMA)
