"""Merkezi rol → permission matrisi ve idempotent seed (ADR-0003-04, Faz 2.0).

Özel Meta.permissions + admin için gerekli Django view/change izinleri
rol gruplarına matris üzerinden eklenir; kullanıcıya doğrudan user_permissions yok.
"""

from django.contrib.auth.models import Group, Permission
from django.db import transaction

from . import roles

# app_label.codename — Meta.permissions ile uyumlu olmalı
P = {
    "approve_firma": "firmalar.approve_firma",
    "view_all_tenants": "firmalar.view_all_tenants",
    "manage_users": "firmalar.manage_users",
    "manage_all_users": "firmalar.manage_all_users",
    "act_as_user": "firmalar.act_as_user",
    "submit_urun": "urunler.submit_urun",
    "approve_urun": "urunler.approve_urun",
    "publish_urun": "urunler.publish_urun",
    "manage_own_teklif": "fiyatlama.manage_own_teklif",
    "approve_teklif": "fiyatlama.approve_teklif",
    "approve_eslestirme": "fiyatlama.approve_eslestirme",
    "manage_sozlesme": "fiyatlama.manage_sozlesme",
    "lock_quote": "fiyatlama.lock_quote",
    "lock_quote_on_behalf": "fiyatlama.lock_quote_on_behalf",
    "manage_warehouse": "stok.manage_warehouse",
    "manage_own_warehouse": "stok.manage_own_warehouse",
    "manage_kur": "tanimlar.manage_kur",
    "manage_piyasa": "piyasa.manage_piyasa",
    "post_ledger": "finans.post_ledger",
    "manage_qc": "kalite.manage_qc",
    "view_qc": "kalite.view_qc",
    "manage_qc_override": "kalite.manage_qc_override",
    "manage_shipment": "lojistik.manage_shipment",
    "manage_return": "lojistik.manage_return",
    "manage_document": "belgeler.manage_document",
    "manage_hak_edis": "finans.manage_hak_edis",
    "manage_org": "firmalar.manage_org",
    "manage_spend_limit": "firmalar.manage_spend_limit",
    "manage_approval": "firmalar.manage_approval",
    "manage_rfq": "siparis.manage_rfq",
    "manage_smtp": "bildirim.manage_smtp",
    "manage_email_template": "bildirim.manage_email_template",
    "manage_notification_rule": "bildirim.manage_notification_rule",
    "send_manual_email": "bildirim.send_manual_email",
    "view_email_log": "bildirim.view_email_log",
}

_BILDIRIM_ADMIN = (
    P["manage_smtp"],
    P["manage_email_template"],
    P["manage_notification_rule"],
    P["send_manual_email"],
    P["view_email_log"],
    "bildirim.view_smtpsettings",
    "bildirim.change_smtpsettings",
    "bildirim.view_emailtemplate",
    "bildirim.add_emailtemplate",
    "bildirim.change_emailtemplate",
    "bildirim.view_notificationrule",
    "bildirim.add_notificationrule",
    "bildirim.change_notificationrule",
    "bildirim.view_emaildelivery",
    "bildirim.change_emaildelivery",
    "bildirim.view_recipientsettings",
    "bildirim.change_recipientsettings",
)

_KUR_ADMIN = (
    "tanimlar.view_kursaglayici",
    "tanimlar.change_kursaglayici",
    "tanimlar.add_kursaglayici",
    "tanimlar.view_kurpolitikasi",
    "tanimlar.change_kurpolitikasi",
    "tanimlar.add_kurpolitikasi",
    "tanimlar.view_metalkuru",
    "tanimlar.add_metalkuru",
    "tanimlar.view_dovizkuru",
    "tanimlar.add_dovizkuru",
)
_PIYASA_ADMIN = (
    P["manage_piyasa"],
    "piyasa.view_piyasaurun",
    "piyasa.add_piyasaurun",
    "piyasa.change_piyasaurun",
    "piyasa.delete_piyasaurun",
    "piyasa.view_piyasafiyatkurali",
    "piyasa.add_piyasafiyatkurali",
    "piyasa.change_piyasafiyatkurali",
    "piyasa.delete_piyasafiyatkurali",
)

