"""ADR-0021 — act-as çekirdek + ADR-0029 API (HTML portal yok)."""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

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

    def test_api_start_stop_and_me_as_target(self):
        api = APIClient(enforce_csrf_checks=False)
        self.assertTrue(api.login(username="actas_admin", password="x"))
        start = api.post(
            reverse("api-act-as-start"),
            {"user_id": self.buyer.pk},
            format="json",
        )
        self.assertEqual(start.status_code, 200, start.data)
        self.assertTrue(start.data["act_as"])
        self.assertEqual(start.data["target_id"], self.buyer.pk)
        self.assertEqual(start.data["redirect_url"], "/admin/")

        me = api.get(reverse("api-me"))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["username"], "actas_buyer")
        act = me.data.get("act_as") or {}
        self.assertTrue(act.get("active"))
        self.assertEqual(act.get("target_username"), "actas_buyer")
        self.assertEqual(act.get("actor_username"), "actas_admin")
        self.assertTrue(me.data["capabilities"].get("can_act_as"))

        stop = api.post(reverse("api-act-as-stop"), {}, format="json")
        self.assertEqual(stop.status_code, 200)
        self.assertFalse(stop.data["act_as"])

        me2 = api.get(reverse("api-me"))
        self.assertEqual(me2.status_code, 200)
        self.assertFalse((me2.data.get("act_as") or {}).get("active"))

    @override_settings(FRONTEND_PORTAL_BASE_URL="https://app.example.test")
    def test_portal_hedef_uses_frontend_base(self):
        self.assertEqual(
            act_as_servisi.portal_hedef_url(self.buyer),
            "https://app.example.test/",
        )

    def test_html_portals_gone(self):
        from django.test import Client

        c = Client()
        self.assertTrue(c.login(username="actas_sup", password="x"))
        self.assertEqual(c.get("/supplier/").status_code, 404)
        self.assertEqual(c.get("/buyer/").status_code, 404)
