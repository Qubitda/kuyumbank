from django.core.exceptions import ValidationError
from django.test import TestCase

from bildirim.services import seed_servisi, template_servisi
from bildirim.services.template_servisi import render


class TemplateRenderTests(TestCase):
    def test_mustache_allowlist(self):
        subj, body = render(
            subject="Sipariş #{{order_id}}",
            body="<p>{{firma_adi}}</p>",
            context={"order_id": "42", "firma_adi": "Acme"},
        )
        self.assertEqual(subj, "Sipariş #42")
        self.assertIn("Acme", body)

    def test_forbidden_supplier_key(self):
        with self.assertRaises(ValidationError):
            render(
                subject="x",
                body="{{order_id}}",
                context={"order_id": "1", "tedarikci_adi": "gizli"},
            )

    def test_unknown_template_var_in_body(self):
        with self.assertRaises(ValidationError):
            render(subject="x", body="{{secret_cost}}", context={})

    def test_seed_templates(self):
        from bildirim.models import EmailTemplate, NotificationRule

        seed_servisi.seed_templates_and_rules()
        self.assertTrue(
            EmailTemplate.objects.filter(kod="order_created", sistem_mi=True).exists()
        )
        self.assertTrue(
            NotificationRule.objects.filter(event_type="order.created").exists()
        )
        self.assertGreaterEqual(EmailTemplate.objects.filter(sistem_mi=True).count(), 10)
        # idempotent
        stats2 = seed_servisi.seed_templates_and_rules()
        self.assertEqual(stats2["templates_created"], 0)
