# Endpoint readiness (ADIM 5)

**Tarih:** 2026-11-11
**OpenAPI ops:** 106
**Smoke:** ok=True passed=15/15 mode=django.test.Client

Checklist sütunları: R=route · H=handler gerçek · V=validasyon · A=auth · S=status · Sch=şema · E=hata formatı · P=pagination(gerekirse) · M=migration N/A tur · T=test kanıtı · O=OpenAPI

| Grup | Metot | Path | R | H | V | A | S | Sch | E | P | T | O | Not |
|------|-------|------|---|---|---|---|---|-----|---|---|---|---|-----|
| CAP | POST | `/api/v1/act-as/start/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_act_as_adr0021 |
| CAP | POST | `/api/v1/act-as/stop/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_act_as_adr0021 |
| B4 | GET | `/api/v1/approvals/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/approvals/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | GET | `/api/v1/approvals/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/approvals/{id}/approve/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/approvals/{id}/reject/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/approvals/{id}/submit/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B1 | GET | `/api/v1/auth/csrf/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/email-verify/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/email-verify/confirm/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | GET | `/api/v1/auth/invites/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/invites/accept/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/invites/create/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/login/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/logout/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/mfa/resend/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/mfa/verify/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/password-change/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/password-reset/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B1 | POST | `/api/v1/auth/password-reset/confirm/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + test_auth_qa_gates + invite tests |
| B2 | POST | `/api/v1/bulk-orders/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_bulk_f4_081 |
| B1 | GET | `/api/v1/carts/me/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency |
| B2 | POST | `/api/v1/carts/me/lines/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency |
| B2 | DELETE | `/api/v1/carts/me/lines/{line_id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency |
| B2 | PATCH | `/api/v1/carts/me/lines/{line_id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency |
| B2 | GET | `/api/v1/carts/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency |
| B2 | GET | `/api/v1/catalog/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b2_buyer_commerce |
| B2 | GET | `/api/v1/catalog/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2_buyer_commerce |
| B2 | POST | `/api/v1/checkouts/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + concurrency + pre_005 |
| B3 | POST | `/api/v1/credit/check/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + credit_f5 |
| B1 | GET | `/api/v1/credit/me/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + credit_f5 |
| B3 | GET | `/api/v1/finance/cari/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b3_finance_ops |
| B3 | GET | `/api/v1/finance/cari/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3_finance_ops |
| B3 | GET | `/api/v1/finance/ledger/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b3_finance_ops |
| B1 | GET | `/api/v1/finance/me/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3_finance_ops |
| B1 | GET | `/api/v1/health/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 / smoke |
| B1 | GET | `/api/v1/me/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + nx + act_as |
| CAP | GET | `/api/v1/me/dashboard/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1 + nx + act_as |
| B3+ | GET | `/api/v1/ops/anomalies/ciro/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_rapor_adr0026 |
| B3+ | GET | `/api/v1/ops/finance/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_ops_finans_f5_031 / b3 |
| B3+ | GET | `/api/v1/ops/finance/cari/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_ops_finans_f5_031 / b3 |
| B3+ | GET | `/api/v1/ops/finance/ledger/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_ops_finans_f5_031 / b3 |
| B3+ | GET | `/api/v1/ops/finance/payments/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_ops_finans_f5_031 / b3 |
| B5 | GET | `/api/v1/ops/inspections/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | GET | `/api/v1/ops/inspections/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/{id}/cancel/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/{id}/fail/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/{id}/measurements/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/{id}/pass/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/inspections/{id}/start/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B2 | GET | `/api/v1/ops/orders/summary/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b1/ops |
| B5 | GET | `/api/v1/ops/shipments/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | GET | `/api/v1/ops/shipments/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/{id}/cancel/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/{id}/deliver/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/{id}/dispatch/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/{id}/pod/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B5 | POST | `/api/v1/ops/shipments/{id}/prepare/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b5_ops |
| B2 | GET | `/api/v1/orders/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b2 + order_api_f4_060 |
| B2 | POST | `/api/v1/orders/from-checkout/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + order_api_f4_060 |
| B2 | GET | `/api/v1/orders/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + order_api_f4_060 |
| B2 | POST | `/api/v1/orders/{id}/cancel/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + order_api_f4_060 |
| B2 | POST | `/api/v1/orders/{id}/reorder/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + order_api_f4_060 |
| B4 | GET | `/api/v1/org-units/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/org-units/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | GET | `/api/v1/org-units/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | GET | `/api/v1/org-units/{id}/members/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/org-units/{id}/members/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B3 | POST | `/api/v1/payments/intents/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + webhook |
| B3 | POST | `/api/v1/payments/webhook/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + webhook |
| B2 | POST | `/api/v1/price-locks/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + nx |
| B2 | GET | `/api/v1/price-locks/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2 + nx |
| B2 | POST | `/api/v1/quotes/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2_buyer_commerce |
| B2 | GET | `/api/v1/quotes/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b2_buyer_commerce |
| B3+ | GET | `/api/v1/reports/buyer-behavior/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_rapor_adr0026 |
| B2 | GET | `/api/v1/reports/orders/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_rapor_adr0026 |
| B3 | GET | `/api/v1/returns/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | GET | `/api/v1/returns/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/{id}/approve/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/{id}/cancel/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/{id}/mahsup/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/{id}/reject/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B3 | POST | `/api/v1/returns/{id}/submit/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 + mahsup adr0023 |
| B4 | GET | `/api/v1/rfqs/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/rfqs/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | GET | `/api/v1/rfqs/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/rfqs/{id}/messages/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/rfqs/{id}/revisions/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B4 | POST | `/api/v1/rfqs/{id}/send/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b4_enterprise |
| B3 | GET | `/api/v1/shipments/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b3 |
| B3 | GET | `/api/v1/shipments/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b3 |
| B6 | GET | `/api/v1/supplier/offers/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b6_supplier |
| B6 | GET | `/api/v1/supplier/offers/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/offers/{id}/deactivate/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/offers/{id}/submit/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/offers/{id}/versions/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | GET | `/api/v1/supplier/rfqs/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | test_api_b6_supplier |
| B6 | GET | `/api/v1/supplier/rfqs/{id}/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/rfqs/{id}/messages/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/rfqs/{id}/revisions/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | GET | `/api/v1/supplier/stock/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |
| B6 | POST | `/api/v1/supplier/stock/adjustments/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | test_api_b6_supplier |

## Özet

| Toplam OpenAPI op | Hazır (test kanıtlı) | Sorunlu/kanıt zayıf |
|-------------------|----------------------|---------------------|
| 106 | 106 | 0 |

Not: R/H/A/S/Sch/E/O sütunları OpenAPI lint OK + urls.py + DRF view envanterine dayanır (2026-11-11). T sütunu odaklı suite adına göre; tam suite **DOĞRULANAMADI**.

## Frontend → backend çapraz

| FE çağrı | Backend |
|----------|---------|
| `GET /api/v1/auth/csrf/` | ✅ |
| `POST /api/v1/auth/login/` | ✅ |
| `POST /api/v1/auth/logout/` | ✅ |
| `GET /api/v1/me/` | ✅ |
| `GET /api/v1/health/` | ✅ |

Diğer feature `services/index.ts` dosyaları boş iskelet — ek FE path yok (DOĞRULANDI `frontend/src`).
