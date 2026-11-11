# Kuyumbank — Backend haritası (FE tek doğruluk kaynağı)

**Tarih:** 2026-11-11  
**Normatif şema:** [`docs/api/openapi-v1.json`](api/openapi-v1.json) (**106** path / **120** op)  
**İnsan özeti:** [API_CONTRACT](API_CONTRACT.md) · Handoff: [FRONTEND_HANDOFF](FRONTEND_HANDOFF.md)  
**TS tipler:** `frontend/lib/api/schema.d.ts` (`npm run generate:api`)  
**Kanıt:** kod + OpenAPI; bu dosya sonraki FE oturumlarında kodu baştan taramayı önler.

> Varsayım (ADIM 3.2): müşteri şikayeti metni boş bırakıldı → dilim 2 atlandı; öncelik dilim 3 (katalog / karşılaştırma / sipariş-RFQ).

---

## 1. Auth akışı

| Adım | Method | Path | Not |
|------|--------|------|-----|
| CSRF | GET | `/api/v1/auth/csrf/` | `csrf_token` + `csrftoken` cookie; AllowAny |
| Login | POST | `/api/v1/auth/login/` | `{username,password}` → session + `MeResponse` + `mfa_required`/`mfa_ok` |
| MFA | POST | `/api/v1/auth/mfa/verify/` · `/mfa/resend/` | Platform MFA açıksa |
| Me | GET | `/api/v1/me/` | kimlik + `capabilities` (UI keşif; güvenlik değil) |
| Logout | POST | `/api/v1/auth/logout/` | session kapanır + kullanıcının DRF Token silinir |
| Reset / change | POST | `/auth/password-reset/` · `/confirm/` · `/password-change/` | |
| Invite / email | POST/GET | `/auth/invites/*` · `/auth/email-verify/*` | ADR-0028 |
| Act-as | POST | `/act-as/start/` · `/stop/` | platform `act_as_user` |

**Oturum modeli (tarayıcı):** Session cookie (HttpOnly) + CSRF header `X-CSRFToken`. **Refresh token yok.** Tarayıcıda DRF Token yok (NX-1). S2S: TokenAuthentication.

**Login yanıt alanları:** `id`, `username`, `rol`, `email_verified`, `firma` `{id,ad,alici_mi,tedarikci_mi,platform_mu,aktif}`, `firma_id`, `capabilities`, (+ MFA bayrakları).

---

## 2. Rol / yetki mantığı

### 2.1 Roller (`firmalar.roles`)

| Grup | Kodlar |
|------|--------|
| Platform | `platform_super`, `platform_admin`, `platform_ops`, `platform_finance`, `platform_catalog`, `platform_quality`, `platform_logistics`, `platform_support` |
| Alıcı | `alici_yonetici`, `alici_satinalmaci`, `alici_onaylayici`, `alici_finans`, `alici_denetci` |
| Tedarikçi | `tedarikci_sahip`, `tedarikci_yonetici`, `tedarikci_satis`, `tedarikci_depo`, `tedarikci_finans` |

- Kullanıcı **tek firmaya** bağlı (`Kullanici.firma`).
- Süper kullanıcı / staff: Django Admin; API’de asıl kapı `rol` + permission grupları.
- Firma admini ≈ `*_yonetici` / `*_sahip` + `manage_users` matrisi.
- Fonksiyon izinleri: `firmalar.role_permissions.P` → Django `Group` (`rol:<kod>`).

### 2.2 Önemli perm kodları (`P`)

`view_all_tenants`, `manage_users`, `manage_all_users`, `act_as_user`, `manage_own_teklif`, `approve_teklif`, `lock_quote`, `manage_own_warehouse`, `manage_qc`/`view_qc`, `manage_shipment`, `manage_return`, `manage_org`, `manage_approval`, `manage_rfq`, `submit_urun`/`approve_urun`/`publish_urun`, …

### 2.3 Commerce SoD (API)

