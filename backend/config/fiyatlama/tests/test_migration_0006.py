"""fiyatlama.0006 Faz 3.2 — ileri/reverse (K-007/K-008)."""

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Fiyatlama0006MigrationTests(TransactionTestCase):
    def tearDown(self):
        call_command("migrate", verbosity=0)

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def test_forward_and_reverse(self):
        self._migrate([("fiyatlama", "0005_faz3_1_teklif_yasam_dongusu")])
        self._migrate([("fiyatlama", "0006_faz3_2_k007_k008")])
        self._migrate([("fiyatlama", "0005_faz3_1_teklif_yasam_dongusu")])
        self._migrate([("fiyatlama", "0006_faz3_2_k007_k008")])