# Admin changelist/inline için Django model izinleri (grup üzerinden)
_URUN_ADMIN = (
    "urunler.view_urun",
    "urunler.change_urun",
    "urunler.add_urun",
    "urunler.view_varyant",
    "urunler.change_varyant",
    "urunler.add_varyant",
    "urunler.view_urunkanal",
    "urunler.change_urunkanal",
    "urunler.view_uruntasi",
    "urunler.change_uruntasi",
)
_FIYATLAMA_TEKLIF_ADMIN = (
    "fiyatlama.view_tedarikciteklif",
    "fiyatlama.change_tedarikciteklif",
    "fiyatlama.add_tedarikciteklif",
    "fiyatlama.view_tekliftasmaliyeti",
    "fiyatlama.change_tekliftasmaliyeti",
)
_FIYATLAMA_SOZLESME_ADMIN = (
    "fiyatlama.view_fiyatsozlesmesi",
    "fiyatlama.change_fiyatsozlesmesi",
    "fiyatlama.add_fiyatsozlesmesi",
    "fiyatlama.view_fiyatsozlesmesikalemi",
    "fiyatlama.change_fiyatsozlesmesikalemi",
)
_FIYATLAMA_LOG_ADMIN = (
    "fiyatlama.view_pricecalculationlog",
)
_FIRMA_ADMIN = (
    "firmalar.view_firma",
    "firmalar.change_firma",
    "firmalar.view_firmaadresi",
    "firmalar.change_firmaadresi",
    "firmalar.view_kullanici",
    "firmalar.change_kullanici",
)