| | Okuma | Yazma (quote/cart/checkout/order) |
|--|-------|-----------------------------------|
| Alıcı yönetici / satınalmacı | ✓ | ✓ |
| Alıcı onaycı / denetçi / finans | ✓ | ✗ |
| Ops `view_all` / QC-lojistik okuma | ✓ (order) | ✗ buyer yazma |
| Tedarikçi | ✗ buyer commerce | ✗ |
| `platform_support` | buyer commerce kapalı | — |

### 2.4 `/me` capabilities (menü bayrakları)

`can_checkout`, `can_view_catalog`, `can_view_cart`, `can_view_orders`, `can_view_finance`, `can_view_credit`, `can_view_shipments`, `can_approve`, `can_manage_rfq`, `can_manage_org`, `can_lock_quote`, `can_manage_offers`, `can_view_supplier_stock`, `can_view_ops`, `can_view_ops_finance`, `can_manage_qc`, `can_manage_shipment`, `can_manage_return`, `can_manage_users`, `can_manage_addresses`.

---

## 3. Endpoint haritası

**Ortak:** Base `/api/v1/`. Hata: `application/problem+json`. Liste: `{count,next,previous,page,page_size,results}`. Decimal/para/gram: **string**. Yazma: CSRF + çoğu commerce `Idempotency-Key`.

**Rol sütunu:** B=buyer · S=supplier · O=ops(`view_all`/QC/lojistik) · F=finance ops · A=anon · * = ilgili perm.

### 3.1 Auth / me / act-as

| Method | Path | Rol | Request | Response |
|--------|------|-----|---------|----------|
| GET | `/health/` | A | — | `{status,service,api}` |
| GET | `/ready/` | A | — | DB ready / 503 |
| GET | `/auth/csrf/` | A | — | `{csrf_token}` |
| POST | `/auth/login/` | A | `LoginRequest` | `MeResponse` + MFA |
| POST | `/auth/logout/` | auth | — | `{ok}` |
| POST | `/auth/mfa/verify/` | auth | OTP | `MeResponse` |
| POST | `/auth/mfa/resend/` | auth | — | ok |
| POST | `/auth/password-reset/` | A | `{email}` | genel mesaj |
| POST | `/auth/password-reset/confirm/` | A | token+şifre | ok |
| POST | `/auth/password-change/` | auth | eski/yeni | ok |
| GET/POST | `/auth/invites/` · `/create/` · `/accept/` | * | invite DTO | invite |
| POST | `/auth/email-verify/` · `/confirm/` | auth | — | ok |
| GET | `/me/` | firma | — | `MeResponse` |
| GET | `/me/dashboard/` | B | — | `MeDashboard` |
| GET/PATCH | `/me/profile/` | firma | patch alanları | `MeProfile` |
| GET/POST | `/me/addresses/` | firma | adres | adres |
| GET/PATCH/DELETE | `/me/addresses/{id}/` | `manage_users` yazma | — | adres |
| POST | `/act-as/start/` · `/stop/` | `act_as_user` | target user | ok |

### 3.2 Buyer commerce (B2)

