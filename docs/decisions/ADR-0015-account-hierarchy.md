# ADR-0015 — Account Hierarchy (firma-içi org/şube; U-014 A)

**Durum:** **Kabul** (ürün sahibi Qubit, 2026-11-09 — plan onayı)
**Bağımlılık:** ADR-0003 **Kabul** (metin değişmez); U-014 seçenek **A**; F4 Order UYGULANDI
**Kod:** F10-010…013 + F10-020 dilimleri; her dilim testli

> F10-001 kartı. Amaç: firma-içi hiyerarşi; tenant sınırı `Firma` kalır.

## Amaç

Alıcı (ve gerektiğinde tedarikçi) firmasında şube/org birimi scope’u.  
Kullanıcı hâlâ **tek firma + tek rol** (ADR-0003). Org üyelikleri firma içi ek scope verir; tenant’ı bölmez.

## Kabul kararları (OH-1…OH-6)

| ID | Karar |
|----|--------|
| OH-1 | Model **`firmalar.OrgBirimi`**: FK `firma`, opsiyonel `parent` (self), `kod`, `ad`, `aktif`. |
| OH-2 | **`OrgUyeligi`**: kullanıcı ↔ org birimi (M2M üzerinden ara tablo); tenant hâlâ `Kullanici.firma`. |
| OH-3 | `Order.sube` / `Cart.sube` **nullable** FK → `OrgBirimi` (PROTECT); yoksa null. |
| OH-4 | Selector: org scope ⊆ aktör firması; çapraz firma → DoesNotExist/404. |
| OH-5 | `view_all_tenants` org birimini tenant’a çevirmez; platform tüm org’ları görebilir. |
| OH-6 | Harcama limiti / onay SM / RFQ bu ADR’nin sınırları dışında ayrı dilimler (F10-012/013/020); org FK kullanır. |

## Kapsam dışı

- ADR-0003 metin değişikliği / çoklu firma üyeliği
- Şubeyi ayrı tenant yapmak
- Celery; zengin onay UI (F10-014); RFQ buyer UI (F10-023)

## Uygulama sırası

1. Bu ADR **Kabul** ← plan onayı  
2. F10-010 OrgBirimi + OrgUyeligi + Order/Cart.sube  
3. F10-011 org scope → F10-012 limit → F10-013 onay  
4. F10-020 RFQ modelleri  

## İlişkili

- BACKLOG: F10-001…020; U-014  
- ROADMAP §4 Faz 10; MASTER §12
