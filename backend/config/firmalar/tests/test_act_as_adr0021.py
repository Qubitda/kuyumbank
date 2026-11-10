"""ADR-0021 — act-as + supplier portal erişim."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from firmalar import roles
from firmalar.models import Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import act_as_servisi
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()


class ActAsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.admin = User(
            username="actas_admin",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.admin.set_password("x")
        cls.admin.save()
        sync_user_role_groups(cls.admin)

        cls.alici_firma = Firma.objects.create(
            ad="ActAs Alıcı",
            firma_kodu="ACTAS_ALICI",
            alici_mi=True,
            onay_durumu="onayli",
        )
        cls.buyer = User(
            username="actas_buyer",
            firma=cls.alici_firma,
            rol=roles.ALICI_SATINALMACI,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

        cls.ted_firma = Firma.objects.create(
            ad="ActAs Ted",
            firma_kodu="ACTAS_TED",
            tedarikci_mi=True,
            onay_durumu="onayli",
        )
        cls.supplier = User(
            username="actas_sup",
            firma=cls.ted_firma,
            rol=roles.TEDARIKCI_SATIS,
        )
        cls.supplier.set_password("x")
        cls.supplier.save()
        sync_user_role_groups(cls.supplier)

    def test_baslat_durdur_session(self):
        session = self.client.session
        session.save()
        act_as_servisi.baslat(
            actor=self.admin, target=self.buyer, session=session
        )
        self.assertTrue(act_as_servisi.act_as_aktif_mi(session))
        act_as_servisi.durdur(session=session)
        self.assertFalse(act_as_servisi.act_as_aktif_mi(session))

    def test_kendine_yasak(self):
        session = self.client.session
        with self.assertRaises(ValidationError):
            act_as_servisi.baslat(
                actor=self.admin, target=self.admin, session=session
            )

    def test_yetkisiz(self):
        session = self.client.session
        with self.assertRaises(PermissionDenied):
            act_as_servisi.baslat(
                actor=self.buyer, target=self.supplier, session=session
            )

    def test_middleware_swap_buyer_home(self):
        c = Client()
        self.assertTrue(c.login(username="actas_admin", password="x"))
        r = c.post(reverse("act-as-start", args=[self.buyer.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.url.startswith("/buyer/"))
        home = c.get("/buyer/")
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, "Act-as aktif")
        self.assertContains(home, "actas_buyer")

    def test_supplier_portal_login(self):
        c = Client()
        self.assertTrue(c.login(username="actas_sup", password="x"))
        r = c.get("/supplier/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Tedarikçi paneli")

    def test_ops_supplier_blocked_without_act_as(self):
        c = Client()
        self.assertTrue(c.login(username="actas_admin", password="x"))
        r = c.get("/supplier/")
        self.assertEqual(r.status_code, 403)
