"""F10-014 — Onay kuyruğu UI (tenant + RBAC)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from firmalar import roles
from firmalar.models import Firma, OnayTalebi
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import onay_servisi
from firmalar.services.rol_servisi import sync_user_role_groups
from siparis.tests.test_checkout_f4_040 import CheckoutFixtureMixin

User = get_user_model()


class ApprovalUiF10014Tests(CheckoutFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._build_checkout_world()
        seed_role_permissions()
        cls.approver = User(
            username="ui_appr",
            firma=cls.alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.approver.set_password("x")
        cls.approver.save()
        sync_user_role_groups(cls.approver)

        cls.other_alici = Firma.objects.create(
            ad="OTHAL",
            firma_kodu="OTHAL",
            alici_mi=True,
        )
        cls.other_approver = User(
            username="ui_appr_other",
            firma=cls.other_alici,
            rol=roles.ALICI_ONAYLAYICI,
            is_staff=True,
        )
        cls.other_approver.set_password("x")
        cls.other_approver.save()
        sync_user_role_groups(cls.other_approver)

    def setUp(self):
        self.client = Client()

    def test_login_required(self):
        res = self.client.get(reverse("buyer-approval-list"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/buyer/login/", res.url)

    def test_buyer_without_approval_perm_forbidden(self):
        self.client.force_login(self.buyer)
        res = self.client.get(reverse("buyer-approval-list"))
        self.assertEqual(res.status_code, 403)

    def test_supplier_forbidden(self):
        self.client.force_login(self.ted_user)
        res = self.client.get(reverse("buyer-approval-list"))
        self.assertEqual(res.status_code, 403)

    def test_approver_list_and_approve(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("75.00"),
            para_birimi="TRY",
            gerekce="UI smoke",
        )
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)

        self.client.force_login(self.approver)
        res = self.client.get(reverse("buyer-approval-list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f"OT#{ot.pk}")
        self.assertContains(res, "TRY")
        self.assertContains(res, "UI smoke")

        res = self.client.post(
            reverse("buyer-approval-action", kwargs={"pk": ot.pk}),
            {"action": "onayla"},
        )
        self.assertEqual(res.status_code, 302)
        ot.refresh_from_db()
        self.assertEqual(ot.durum, OnayTalebi.Durum.ONAYLANDI)

    def test_cross_tenant_action_404(self):
        ot = onay_servisi.olustur(
            actor=self.approver,
            firma=self.alici,
            tutar=Decimal("20.00"),
        )
        ot = onay_servisi.beklemede_al(actor=self.approver, onay=ot)

        self.client.force_login(self.other_approver)
        res = self.client.post(
            reverse("buyer-approval-action", kwargs={"pk": ot.pk}),
            {"action": "onayla"},
        )
        self.assertEqual(res.status_code, 404)
        ot.refresh_from_db()
        self.assertEqual(ot.durum, OnayTalebi.Durum.BEKLEMEDE)
