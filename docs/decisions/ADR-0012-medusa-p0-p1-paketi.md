# ADR-0012 — Medusa_b2b türev P0/P1 paket (audit / FX / hedge / cari)

**Durum:** **Kabul** (ürün sahibi Emre, 2026-11-09)

> Bu dosya master §6.5'ten taşındı (2026-11-09). Analiz metni arşiv; bağlayıcı olan **Kabul kararları**dır.

### Onay checklist (2026-11-09)

| Madde | Durum |
|-------|--------|
| Ürün sahibi (Emre) Kabul | **Evet** |
| Kabul kapsamı | Faz 5 **tasarım / paket sınırları** (F5-K1…K10) |
| Kod / migration / yeni app | **Bu Kabul tek başına yetki vermez**; her dilim için ayrı açık talimat gerekir |
| B-01 / B-06 | Bu ADR ile değişmez (dokunulmadı) |

**Kaynak:** Medusa_b2b’den uyarlanmış 4 Cursor prompt’u (2026-11-08 ürün sahibi analizi talebi).  
**Bağlayıcı kısıt:** AGENTS faz sırası; üretim `migrate` izinsiz yok; F4 dilim 1–7 (Order+iptal) UYGULANDI — bu paket F4’ü kesmez; F5 kodu yalnız açık talimatla.

## Kabul kararları (bağlayıcı)

| ID | Karar |
|----|--------|
| F5-K1 | Paket: yeni Django app **`finans`** (ADR-0004). `fiyatlama/models/ledger.py` **açılmaz** (çift ledger yasak). |
| F5-K2 | **LedgerEntry** append-only: app UPDATE/DELETE + QuerySet engeli + PG trigger; ters kayıt yalnız **contra** (yeni satır). |
| F5-K3 | Para: `Decimal` + zorunlu ISO `para_birimi`; `tutar > 0`; yön `BORC`/`ALACAK` (`firma` hesabına göre). |
| F5-K4 | Audit: her başarılı hareket `record_audit`; fail → `record_audit_durable` (domain_atomic dışı). |
| F5-K5 | Cari taraflar (**U-005 Kabul** 2026-11-09): **platform↔alıcı**; tedarikçi↔alıcı Medusa kopyası sabitlenmez. `karsi_firma` nullable/PROTECT. |
| F5-K6 | FX pozisyon (FX-001; **U-013 Kabul** 2026-11-09): `open_has = locked_customer − unpaid_supplier − hedge`. `PriceLock.has_adet` **uydurulmaz**. `locked_customer` = AKTİF lock → quote `gram` toplamı. `unpaid_supplier` hak ediş (U-006) sonrası. |
| F5-K7 | Hedge (HEDGE-001): `finans.HedgeEntry` append-only; `grams ≠ 0`; FX toplamından düşülür. |
| F5-K8 | Checkout FX gate / Order charge: F4 checkout’a **erken bağlanmaz**; F5 gate ayrı dilim. |
| F5-K9 | AUD-001 çekirdek (immutability) UYGULANDI; `ip_address`/changes → AUD-001b (opsiyonel). |
| F5-K10 | Uygulama sırası: F5-001 (bu ADR) → F5-010 ledger → FX-001 + HEDGE-001 → F5-011 cari (U-005 notları) → PaymentIntent… |

## Özet eşleme (Kabul)

| Prompt | Öncelik | Hedef | Karar |
|--------|---------|-------|--------|
| 1 Immutable Audit | P0 çapraz | AUD-001 | Çekirdek UYGULANDI; rename yok |
| 2 FX pozisyon | P0 finans | FX-001 | F5-K6 |
| 3 Hedge | P1 finans | HEDGE-001 | F5-K7; audit `firmalar` |
| 4 Cari + kredi | P1 finans | F5-010/011 | `finans` app; U-005 F5-K5 |

## Prompt 1 — Immutable Audit Log (arşiv özeti)

**Mevcut (DOĞRULANDI):** `firmalar.AuditOlay` + `record_audit` / durable sidecar.  
**Kabul:** mevcut `entity_*` korunur; Medusa `target` rename yok. AUD-001b isteğe bağlı.

## Prompt 2 — FX pozisyon (HAS) (arşiv özeti)

**Mevcut (DOĞRULANDI):** PriceLock’ta `has_adet` yok.  
**Kabul:** F5-K6; checkout erken bağ yok (F5-K8).

## Prompt 3 — Hedge kayıt (arşiv özeti)

**Kabul:** F5-K7; `except Exception: pass` yasak; audit `firmalar.services.audit_servisi`.

## Prompt 4 — Cari + kredi limiti (arşiv özeti)

**Kabul:** F5-K1 + F5-K5; LedgerEntry F5-010; CariBalance F5-011.

## Çalıştırma sırası

1. F4 Cart→Checkout→Order+iptal **UYGULANDI**.  
2. AUD-001 çekirdek **UYGULANDI**.  
3. ADR-0012 **Kabul** (tasarım) → kod dilimleri yalnız açık talimat + U-* Kabul ile.  
4. U-005 / U-013 **Kabul** (2026-11-09, Emre override); U-006/U-009 Kabul metni BACKLOG’da — çelişirse yeni ADR.
