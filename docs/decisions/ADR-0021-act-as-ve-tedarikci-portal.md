# ADR-0021 — Act-as (kullanıcı gözü) + tedarikçi HTML portal + demo seed

**Durum:** **Kabul** (2026-11-10, ürün sahibi Qubit — öncelik sırasıyla uygulama talimatı)  
**Bağımlılık:** ADR-0003 (RBAC/audit), ADR-0009 (admin), F4-062 / F9 buyer UI, F7 supplier API  
**Kapsam:** CAP-ACTAS · CAP-SUP-UI

## Amaç

1. Platform yetkilisinin seçilen kullanıcı **gözüyle** `/buyer/` veya `/supplier/` gezmesi (impersonation).  
2. Tedarikçi için minimal HTML portal (teklif / stok / RFQ listesi).  
3. Yerel demo alıcı + tedarikçi kullanıcı seed.

## Kararlar (Kabul)

| ID | Karar |
|----|--------|
| AA-1 | Yetki: `firmalar.act_as_user` (platform_super / platform_admin matrisi). `is_superuser` tek başına yetmez (`yetki_servisi`). |
| AA-2 | Session: `act_as_actor_id` + `act_as_target_id`; middleware hedefi `request.user` yapar; `request.act_as_actor` gerçek aktör. |
| AA-3 | Act-as sırasında banner zorunlu; durdurma tek tık; iç içe act-as yok. |
| AA-4 | Audit: `user.act_as_start` / `user.act_as_stop` (başarı + fail durable). |
| AA-9 | Act-as süresince tüm `record_audit*`: `actor` = gerçek operatör (`act_as_actor`), `on_behalf_of` = hedef kullanıcı (inkâr edilemezlik). Middleware `act_as_audit_context`. |
| AA-5 | Hedef: aktif kullanıcı; kendini seçemez; platform→platform serbest (debug). |
| AA-6 | `/buyer/` ve `/supplier/` HTML: `view_all` ops kullanıcıları **doğrudan** giremez; act-as veya gerçek tenant gerekir. |
| AA-7 | Tedarikçi portal `/supplier/`: teklif/stok/RFQ **okuma** iskeleti; yazma API’de kalır (v1). |
| AA-8 | Demo seed: `DEMO_ALICI` / `DEMO_TEDARIKCI` + kullanıcılar; yalnız local/dev; şifre komut çıktısı. |

## Kabul checklist

| Madde | Durum |
|-------|--------|
| Ürün sahibi Kabul | **Evet** |
| Act-as servis + middleware + admin | Bu dilim |
| Buyer/supplier banner + stop | Bu dilim |
| `/supplier/` HTML | Bu dilim |
| `seed_demo_portals` | Bu dilim |
| AA-9 audit `on_behalf_of` (inkâr edilemezlik) | UYGULANDI (`firmalar.0010`) |
