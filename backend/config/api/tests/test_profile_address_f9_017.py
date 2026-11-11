"""F9-017 — /me/profile + /me/addresses self-service + IDOR."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar import roles
from firmalar.models import Firma, FirmaAdresi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()


class ProfileAddressApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        cls.firma_a = Firma.objects.create(
            ad="Alici A", firma_kodu="F9017A", alici_mi=True, aktif=True
        )
        cls.firma_b = Firma.objects.create(
            ad="Alici B", firma_kodu="F9017B", alici_mi=True, aktif=True
        )
        cls.admin_a = User(
            username="f9017_admin_a",
            firma=cls.firma_a,
            rol=roles.ALICI_YONETICI,
            email="a@ex.com",
            first_name="Ali",
            last_name="A",
        )
        cls.admin_a.set_password("x")
        cls.admin_a.save()
        sync_user_role_groups(cls.admin_a)

        cls.buyer_a = User(
            username="f9017_buyer_a",
            firma=cls.firma_a,
            rol=roles.ALICI_SATINALMACI,
            email="buyer@ex.com",
        )
        cls.buyer_a.set_password("x")
        cls.buyer_a.save()
        sync_user_role_groups(cls.buyer_a)

        cls.admin_b = User(
            username="f9017_admin_b",
            firma=cls.firma_b,
            rol=roles.ALICI_YONETICI,
            email="b@ex.com",
        )
        cls.admin_b.set_password("x")
        cls.admin_b.save()
        sync_user_role_groups(cls.admin_b)

        cls.adres_b = FirmaAdresi.objects.create(
            firma=cls.firma_b,
            tip="merkez",
            il="Ankara",
            ilce="Cankaya",
            adres="B cad",
            varsayilan=True,
        )

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key: str):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_profile_get_patch_json(self):
        self.api.force_authenticate(user=self.admin_a)
        res = self.api.get(reverse("api-me-profile"))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res["Content-Type"].split(";")[0], "application/json")
        self.assertNotIn("<html", res.content.decode().lower())
        body = res.json()
        self.assertEqual(body["username"], "f9017_admin_a")
        self.assertEqual(body["first_name"], "Ali")

        patch = self.api.patch(
            reverse("api-me-profile"),
            {"first_name": "Ayse", "last_name": "Yilmaz", "email": "hack@x.com"},
            format="json",
        )
        self.assertEqual(patch.status_code, 200, patch.content)
        self.assertEqual(patch.json()["first_name"], "Ayse")
        self.assertEqual(patch.json()["last_name"], "Yilmaz")
        self.admin_a.refresh_from_db()
        self.assertEqual(self.admin_a.first_name, "Ayse")
        self.assertEqual(self.admin_a.email, "a@ex.com")  # email ignored

        empty = self.api.patch(reverse("api-me-profile"), {}, format="json")
        self.assertEqual(empty.status_code, 400, empty.content)

    def test_address_crud_and_idor(self):
        self.api.force_authenticate(user=self.admin_a)
        created = self.api.post(
            reverse("api-me-addresses"),
            {
                "tip": "sevk",
                "il": "Istanbul",
                "ilce": "Kadikoy",
                "adres": "A sk 1",
                "varsayilan": True,
                "firma_id": self.firma_b.pk,  # ignored
            },
            format="json",
            **self._idem("addr-c1"),
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created["Content-Type"].split(";")[0], "application/json")
        aid = created.json()["id"]
        self.assertEqual(created.json()["firma_id"], self.firma_a.pk)
        self.assertTrue(created.json()["varsayilan"])

        # buyer without manage_users → 403
        self.api.force_authenticate(user=self.buyer_a)
        denied = self.api.post(
            reverse("api-me-addresses"),
            {"il": "X", "adres": "Y"},
            format="json",
            **self._idem("addr-buyer"),
        )
        self.assertEqual(denied.status_code, 403, denied.content)

        # list OK for buyer (read)
        listed = self.api.get(reverse("api-me-addresses"))
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(listed.json()["count"], 1)

        # IDOR: firma B adresi → 404
        idor = self.api.get(reverse("api-me-address-detail", kwargs={"pk": self.adres_b.pk}))
        self.assertEqual(idor.status_code, 404, idor.content)

        self.api.force_authenticate(user=self.admin_a)
        idor_patch = self.api.patch(
            reverse("api-me-address-detail", kwargs={"pk": self.adres_b.pk}),
            {"il": "Hack"},
            format="json",
            **self._idem("addr-idor"),
        )
        self.assertEqual(idor_patch.status_code, 404, idor_patch.content)

        updated = self.api.patch(
            reverse("api-me-address-detail", kwargs={"pk": aid}),
            {"il": "Bursa", "varsayilan": True},
            format="json",
            **self._idem("addr-u1"),
        )
        self.assertEqual(updated.status_code, 200, updated.content)
        self.assertEqual(updated.json()["il"], "Bursa")

        deleted = self.api.delete(
            reverse("api-me-address-detail", kwargs={"pk": aid}),
            **self._idem("addr-d1"),
        )
        self.assertEqual(deleted.status_code, 200, deleted.content)
        self.assertFalse(FirmaAdresi.objects.filter(pk=aid).exists())

        bad = self.api.post(
            reverse("api-me-addresses"),
            {"tip": "yok", "il": "Istanbul", "adres": "x"},
            format="json",
            **self._idem("addr-bad"),
        )
        self.assertEqual(bad.status_code, 400, bad.content)

    def test_anon_401(self):
        res = self.api.get(reverse("api-me-profile"))
        self.assertIn(res.status_code, (401, 403), res.content)