| Method | Path | Rol | Request | Response |
|--------|------|-----|---------|----------|
| GET | `/catalog/` | B/O | `page`, `q` | `BuyerCatalogPage` — item: `id,ad,platform_kodu,kategori,ayar,fiyat_tipi,varyant_count,yayin_durumu,allowed_actions` |
| GET | `/catalog/{id}/` | B/O | — | `BuyerCatalogDetail` + `varyantlar` (**tedarikçi yok**) |
| GET | `/sales-channels/` | firma | — | `{count,results[{id,kod,ad,quote_ttl_saniye}]}` — quote `satis_kanali_id` keşfi |
| POST | `/quotes/` | B yazma | `{varyant_id,satis_kanali_id?,para_birimi?}` | `BuyerQuote` |
| GET | `/quotes/{id}/` | B/O | — | `BuyerQuote` |
| POST | `/price-locks/` | B + lock | `{quote_id}` | `BuyerPriceLock` |
| GET | `/price-locks/{id}/` | B/O | — | `BuyerPriceLock` |
| GET | `/carts/me/` | B/O | — | `BuyerCart` |
| POST | `/carts/me/lines/` | B yazma | `{quote_id,miktar}` | line |
| PATCH/DELETE | `/carts/me/lines/{line_id}/` | B yazma | `{miktar}` | line / 204 |
| GET | `/carts/{id}/` | B/O | — | `BuyerCart` |
| POST | `/checkouts/` | B yazma | (cart context) | `CheckoutResult` |
| POST | `/orders/from-checkout/` | B yazma | `{checkout_id}` | `BuyerOrder` |
| GET | `/orders/` · `/{id}/` | B/O | page | `BuyerOrder` — `durum,lines,snapshots` |
| POST | `/orders/{id}/cancel/` · `/reorder/` | B yazma | reorder:`replace_cart?` | order/cart |
| POST | `/bulk-orders/` | B yazma | csv/rows | `BulkOrderResult` |

### 3.3 Finans / sevkiyat / iade (B3)

| Method | Path | Rol | Not |
|--------|------|-----|-----|
| GET | `/finance/me/` · `/cari/` · `/cari/{id}/` · `/ledger/` | B | maskeli |
| GET | `/credit/me/` · POST `/credit/check/` | B | |
| POST | `/payments/intents/` | B | `{order_id}` |
| POST | `/payments/webhook/` | A/provider | ayrı auth |
| GET | `/shipments/` · `/{id}/` | B | R |
| GET/POST | `/returns/` · aksiyonlar | B + O `manage_return` | submit/approve/reject/cancel/mahsup |

### 3.4 Kurumsal (B4)

| Method | Path | Rol |
|--------|------|-----|
| `/org-units/` CRUD-lite + `/members/` | `manage_org` |
| `/approvals/` + submit/approve/reject | `manage_approval` |
| `/rfqs/` + send/messages/revisions | B `manage_rfq` |

### 3.5 Ops (B5 + eşleştirme)

| Method | Path | Rol |
|--------|------|-----|
| `/ops/finance/*` | O/F |
| `/ops/orders/summary/` · `/ops/anomalies/ciro/` | O |
| `/ops/inspections/*` | `view_qc`/`manage_qc` |
| `/ops/shipments/*` | `manage_shipment` |
| `/ops/rfq-lines/{line_id}/match-candidates/` · `/matches/` | O |
| `/ops/rfq-matches/{id}/approve|reject/` | O |

### 3.6 Supplier (B6)

| Method | Path | Rol | Request/Response |
|--------|------|-----|------------------|
| GET/POST | `/supplier/offers/` | S (+ O view_all) | Create: `varyant_id,birim_fiyat,gram,…` → `SupplierOffer` |
| GET | `/supplier/offers/{id}/` | S | |
| POST | `…/submit/` · `/deactivate/` · `/versions/` | S | version: fiyat/gram |
| GET | `/supplier/stock/` | S/O | özet |
| POST | `/supplier/stock/adjustments/` | S | hareket |
| GET | `/supplier/rfqs/` · `/{id}/` + messages/revisions | S | **alıcı kimliği yok** |

### 3.7 Raporlar

| GET | `/reports/orders/` · `/reports/buyer-behavior/` | B/O |

Tam alan listesi: OpenAPI `components.schemas.*` + `schema.d.ts`.

---

## 4. Ana modeller ve ilişkiler

