"""GAP-F3-04 — supplier offer CSV import preview/commit."""

from __future__ import annotations

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from fiyatlama.models import TedarikciTeklif
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class SupplierOfferImportF304Tests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.ted_user)
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.api = APIClient()

    def _idem(self, key):
        return {"HTTP_IDEMPOTENCY_KEY": key}

    def test_preview_and_commit_csv_json(self):
        self.api.force_authenticate(user=self.ted_user)
        csv_text = (
            "varyant_id,fiyat_modeli,gram,tedarikci_kodu\n"
            f"{self.varyant.pk},METAL_BAZLI,1.250,FOY1\n"
            f"{self.varyant.pk},METAL,2.000,FOY2\n"
        )
        prev = self.api.post(
            reverse("api-supplier-offer-import-preview"),
            {"csv": csv_text},
            format="json",
            **self._idem("foy-prev-1"),
        )
        self.assertEqual(prev.status_code, 200, prev.content)
        body = prev.json()
        self.assertEqual(len(body["satirlar"]), 2)
        self.assertEqual(body["hatalar"], [])
        self.assertEqual(body["satirlar"][0]["fiyat_modeli"], "METAL_BAZLI")

        commit = self.api.post(
            reverse("api-supplier-offer-import-commit"),
            {"satirlar": body["satirlar"]},
            format="json",
            **self._idem("foy-commit-1"),
        )
        self.assertEqual(commit.status_code, 201, commit.content)
        created = commit.json()["created"]
        self.assertEqual(len(created), 2)
        ids = [c["teklif_id"] for c in created]
        qs = TedarikciTeklif.objects.filter(pk__in=ids)
        self.assertEqual(qs.count(), 2)
        self.assertTrue(all(t.durum == TedarikciTeklif.Durum.TASLAK for t in qs))
        self.assertTrue(all(t.tedarikci_id == self.ted.pk for t in qs))

    def test_preview_row_error_and_pdf_rejected(self):
        self.api.force_authenticate(user=self.ted_user)
        csv_text = (
            "varyant_id,fiyat_modeli,gram\n"
            f"{self.varyant.pk},METAL_BAZLI,\n"  # gram eksik
        )
        prev = self.api.post(
            reverse("api-supplier-offer-import-preview"),
            {"csv": csv_text},
            format="json",
            **self._idem("foy-prev-err"),
        )
        self.assertEqual(prev.status_code, 200, prev.content)
        self.assertEqual(prev.json()["satirlar"], [])
        self.assertTrue(prev.json()["hatalar"])

        pdf = self.api.post(
            reverse("api-supplier-offer-import-preview"),
            {"csv": "x", "filename": "foy.pdf"},
            format="json",
            **self._idem("foy-pdf"),
        )
        self.assertEqual(pdf.status_code, 400, pdf.content)

    def test_buyer_forbidden(self):
        self.api.force_authenticate(user=self.buyer)
        res = self.api.post(
            reverse("api-supplier-offer-import-preview"),
            {"csv": "varyant_id,fiyat_modeli,gram\n1,METAL_BAZLI,1\n"},
            format="json",
            **self._idem("foy-buyer"),
        )
        self.assertIn(res.status_code, (403, 401), res.content)

    def test_commit_rejects_invalid_without_write(self):
        self.api.force_authenticate(user=self.ted_user)
        before = TedarikciTeklif.objects.filter(tedarikci=self.ted).count()
        res = self.api.post(
            reverse("api-supplier-offer-import-commit"),
            {
                "satirlar": [
                    {
                        "varyant_id": self.varyant.pk,
                        "fiyat_modeli": "METAL_BAZLI",
                        # gram yok
                    }
                ]
            },
            format="json",
            **self._idem("foy-commit-bad"),
        )
        self.assertEqual(res.status_code, 400, res.content)
        self.assertEqual(
            TedarikciTeklif.objects.filter(tedarikci=self.ted).count(), before
        )
