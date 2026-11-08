"""Faz 2.1 O4 — Toplu Reddet çoklu _selected_action ID listesi."""

from django.http import QueryDict
from django.test import SimpleTestCase

from urunler.admin.urun_admin import TopluRedForm


def _post(**kwargs):
    q = QueryDict(mutable=True)
    for key, val in kwargs.items():
        if isinstance(val, (list, tuple)):
            q.setlist(key, list(val))
        else:
            q[key] = val
    return q


class TopluRedO4Tests(SimpleTestCase):
    def test_multi_selected_action_ids(self):
        form = TopluRedForm(
            _post(
                _selected_action=["11", "22", "33"],
                red_nedeni="Gram hatalı",
                apply="1",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["_selected_action"], ["11", "22", "33"])

    def test_single_id_still_works(self):
        form = TopluRedForm(_post(_selected_action=["7"], red_nedeni="Eksik"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["_selected_action"], ["7"])

    def test_initial_list_renders_choices(self):
        form = TopluRedForm(initial={"_selected_action": ["1", "2"]})
        self.assertEqual(
            form.fields["_selected_action"].choices,
            [("1", "1"), ("2", "2")],
        )
