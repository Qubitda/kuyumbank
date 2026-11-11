# CRUD Matrix — 2026-11-11

Kaynak: `docs/api/openapi-v1.json` (106 op / 98 path) + `backend/config/api/urls.py` + MASTER/ADR/API_CONTRACT.  
Durum: **VAR** | **EKSİK** | **KAPSAM DIŞI** (imzalı gerekçe).

Roller: B=buyer · BA=buyer-admin · S=supplier · O=ops/platform · A=admin(Django)

| Kaynak | C | R | U | D / aksiyon | Rol | Durum | Gerekçe |
|--------|---|---|---|-------------|-----|-------|---------|
| catalog | — | GET list/detail | — | — | B | VAR | `/catalog/` |
| carts / lines | POST line | GET cart | PATCH qty | DELETE line | B | VAR | `/carts/` |
| quotes | POST | GET | — | — | B | VAR | `/quotes/` |
| price-locks | POST | GET | — | — | B | VAR | `/price-locks/` |
| checkouts | POST | — | — | — | B | VAR | `/checkouts/` |
| orders | — | GET list/detail | — | cancel, reorder | B/O | VAR | `/orders/` |
| bulk-orders | POST | — | — | — | B | VAR | `/bulk-orders/` |
| rfqs (buyer) | POST | GET | — | send, msg, rev | B | VAR | `/rfqs/` |
| rfqs eşleştirme | POST öner | GET aday/liste | — | approve/reject | O | **VAR** | `/ops/rfq-lines|rfq-matches/` |
| supplier offers | POST create | GET | version | submit, deactivate | S | **VAR** | `POST /supplier/offers/` → `taslak_olustur` |
| supplier stock | adjust POST | GET | — | — | S | VAR | `/supplier/stock/` |
| supplier rfqs | — | GET | — | msg, rev | S | VAR | ters kör |
| org-units | POST | GET | — | add member | BA | VAR | update/deactivate FE v1 dışı imza |
| approvals | POST | GET | — | submit/approve/reject | BA | VAR | |
| returns | POST | GET | — | approve/reject/mahsup | B/O | VAR | |
| shipments (buyer) | — | GET | — | — | B | VAR | |
| ops inspections | POST | GET | — | start/pass/fail/cancel/meas | O | VAR | |
| ops shipments | POST | GET | — | prepare/dispatch/deliver/cancel/pod | O | VAR | |
| ops finance/reports | — | GET | — | — | O | VAR | |
| invites | create/list | GET | — | accept (anon) | BA/A | VAR | |
| auth/me | — | GET me/dashboard | password/MFA | logout | * | VAR | |
| profile/adres | POST adres | GET profile/adres | PATCH | DELETE adres | * / BA yazma | **VAR** | F9-017: `/me/profile/`, `/me/addresses/` · `test_profile_address_f9_017` |
| bildirimler HTTP | — | — | — | — | — | **KAPSAM DIŞI** | Outbox/admin; portal list API yok (ADR-0027) |
| payments | intent POST | — | — | webhook | B/* | VAR | |
| credit/finance | — | GET | — | check | B | VAR | |
| act-as | start/stop | — | — | — | O | VAR | |

## Süreç zinciri (ADIM 2 özet)

| Akış | Kopuk halka |
|------|-------------|
| a) Alıcı commerce | Yok (catalog→…→mahsup HTTP var) |
| b) RFQ | Eşleştirme HTTP VAR (platform ops) |
| c) Tedarikçi | Teklif create + lifecycle + stock VAR |
| d) Ops | Inspection/shipment/finance/report VAR |
| e) Kurumsal | Org/onay/invite + profil/adres VAR |

## HTML tarama (mimari kilit)

`rg` portal HTML: yalnız `bildirim.template_servisi.render` (e-posta) + admin inline toplu red string — portal TemplateView **yok**.
