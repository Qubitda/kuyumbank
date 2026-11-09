"""F10-023 RFQ buyer UI + F10-021 katalog dışı create (kör)."""

from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.models import RFQ
from siparis.services import rfq_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin


class RfqUiF10023Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        sync_user_role_groups(cls.buyer)

    def setUp(self):
        self.client = Client()

    def test_login_required(self):
        res = self.client.get(reverse("buyer-rfq-list"))
        self.assertEqual(res.status_code, 302)

    def test_supplier_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-rfq-list"))
        self.assertEqual(res.status_code, 403)

    def test_katalog_disi_create_send_message_masked(self):
        self.client.force_login(self.buyer)
        res = self.client.post(
            reverse("buyer-rfq-create"),
            {
                "baslik": "Özel bilezik",
                "aciklama": "18 ayar özel üretim benzeri",
                "miktar": "5",
                "birim": "ADET",
            },
        )
        self.assertEqual(res.status_code, 302)
        rfq = RFQ.objects.get(alici_firma=self.buyer.firma)
        self.assertIn(
            reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}),
            res.url,
        )
        line = rfq.lines.get()
        self.assertIsNone(line.varyant_id)
        self.assertEqual(line.aciklama, "18 ayar özel üretim benzeri")

        det = self.client.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertEqual(det.status_code, 200)
        self.assertContains(det, "katalog dışı")
        self.assertNotContains(det, "tedarikci")

        send = self.client.post(reverse("buyer-rfq-send", kwargs={"pk": rfq.pk}))
        self.assertEqual(send.status_code, 302)
        rfq.refresh_from_db()
        self.assertEqual(rfq.durum, RFQ.Durum.GONDERILDI)

        msg = self.client.post(
            reverse("buyer-rfq-message", kwargs={"pk": rfq.pk}),
            {"govde": "Platform üzerinden ek bilgi"},
        )
        self.assertEqual(msg.status_code, 302)
        det2 = self.client.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertContains(det2, "Platform üzerinden ek bilgi")
        self.assertNotContains(det2, self.ted_user.username)
        self.assertNotContains(det2, "tedarikci")

        lst = self.client.get(reverse("buyer-rfq-list"))
        self.assertEqual(lst.status_code, 200)
        self.assertContains(lst, f"#{rfq.pk}")

    def test_cross_tenant_rfq_404(self):
        rfq = rfq_servisi.olustur(
            actor=self.buyer,
            baslik="Gizli",
            line_specs=[
                {"aciklama": "x", "miktar": Decimal("1"), "birim": "ADET"}
            ],
        )
        # başka alıcı yoksa supplier login ile 403; IDOR için aynı path
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-rfq-detail", kwargs={"pk": rfq.pk}))
        self.assertEqual(res.status_code, 403)
