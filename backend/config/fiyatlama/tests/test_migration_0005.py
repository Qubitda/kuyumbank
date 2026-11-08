"""fiyatlama.0005 Faz 3.1 — ileri/reverse (CASCADE→PROTECT + alanlar)."""

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Fiyatlama0005MigrationTests(TransactionTestCase):
    def tearDown(self):
        call_command("migrate", verbosity=0)

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def test_forward_and_reverse(self):
        self._migrate([("fiyatlama", "0004_faz2_0_hedef_urun_approve_eslestirme")])
        self._migrate([("fiyatlama", "0005_faz3_1_teklif_yasam_dongusu")])
        # reverse to 0004
        self._migrate([("fiyatlama", "0004_faz2_0_hedef_urun_approve_eslestirme")])
        # forward again
        self._migrate([("fiyatlama", "0005_faz3_1_teklif_yasam_dongusu")])
