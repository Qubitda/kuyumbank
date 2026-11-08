"""firmalar.0003: rolü dolu firmasız kullanıcı platforma bağlanmaz."""

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class Firma0003BackfillTests(TransactionTestCase):
    def tearDown(self):
        call_command("migrate", verbosity=0)

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def test_rolu_dolu_firmasiz_kullanici_migration_durur(self):
        self._migrate([("firmalar", "0002_faz1_kimlik_rbac")])
        executor = MigrationExecutor(connection)
        state = executor.loader.project_state([("firmalar", "0002_faz1_kimlik_rbac")])
        Kullanici = state.apps.get_model("firmalar", "Kullanici")
        u = Kullanici(username="orphan_rol", rol="tedarikci_sahip", is_active=True)
        u.password = "!"
        u.save()

        try:
            with self.assertRaises(RuntimeError) as ctx:
                self._migrate([("firmalar", "0003_faz1_backfill_platform")])
            msg = str(ctx.exception)
            self.assertIn("audit_user_assignments", msg)
            self.assertIn("orphan_rol", msg)
        finally:
            # tearDown migrate 0003'ü yeniden uygular; engeli kaldır
            Kullanici.objects.filter(username="orphan_rol").delete()

    def test_bos_rol_superuser_platforma_baglanir(self):
        self._migrate([("firmalar", "0002_faz1_kimlik_rbac")])
        executor = MigrationExecutor(connection)
        state = executor.loader.project_state([("firmalar", "0002_faz1_kimlik_rbac")])
        Kullanici = state.apps.get_model("firmalar", "Kullanici")
        u = Kullanici(
            username="su_orphan",
            rol="",
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        u.password = "!"
        u.save()

        self._migrate([("firmalar", "0003_faz1_backfill_platform")])
        state3 = MigrationExecutor(connection).loader.project_state(
            [("firmalar", "0003_faz1_backfill_platform")]
        )
        Kullanici3 = state3.apps.get_model("firmalar", "Kullanici")
        u3 = Kullanici3.objects.get(username="su_orphan")
        self.assertIsNotNone(u3.firma_id)
        self.assertEqual(u3.rol, "platform_super")
