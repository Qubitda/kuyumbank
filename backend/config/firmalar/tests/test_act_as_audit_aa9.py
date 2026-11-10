"""ADR-0021 AA-9 — act-as sırasında audit gerçek aktör + on_behalf_of."""

from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from firmalar import roles
from firmalar.middleware import ActAsMiddleware
from firmalar.models import AuditOlay, Firma
from firmalar.role_permissions import seed_role_permissions
from firmalar.services import act_as_servisi
from firmalar.services.audit_servisi import act_as_audit_context, record_audit
from firmalar.services.platform_kurulum import ensure_platform_firma
from firmalar.services.rol_servisi import sync_user_role_groups

User = get_user_model()


class ActAsAuditAA9Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_role_permissions()
        platform = ensure_platform_firma()
        cls.admin = User(
            username="aa9_admin",
            firma=platform,
            rol=roles.PLATFORM_ADMIN,
            is_staff=True,
        )
        cls.admin.set_password("x")
        cls.admin.save()
        sync_user_role_groups(cls.admin)

        cls.alici_firma = Firma.objects.create(
            ad="AA9 Alıcı",
            firma_kodu="AA9_ALICI",
            alici_mi=True,
            onay_durumu="onayli",
        )
        cls.buyer = User(
            username="aa9_buyer",
            firma=cls.alici_firma,
            rol=roles.ALICI_SATINALMACI,
        )
        cls.buyer.set_password("x")
        cls.buyer.save()
        sync_user_role_groups(cls.buyer)

    def test_context_remaps_actor_to_real_operator(self):
        with act_as_audit_context(actor=self.admin, target=self.buyer):
            row = record_audit(
                actor=self.buyer,
                action="aa9.demo_write",
                entity_type="Test",
                entity_id="1",
            )
        row.refresh_from_db()
        self.assertEqual(row.actor_id, self.admin.pk)
        self.assertEqual(row.on_behalf_of_id, self.buyer.pk)
        self.assertEqual(row.actor_firma_id, self.admin.firma_id)

    def test_without_context_unchanged(self):
        row = record_audit(
            actor=self.buyer,
            action="aa9.normal",
            entity_type="Test",
            entity_id="2",
        )
        self.assertEqual(row.actor_id, self.buyer.pk)
        self.assertIsNone(row.on_behalf_of_id)

    def test_middleware_remaps_audit_during_request(self):
        factory = RequestFactory()
        seed = factory.get("/seed")
        SessionMiddleware(lambda r: HttpResponse("ok")).process_request(seed)
        seed.session.save()
        act_as_servisi.baslat(
            actor=self.admin, target=self.buyer, session=seed.session
        )
        session = seed.session

        captured = {}

        def get_response(req):
            captured["user_id"] = req.user.pk
            captured["row"] = record_audit(
                actor=req.user,
                action="aa9.mw_write",
                entity_type="Test",
                entity_id="mw",
            )
            return HttpResponse("ok")

        mw = ActAsMiddleware(get_response)
        req = factory.get("/buyer/")
        req.user = self.admin
        req.session = session
        resp = mw(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(captured["user_id"], self.buyer.pk)
        row = captured["row"]
        self.assertEqual(row.actor_id, self.admin.pk)
        self.assertEqual(row.on_behalf_of_id, self.buyer.pk)

    def test_act_as_start_audit_is_real_actor(self):
        c = Client()
        self.assertTrue(c.login(username="aa9_admin", password="x"))
        r = c.post(reverse("act-as-start", args=[self.buyer.pk]))
        self.assertEqual(r.status_code, 302)
        start = AuditOlay.objects.filter(action="user.act_as_start").latest(
            "created_at"
        )
        self.assertEqual(start.actor_id, self.admin.pk)
        self.assertIsNone(start.on_behalf_of_id)