ROLE_PERMISSION_MATRIX = {
    roles.PLATFORM_SUPER: (
        P["approve_firma"],
        P["view_all_tenants"],
        P["manage_users"],
        P["manage_all_users"],
        P["act_as_user"],
        P["submit_urun"],
        P["approve_urun"],
        P["publish_urun"],
        P["manage_own_teklif"],
        P["approve_teklif"],
        P["approve_eslestirme"],
        P["manage_sozlesme"],
        P["lock_quote_on_behalf"],
        P["manage_warehouse"],
        P["manage_kur"],
        P["post_ledger"],
        P["manage_return"],
        P["manage_hak_edis"],
        P["manage_org"],
        P["manage_spend_limit"],
        P["manage_approval"],
        P["manage_rfq"],
        *_FIRMA_ADMIN,
        *_URUN_ADMIN,
        *_FIYATLAMA_TEKLIF_ADMIN,
        *_FIYATLAMA_SOZLESME_ADMIN,
        *_FIYATLAMA_LOG_ADMIN,
        *_KUR_ADMIN,
        *_PIYASA_ADMIN,
        *_BILDIRIM_ADMIN,
    ),
    roles.PLATFORM_ADMIN: (
        P["approve_firma"],
        P["view_all_tenants"],
        P["manage_users"],
        P["manage_all_users"],
        P["act_as_user"],
        P["approve_urun"],
        P["publish_urun"],
        P["approve_teklif"],
        P["approve_eslestirme"],
        P["manage_sozlesme"],
        P["lock_quote_on_behalf"],
        P["manage_warehouse"],
        P["manage_kur"],
        P["post_ledger"],
        P["manage_return"],
        P["manage_hak_edis"],
        P["manage_org"],
        P["manage_spend_limit"],
        P["manage_approval"],
        P["manage_rfq"],
        *_FIRMA_ADMIN,
        *_URUN_ADMIN,
        *_FIYATLAMA_TEKLIF_ADMIN,
        *_FIYATLAMA_SOZLESME_ADMIN,
        *_FIYATLAMA_LOG_ADMIN,
        *_KUR_ADMIN,
        *_PIYASA_ADMIN,
        *_BILDIRIM_ADMIN,
    ),
    roles.PLATFORM_OPS: (
        P["view_all_tenants"],
        P["approve_teklif"],
        P["manage_warehouse"],
        P["manage_return"],
        P["manage_org"],
        P["manage_approval"],
        *_FIYATLAMA_TEKLIF_ADMIN,
    ),
    roles.PLATFORM_FINANCE: (
        P["view_all_tenants"],
        P["manage_sozlesme"],
        P["manage_kur"],
        P["post_ledger"],
        P["manage_hak_edis"],
        P["view_email_log"],
        P["send_manual_email"],
        "bildirim.view_emaildelivery",
        "bildirim.change_emaildelivery",
        "bildirim.view_emailtemplate",
        *_FIYATLAMA_SOZLESME_ADMIN,
        *_FIYATLAMA_LOG_ADMIN,
        *_KUR_ADMIN,
        *_PIYASA_ADMIN,
    ),
    roles.PLATFORM_CATALOG: (
        P["view_all_tenants"],
        P["approve_urun"],
        P["publish_urun"],
        P["approve_teklif"],
        P["approve_eslestirme"],
        P["manage_document"],
        "belgeler.view_document",
        "belgeler.view_tassertifikabelgesi",
        *_URUN_ADMIN,
        *_FIYATLAMA_TEKLIF_ADMIN,
    ),
    roles.PLATFORM_QUALITY: (
        P["manage_qc"],
        P["view_qc"],
        P["manage_qc_override"],
        "kalite.view_qualityinspection",
        "kalite.view_qualitymeasurement",
    ),
    roles.PLATFORM_LOGISTICS: (
        P["view_qc"],
        P["manage_shipment"],
        P["manage_return"],
        "kalite.view_qualityinspection",
        "kalite.view_qualitymeasurement",
        "lojistik.view_shipment",  # Django builtin
        "lojistik.view_returnrequest",
        "lojistik.view_returnline",
    ),
    roles.PLATFORM_SUPPORT: (),
    roles.ALICI_YONETICI: (
        P["manage_users"],
        P["manage_org"],
        P["manage_spend_limit"],
        P["manage_approval"],
        P["manage_rfq"],
        "firmalar.view_firma",
        "firmalar.view_kullanici",
        "firmalar.change_kullanici",
        "firmalar.view_orgbirimi",
        "firmalar.view_orguyeligi",
    ),
    roles.ALICI_SATINALMACI: (
        P["lock_quote"],
        P["manage_rfq"],
    ),
    roles.ALICI_ONAYLAYICI: (
        P["manage_approval"],
    ),
    roles.ALICI_FINANS: (
        P["manage_spend_limit"],
    ),
    roles.ALICI_DENETCI: (),
    roles.TEDARIKCI_SAHIP: (
        P["manage_users"],
        P["submit_urun"],
        P["manage_own_teklif"],
        P["manage_own_warehouse"],
        P["manage_document"],
        "belgeler.view_document",
        "belgeler.view_tassertifikabelgesi",
        *_URUN_ADMIN,
        *_FIYATLAMA_TEKLIF_ADMIN,
        "firmalar.view_firma",
        "firmalar.view_kullanici",
        "firmalar.change_kullanici",
    ),
    roles.TEDARIKCI_YONETICI: (
        P["manage_users"],
        P["submit_urun"],
        P["manage_own_teklif"],
        P["manage_own_warehouse"],
        P["manage_document"],
        "belgeler.view_document",
        "belgeler.view_tassertifikabelgesi",
        *_URUN_ADMIN,
        *_FIYATLAMA_TEKLIF_ADMIN,
    ),
    roles.TEDARIKCI_SATIS: (
        P["submit_urun"],
        P["manage_own_teklif"],
        "urunler.view_urun",
        "urunler.change_urun",
        "urunler.view_varyant",
        "urunler.change_varyant",
        "fiyatlama.view_tedarikciteklif",
        "fiyatlama.change_tedarikciteklif",
        "fiyatlama.add_tedarikciteklif",
    ),
    roles.TEDARIKCI_DEPO: (
        P["manage_own_warehouse"],
    ),
    roles.TEDARIKCI_FINANS: (),
}


def _permission(codename_full: str) -> Permission:
    app_label, codename = codename_full.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


@transaction.atomic
def seed_role_permissions(*, clear_unknown_role_groups: bool = False) -> dict:
    """Rol gruplarını oluşturur ve permission setlerini matrise eşitler (idempotent)."""
    stats = {"groups": 0, "synced": 0, "skipped_missing": 0}
    for role_code, perm_codes in ROLE_PERMISSION_MATRIX.items():
        group, _ = Group.objects.get_or_create(name=roles.role_group_name(role_code))
        stats["groups"] += 1
        wanted = []
        for full in perm_codes:
            try:
                wanted.append(_permission(full))
            except Permission.DoesNotExist:
                stats["skipped_missing"] += 1
        group.permissions.set(wanted)
        stats["synced"] += 1

    if clear_unknown_role_groups:
        known = {roles.role_group_name(r) for r in ROLE_PERMISSION_MATRIX}
        Group.objects.filter(name__startswith=roles.ROLE_GROUP_PREFIX).exclude(
            name__in=known
        ).delete()
    return stats