```text
Firma (alici_mi | tedarikci_mi | platform_mu)
  └── Kullanici (rol, email_verified_at)
  └── OrgBirimi / OrgUyeligi / HarcamaLimiti / OnayTalebi / FirmaInvite / FirmaAdresi

Kategori ──< Urun ──< Varyant (gram, renk, beden, sku…)
                └── UrunTasi, UrunKanal

Varyant ──< TedarikciTeklif (tedarikci Firma, versiyon, birim_fiyat, gram…)
              └── StockBalance / StockMovement / StockReservation (Warehouse)

PriceQuote (alici_firma, varyant, teklif ref, satırlar) ── PriceLock ── OrderLine
Cart ── CartLine(quote) ── CheckoutAttempt ── Order ── OrderLine (snapshot + lock + reservation)

RFQ ── RFQLine ── RFQEslestirme (önerilen_varyant) ; RFQMessage ; RFQRevizyon

FiyatSozlesmesi ── kalemler ; ContractReleasePlan/Event/Consumption
CariHesap / LedgerEntry / PaymentIntent ; TedarikciHakEdis
QualityInspection ; Shipment / ReturnRequest
```

**Alıcı fiyatı:** quote (platform); siparişte snapshot + PriceLock.  
**Kör havuz:** buyer DTO’da tedarikçi kimlik/maliyet yok (`api/masking.FORBIDDEN_KEYS` — **DOĞRULANDI**).

---

## 5. Kör havuz (kritik)

| Kural | Durum |
|-------|--------|
| Buyer catalog/quote/order’da `tedarikci_*` / maliyet yok | **OK** — masking + presenters |
| Supplier RFQ’da alıcı firma/şube yok | **OK** |
| Client `firma_id` / `tedarikci_id` güvenilmez | **OK** — sunucu `request.user.firma` |
| FE müşteri UI’da tedarikçi ipucu | **FE sorumluluğu** — backend filtreye güven; ekstra alan gösterme |

---

## 6. Eksikler / FE’yi bloke edenler (max 10)

1. **Kritik — Sipariş→tedarikçi yönlendirme HTTP yok:** Sipariş alıcıya aittir; admin’in “siparişi tedarikçiye ata” ayrı uç yok. Operasyon yolu: **RFQ eşleştirme** (`/ops/rfq-matches/*`) + teklif/stok. Dilim 4’te bu API’ye map et; eksik iş kuralı varsa küçük backend ekle.
2. ~~**Kritik — Platform ürün CRUD API yok**~~ → **ADR-0030 UYGULANDI:** `/api/v1/ops/products/` (+ variants/submit/approve/reject/publish/unpublish).
3. **Kullanıcı/izin yönetimi API sınırlı:** Invite + profile; tam RBAC UI için Admin veya genişletme gerekir.
4. **Karşılaştırma endpoint’i yok:** Aynı özellik (gram/çeşit) karşılaştırması FE’de `/catalog` + detay ile yapılır; sunucu-side compare yok. (`GET /sales-channels/` eklendi — quote kanal keşfi.)
5. **Tek portal iskeleti:** Next’te buyer/supplier/admin ayrımı henüz yoktu (bu dilimde eklenecek); domain stub menü yanlış yönlendiriyordu.
6. **Refresh token yok:** Session süresi Django ayarına bağlı; FE re-login akışı gerekir (bilinçli).
7. **Redis/Celery yok:** Kullanıcı yığınında Redis 7 geçse de runtime’da yok (MASTER); kuyruk/cache varsayma.
8. **CORS erteli:** Yalnız same-origin rewrite; ayrı origin credentialed çağrı yok.
9. **ADR-0017 bütünü Taslak:** NX maddeleri Kabul; sözleşme riski düşük ama ADR Kabul değil.
10. **Dilim 2 şikayet metni boş:** Öncelik dilim 3’e kaydırıldı (bu belgede not).

---

## 7. FE portal yönlendirme (varsayım)

| Koşul | Portal kökü |
|-------|-------------|
| `firma.platform_mu` veya `capabilities.can_view_ops` | `/admin` |
| `firma.tedarikci_mi` (ve alıcı değil / ops değil) | `/supplier` |
| `firma.alici_mi` | `/buyer` |
| Belirsiz | `/login` |

Admin, tedarikçi yüzeyindeki aksiyonları da (`/supplier/*` + ops) yetkisi varsa kullanabilir (`view_all` + ilgili perm).
