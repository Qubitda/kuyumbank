"""F6-023 — buyer shipment API maskeli; tedarikçi 403; çapraz 404."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from firmalar import roles
from firmalar.role_permissions import seed_role_permissions
from firmalar.services.rol_servisi import sync_user_role_groups
from kalite.services import inspection_servisi, olcum_servisi
from lojistik.services import pod_servisi, shipment_servisi
from siparis.services import checkout_servisi, order_servisi
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class ShipmentApiF6023Tests(CheckoutFixtureMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.qc = User(
            username="api_ship_qc",
            firma=cls.platform,
            rol=roles.PLATFORM_QUALITY,
            is_staff=True,
        )
        cls.qc.set_password("x")
        cls.qc.save()
        sync_user_role_groups(cls.qc)
        cls.log = User(
            username="api_ship_log",
            firma=cls.platform,
            rol=roles.PLATFORM_LOGISTICS,
            is_staff=True,
        )
        cls.log.set_password("x")
        cls.log.save()
        sync_user_role_groups(cls.log)

    def setUp(self):
        self.api = APIClient()

    def _ship(self, key):
        self._quote_and_cart(miktar=Decimal("2.500"))
        co = checkout_servisi.checkout(actor=self.buyer, idempotency_key=key)
        order = order_servisi.olustur_from_checkout(
            actor=self.buyer, checkout_attempt=co.attempt
        )
        insp = inspection_servisi.olustur(actor=self.qc, order=order)
        insp = inspection_servisi.olcume_al(actor=self.qc, inspection=insp)
        line = order.lines.get()
        olcum_servisi.kaydet_olcum(
            actor=self.qc,
            inspection=insp,
            order_line=line,
            olculen=line.miktar,
        )
        inspection_servisi.pass_et(actor=self.qc, inspection=insp)
        ship = shipment_servisi.olustur(actor=self.log, order=order)
        ship = shipment_servisi.hazirla(actor=self.log, shipment=ship)
        ship = shipment_servisi.sevk_et(
            actor=self.log, shipment=ship, takip_no="API-TRK"
        )
        pod_servisi.kaydet_pod(
            actor=self.log, shipment=ship, teslim_alan="Musteri"
        )
        return order, ship

    def test_buyer_list_and_detail_masked(self):
        order, ship = self._ship("api-ship-ok")
        self.api.force_authenticate(user=self.buyer)
        res = self.api.get("/api/v1/shipments/", {"order_id": order.pk})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        row = res.data["results"][0]
        self.assertEqual(row["id"], ship.pk)
        self.assertEqual(row["takip_no"], "API-TRK")
        self.assertEqual(row["pod"]["teslim_alan"], "Musteri")
        self.assertNotIn("tedarikci", row)
        self.assertNotIn("warehouse", row)
        detail = self.api.get(f"/api/v1/shipments/{ship.pk}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["order_id"], order.pk)

    def test_supplier_forbidden(self):
        _order, ship = self._ship("api-ship-ted")
        self.api.force_authenticate(user=self.ted_user)
        res = self.api.get(f"/api/v1/shipments/{ship.pk}/")
        self.assertEqual(res.status_code, 403)

    def test_cross_tenant_404(self):
        _order, ship = self._ship("api-ship-x")
        from firmalar.models import Firma

        foreign = Firma.objects.create(
            ad="Foreign Alici",
            firma_kodu="FRNALI",
            alici_mi=True,
        )
        other = User(
            username="other_buyer",
            firma=foreign,
            rol=roles.ALICI_SATINALMACI,
            is_staff=True,
        )
        other.set_password("x")
        other.save()
        sync_user_role_groups(other)
        self.api.force_authenticate(user=other)
        res = self.api.get(f"/api/v1/shipments/{ship.pk}/")
        self.assertEqual(res.status_code, 404)
