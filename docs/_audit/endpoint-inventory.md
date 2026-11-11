# Endpoint Inventory (ADIM 0)

**Tarih:** 2026-11-11
**Kaynak kod:** `backend/config/api/urls.py` + `config/urls.py` + `api/docs_urls.py` + `firmalar/urls_act_as.py`
**OpenAPI:** `docs/api/openapi-v1.json`

## 0.1 Doküman envanteri (git last commit)

| Dosya | Son commit tarihi | Hash | Konu |
|-------|-------------------|------|------|
| ﻿AGENTS.md | 2026-11-10 14:45:21 | 4bf4a65 | ﻿docs+api: OpenAPI request/response DTO, Swagger/ReDoc, FE r |
| README.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| backend/README.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/MASTER.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/API_CONTRACT.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/API_READINESS.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/BACKLOG.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/DATA_DICTIONARY.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/HISTORY.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/ROADMAP.md | 2026-11-10 14:45:21 | 4bf4a65 | ﻿docs+api: OpenAPI request/response DTO, Swagger/ReDoc, FE r |
| docs/RUNBOOK.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/api/openapi-v1.json | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| frontend/README.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/AGENTS.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/docs/API.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/docs/FRONTEND_ARCHITECTURE.md | 2026-11-10 14:45:21 | 4bf4a65 | ﻿docs+api: OpenAPI request/response DTO, Swagger/ReDoc, FE r |
| frontend/docs/COMPONENT_GUIDELINES.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/docs/DESIGN_SYSTEM.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/docs/PAGE_PATTERNS.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| frontend/docs/UI_UX_GUIDELINES.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| docs/decisions/ADR-0001-agent-standartlari.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0002-runtime-ve-bagimliliklar.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0003-addendum-view-all-scope.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0003-faz1-kimlik-rbac.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0004-modular-python-organizasyon.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0005-bekleyen-kararlar.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0005-katalog-platform-ownership.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0006-faz2-1-kararlar.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0007-faz3-fiyatlama.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0008-faz3b-kur-fiyatlama-quote.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| docs/decisions/ADR-0009-admin-yuzey-sertlestirme.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0010-pricelock.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0011-faz4-ticari-cekirdek.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0012-medusa-p0-p1-paketi.md | 2026-11-09 16:37:02 | 3d2f069 | feat: F5 finans paketi, F6-010 QC SM ve dokuman handoff sync |
| docs/decisions/ADR-0013-faz6-qc-lojistik.md | 2026-11-09 18:49:15 | 17b56e6 | feat: F5-F6 politika, F4-070b/KS-6, F10 hierarchy ve F7 API  |
| docs/decisions/ADR-0014-karlilik-simulasyonu.md | 2026-11-09 18:49:15 | 17b56e6 | feat: F5-F6 politika, F4-070b/KS-6, F10 hierarchy ve F7 API  |
| docs/decisions/ADR-0015-account-hierarchy.md | 2026-11-09 18:49:15 | 17b56e6 | feat: F5-F6 politika, F4-070b/KS-6, F10 hierarchy ve F7 API  |
| docs/decisions/ADR-0016-faz9-frontend.md | 2026-11-09 20:47:23 | b529e5e | feat(api): B1–B3 kabul teslimatı, OpenAPI düzeltmesi ve otur |
| docs/decisions/ADR-0017-nextjs-api-sozlesmesi.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| docs/decisions/ADR-0018-cap-piyasa-kur-dayanikliligi.md | 2026-11-10 14:45:21 | 4bf4a65 | ﻿docs+api: OpenAPI request/response DTO, Swagger/ReDoc, FE r |
| docs/decisions/ADR-0019-object-level-drf.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0020-piyasa-panosu-baz-fiyat.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0021-act-as-ve-tedarikci-portal.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0022-piyasa-panosu-v2-domain.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0023-mahsup-http.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0024-pano-quote-baglama.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0025-pano-ons-kg.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0026-rapor-http.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/ADR-0027-email-bildirim.md | NO_GIT_HISTORY |  |  |
| docs/decisions/ADR-0028-invite-email-verify.md | NO_GIT_HISTORY |  |  |
| docs/decisions/ADR-0029-api-only-html-portal-kaldirma.md | NO_GIT_HISTORY |  |  |
| docs/decisions/NOTE-F11-001-raporlama-v1.md | 2026-11-10 13:58:06 | 78b2eec | feat: CAP-PIYASA/ALERT, F11 raporlama, ADR-0019 object-level |
| docs/decisions/NOTE-PENDING-PRODUCT-DECISIONS.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |
| docs/decisions/README.md | 2026-11-10 17:30:55 | 8c2cde3 | feat: act-as AA-9 audit, ops throttle/purge, piyasa ADR-0020 |

Not: `NO_GIT_HISTORY` = diskte var, henüz commit edilmemiş (DOĞRULANDI `git log`).

## 0.2 Özet sayılar

| Kaynak | Adet |
|--------|------|
| Django `/api*` + `/act-as*` route kaydı | 104 |
| OpenAPI path | 98 |
| OpenAPI operation (method×path) | 106 |

## 0.3 Django route tablosu

| Metot | Yol | Name | Handler | permission_classes | Auth override | Serializer |
|-------|-----|------|---------|--------------------|---------------|------------|
| ? | `/act-as/start/<int:user_id>/` | act-as-start | `?` | (DRF default) | (settings default) | — |
| ? | `/act-as/stop/` | act-as-stop | `?` | (DRF default) | (settings default) | — |
| GET | `/api/docs/` | openapi-docs | `api.docs_urls._DocsSwaggerView` | AllowAny | (settings default) | — |
| GET | `/api/redoc/` | openapi-redoc | `api.docs_urls._DocsRedocView` | AllowAny | (settings default) | — |
| GET | `/api/schema/` | openapi-schema | `api.schema_views.EnrichedOpenAPISchemaView` | IsAuthenticated | (settings default) | — |
| POST | `/api/v1/act-as/start/` | api-act-as-start | `api.views.act_as.ActAsStartView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/act-as/stop/` | api-act-as-stop | `api.views.act_as.ActAsStopView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/approvals/` | api-approval-list | `api.views.approvals.ApprovalListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/approvals/<int:pk>/` | api-approval-detail | `api.views.approvals.ApprovalDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/approvals/<int:pk>/approve/` | api-approval-approve | `api.views.approvals.ApprovalApproveView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/approvals/<int:pk>/reject/` | api-approval-reject | `api.views.approvals.ApprovalRejectView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/approvals/<int:pk>/submit/` | api-approval-submit | `api.views.approvals.ApprovalSubmitView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/auth/csrf/` | api-auth-csrf | `api.views.auth.AuthCsrfView` | AllowAny | (settings default) | — |
| POST | `/api/v1/auth/email-verify/` | api-auth-email-verify-request | `api.views.invite_auth.EmailVerifyRequestView` | AllowAny | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/email-verify/confirm/` | api-auth-email-verify-confirm | `api.views.invite_auth.EmailVerifyConfirmView` | AllowAny | (settings default) | — |
| GET | `/api/v1/auth/invites/` | api-auth-invite-list | `api.views.invite_auth.InviteListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/invites/accept/` | api-auth-invite-accept | `api.views.invite_auth.InviteAcceptView` | AllowAny | (settings default) | — |
| POST | `/api/v1/auth/invites/create/` | api-auth-invite-create | `api.views.invite_auth.InviteCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/login/` | api-auth-login | `api.views.auth.AuthLoginView` | AllowAny | (settings default) | — |
| POST | `/api/v1/auth/logout/` | api-auth-logout | `api.views.auth.AuthLogoutView` | IsAuthenticated | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/mfa/resend/` | api-auth-mfa-resend | `api.views.auth.MfaResendView` | IsAuthenticated | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/mfa/verify/` | api-auth-mfa-verify | `api.views.auth.MfaVerifyView` | IsAuthenticated | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/password-change/` | api-auth-password-change | `api.views.auth.PasswordChangeView` | IsAuthenticated | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/auth/password-reset/` | api-auth-password-reset | `api.views.auth.PasswordResetRequestView` | AllowAny | (settings default) | — |
| POST | `/api/v1/auth/password-reset/confirm/` | api-auth-password-reset-confirm | `api.views.auth.PasswordResetConfirmView` | AllowAny | (settings default) | — |
| POST | `/api/v1/bulk-orders/` | api-bulk-order-create | `api.views.bulk_order.BulkOrderCreateView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/carts/<int:pk>/` | api-cart-detail | `api.views.cart.CartDetailView` | HasCartObjectAccess | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/carts/me/` | api-cart-mine | `api.views.buyer_cart.CartMineView` | IsBuyerCommerceRead | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/carts/me/lines/` | api-cart-line-create | `api.views.buyer_cart.CartLineCreateView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| PATCH,DELETE | `/api/v1/carts/me/lines/<int:line_id>/` | api-cart-line-detail | `api.views.buyer_cart.CartLineDetailView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/catalog/` | api-buyer-catalog | `api.views.catalog.BuyerCatalogListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/catalog/<int:pk>/` | api-buyer-catalog-detail | `api.views.catalog.BuyerCatalogDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/checkouts/` | api-checkout-create | `api.views.checkout.CheckoutCreateView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/credit/check/` | api-credit-check | `api.views.credit.CreditCheckView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/credit/me/` | api-credit-mine | `api.views.credit.CreditMineView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/finance/cari/` | api-finance-cari | `api.views.finance.BuyerCariListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/finance/cari/<int:pk>/` | api-finance-cari-detail | `api.views.finance.BuyerCariDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/finance/ledger/` | api-finance-ledger | `api.views.finance.BuyerLedgerListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/finance/me/` | api-finance-mine | `api.views.finance.BuyerFinanceSummaryView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/health/` | api-health | `api.views.health.HealthView` | AllowAny | (settings default) | — |
| GET | `/api/v1/me/` | api-me | `api.views.me.MeView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/me/dashboard/` | api-me-dashboard | `api.views.me.MeDashboardView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/anomalies/ciro/` | api-ops-anomalies-ciro | `api.views.reports.CiroAnomaliView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/finance/` | api-ops-finance | `api.views.ops_finance.OpsFinanceSummaryView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/finance/cari/` | api-ops-finance-cari | `api.views.ops_finance.OpsFinanceCariListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/finance/ledger/` | api-ops-finance-ledger | `api.views.ops_finance.OpsFinanceLedgerListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/finance/payments/` | api-ops-finance-payments | `api.views.ops_finance.OpsFinancePaymentListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/ops/inspections/` | api-ops-inspection-list | `api.views.ops_qc.OpsInspectionListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/inspections/<int:pk>/` | api-ops-inspection-detail | `api.views.ops_qc.OpsInspectionDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/inspections/<int:pk>/cancel/` | api-ops-inspection-cancel | `api.views.ops_qc.OpsInspectionCancelView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/inspections/<int:pk>/fail/` | api-ops-inspection-fail | `api.views.ops_qc.OpsInspectionFailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/inspections/<int:pk>/measurements/` | api-ops-inspection-measurement | `api.views.ops_qc.OpsInspectionMeasurementCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/inspections/<int:pk>/pass/` | api-ops-inspection-pass | `api.views.ops_qc.OpsInspectionPassView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/inspections/<int:pk>/start/` | api-ops-inspection-start | `api.views.ops_qc.OpsInspectionStartView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/orders/summary/` | api-ops-orders-summary | `api.views.ops.OpsOrderSummaryView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/ops/shipments/` | api-ops-shipment-list | `api.views.ops_shipment.OpsShipmentListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/ops/shipments/<int:pk>/` | api-ops-shipment-detail | `api.views.ops_shipment.OpsShipmentDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/shipments/<int:pk>/cancel/` | api-ops-shipment-cancel | `api.views.ops_shipment.OpsShipmentCancelView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/shipments/<int:pk>/deliver/` | api-ops-shipment-deliver | `api.views.ops_shipment.OpsShipmentDeliverView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/shipments/<int:pk>/dispatch/` | api-ops-shipment-dispatch | `api.views.ops_shipment.OpsShipmentDispatchView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/shipments/<int:pk>/pod/` | api-ops-shipment-pod | `api.views.ops_shipment.OpsShipmentPodCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/ops/shipments/<int:pk>/prepare/` | api-ops-shipment-prepare | `api.views.ops_shipment.OpsShipmentPrepareView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/orders/` | api-order-list | `api.views.order.OrderListView` | IsBuyerCommerceRead | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/orders/<int:pk>/` | api-order-detail | `api.views.order.OrderDetailView` | HasOrderObjectAccess | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/orders/<int:pk>/cancel/` | api-order-cancel | `api.views.buyer_order.OrderCancelView` | IsBuyerCommerceWrite,HasOrderObjectAccess | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/orders/<int:pk>/reorder/` | api-order-reorder | `api.views.buyer_order.OrderReorderView` | IsBuyerCommerceWrite,HasOrderObjectAccess | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/orders/from-checkout/` | api-order-from-checkout | `api.views.buyer_order.OrderFromCheckoutView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/org-units/` | api-org-list | `api.views.org.OrgUnitListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/org-units/<int:pk>/` | api-org-detail | `api.views.org.OrgUnitDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/org-units/<int:pk>/members/` | api-org-members | `api.views.org.OrgMemberListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/payments/intents/` | api-payment-intent-create | `api.views.payment.PaymentIntentCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/payments/webhook/` | api-payment-webhook | `api.views.payment_webhook.PaymentWebhookView` | AllowAny | (settings default) | — |
| POST | `/api/v1/price-locks/` | api-price-lock-create | `api.views.buyer_lock.PriceLockCreateView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/price-locks/<int:pk>/` | api-price-lock-detail | `api.views.buyer_lock.PriceLockDetailView` | IsBuyerCommerceRead | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/quotes/` | api-quote-create | `api.views.buyer_quote.QuoteCreateView` | IsBuyerCommerceWrite | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/quotes/<int:pk>/` | api-quote-detail | `api.views.buyer_quote.QuoteDetailView` | HasQuoteObjectAccess | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/reports/buyer-behavior/` | api-reports-buyer-behavior | `api.views.reports.AliciDavranisOzetView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/reports/orders/` | api-reports-orders | `api.views.reports.TicariSiparisOzetView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/returns/` | api-return-list | `api.views.returns.ReturnListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/returns/<int:pk>/` | api-return-detail | `api.views.returns.ReturnDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/returns/<int:pk>/approve/` | api-return-approve | `api.views.returns.ReturnApproveView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/returns/<int:pk>/cancel/` | api-return-cancel | `api.views.returns.ReturnCancelView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/returns/<int:pk>/mahsup/` | api-return-mahsup | `api.views.returns.ReturnMahsupView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/returns/<int:pk>/reject/` | api-return-reject | `api.views.returns.ReturnRejectView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/returns/<int:pk>/submit/` | api-return-submit | `api.views.returns.ReturnSubmitView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET,POST | `/api/v1/rfqs/` | api-rfq-list | `api.views.rfq.RfqListCreateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/rfqs/<int:pk>/` | api-rfq-detail | `api.views.rfq.RfqDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/rfqs/<int:pk>/messages/` | api-rfq-message | `api.views.rfq.RfqMessageView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/rfqs/<int:pk>/revisions/` | api-rfq-revision | `api.views.rfq.RfqRevisionView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/rfqs/<int:pk>/send/` | api-rfq-send | `api.views.rfq.RfqSendView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/schema/` | api-schema | `api.schema_views.EnrichedOpenAPISchemaView` | IsAuthenticated | (settings default) | — |
| GET | `/api/v1/shipments/` | api-shipment-list | `api.views.shipment.ShipmentListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/shipments/<int:pk>/` | api-shipment-detail | `api.views.shipment.ShipmentDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/supplier/offers/` | api-supplier-offers | `api.views.supplier.SupplierOfferListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/supplier/offers/<int:pk>/` | api-supplier-offer-detail | `api.views.supplier.SupplierOfferDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/offers/<int:pk>/deactivate/` | api-supplier-offer-deactivate | `api.views.supplier.SupplierOfferDeactivateView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/offers/<int:pk>/submit/` | api-supplier-offer-submit | `api.views.supplier.SupplierOfferSubmitView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/offers/<int:pk>/versions/` | api-supplier-offer-versions | `api.views.supplier.SupplierOfferVersionView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/supplier/rfqs/` | api-supplier-rfq-list | `api.views.supplier.SupplierRfqListView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/supplier/rfqs/<int:pk>/` | api-supplier-rfq-detail | `api.views.supplier.SupplierRfqDetailView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/rfqs/<int:pk>/messages/` | api-supplier-rfq-message | `api.views.supplier.SupplierRfqMessageView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/rfqs/<int:pk>/revisions/` | api-supplier-rfq-revision | `api.views.supplier.SupplierRfqRevisionView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| GET | `/api/v1/supplier/stock/` | api-supplier-stock | `api.views.supplier.SupplierStockSummaryView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |
| POST | `/api/v1/supplier/stock/adjustments/` | api-supplier-stock-adjust | `api.views.supplier.SupplierStockAdjustView` | IsAuthenticatedWithFirma | SessionAuthentication,ExpiringTokenAuthentication,BasicAuthentication | — |

## 0.4 OpenAPI operations

| Metot | Yol | operationId | tags | requestBody | response codes |
|-------|-----|-------------|------|-------------|----------------|
| POST | `/api/v1/act-as/start/` | createActAsStart | act-as | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/act-as/stop/` | createActAsStop | act-as | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/approvals/` | listApprovalListCreates | approvals | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/approvals/` | createApprovalList | approvals | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/approvals/{id}/` | retrieveApprovalDetail | approvals | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/approvals/{id}/approve/` | approveApproval | approvals | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/approvals/{id}/reject/` | rejectApproval | approvals | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/approvals/{id}/submit/` | submitApproval | approvals | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/auth/csrf/` | listAuthCsrves | auth | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/auth/email-verify/` | createEmailVerifyRequest | auth | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/auth/email-verify/confirm/` | createEmailVerifyConfirm | auth | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/auth/invites/` | listInvites | auth | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/auth/invites/accept/` | createInviteAccept | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/invites/create/` | createInvite | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/login/` | createAuthLogin | auth | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/auth/logout/` | createAuthLogout | auth | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/auth/mfa/resend/` | createMfaResend | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/mfa/verify/` | createMfaVerify | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/password-change/` | createPasswordChange | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/password-reset/` | createPasswordResetRequest | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/auth/password-reset/confirm/` | createPasswordResetConfirm | auth | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/bulk-orders/` | createBulkOrder | bulk-orders | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/carts/me/` | listCartMines | carts | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/carts/me/lines/` | createCartLine | carts | yes | 201,400,401,403,404,409,429 |
| DELETE | `/api/v1/carts/me/lines/{line_id}/` | destroyCartLineDetail | carts | yes | 200,400,401,403,404,409,429 |
| PATCH | `/api/v1/carts/me/lines/{line_id}/` | partialUpdateCartLineDetail | carts | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/carts/{id}/` | retrieveCartDetail | carts | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/catalog/` | listBuyerCatalogs | catalog | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/catalog/{id}/` | retrieveBuyerCatalogDetail | catalog | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/checkouts/` | createCheckout | checkouts | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/credit/check/` | createCreditCheck | credit | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/credit/me/` | listCreditMines | credit | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/finance/cari/` | listBuyerCaris | finance | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/finance/cari/{id}/` | retrieveBuyerCariDetail | finance | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/finance/ledger/` | listBuyerLedgers | finance | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/finance/me/` | listBuyerFinanceSummaries | finance | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/health/` | listHealths | health | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/me/` | listMes | me | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/me/dashboard/` | listMeDashboards | me | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/anomalies/ciro/` | listCiroAnomalis | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/finance/` | listOpsFinanceSummaries | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/finance/cari/` | listOpsFinanceCaris | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/finance/ledger/` | listOpsFinanceLedgers | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/finance/payments/` | listOpsFinancePayments | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/inspections/` | listOpsInspectionListCreates | ops | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/` | createOpsInspectionList | ops | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/ops/inspections/{id}/` | retrieveOpsInspectionDetail | ops | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/{id}/cancel/` | cancelOpsInspection | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/{id}/fail/` | failOpsInspection | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/{id}/measurements/` | createOpsInspectionMeasurement | ops | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/{id}/pass/` | passOpsInspection | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/inspections/{id}/start/` | startOpsInspection | ops | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/orders/summary/` | listOpsOrderSummaries | ops | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/ops/shipments/` | listOpsShipmentListCreates | ops | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/` | createOpsShipmentList | ops | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/ops/shipments/{id}/` | retrieveOpsShipmentDetail | ops | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/{id}/cancel/` | cancelOpsShipment | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/{id}/deliver/` | deliverOpsShipment | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/{id}/dispatch/` | dispatchOpsShipment | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/{id}/pod/` | createOpsShipmentPod | ops | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/ops/shipments/{id}/prepare/` | prepareOpsShipment | ops | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/orders/` | listOrders | orders | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/orders/from-checkout/` | createOrderFromCheckout | orders | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/orders/{id}/` | retrieveOrderDetail | orders | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/orders/{id}/cancel/` | createOrderCancel | orders | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/orders/{id}/reorder/` | createOrderReorder | orders | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/org-units/` | listOrgUnitListCreates | org-units | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/org-units/` | createOrgUnitList | org-units | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/org-units/{id}/` | retrieveOrgUnitDetail | org-units | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/org-units/{id}/members/` | listOrgMemberListCreates | org-units | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/org-units/{id}/members/` | createOrgMemberList | org-units | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/payments/intents/` | createPaymentIntent | payments | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/payments/webhook/` | createPaymentWebhook | payments | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/price-locks/` | createPriceLock | price-locks | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/price-locks/{id}/` | retrievePriceLockDetail | price-locks | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/quotes/` | createQuote | quotes | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/quotes/{id}/` | retrieveQuoteDetail | quotes | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/reports/buyer-behavior/` | listAliciDavranisOzets | reports | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/reports/orders/` | listTicariSiparisOzets | reports | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/returns/` | listReturnListCreates | returns | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/` | createReturnList | returns | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/returns/{id}/` | retrieveReturnDetail | returns | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/{id}/approve/` | approveReturn | returns | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/{id}/cancel/` | cancelReturn | returns | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/{id}/mahsup/` | createReturnMahsup | returns | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/{id}/reject/` | rejectReturn | returns | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/returns/{id}/submit/` | submitReviewReturnSubmit | returns | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/rfqs/` | listRfqListCreates | rfqs | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/rfqs/` | createRfqList | rfqs | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/rfqs/{id}/` | retrieveRfqDetail | rfqs | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/rfqs/{id}/messages/` | createRfqMessage | rfqs | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/rfqs/{id}/revisions/` | createRfqRevision | rfqs | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/rfqs/{id}/send/` | createRfqSend | rfqs | yes | 200,400,401,403,404,409,429 |
| GET | `/api/v1/shipments/` | listShipments | shipments | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/shipments/{id}/` | retrieveShipmentDetail | shipments | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/supplier/offers/` | listSupplierOffers | supplier | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/supplier/offers/{id}/` | retrieveSupplierOfferDetail | supplier | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/offers/{id}/deactivate/` | createSupplierOfferDeactivate | supplier | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/offers/{id}/submit/` | createSupplierOfferSubmit | supplier | yes | 200,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/offers/{id}/versions/` | createSupplierOfferVersion | supplier | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/supplier/rfqs/` | listSupplierRfqs | supplier | no | 200,400,401,403,404,409,429 |
| GET | `/api/v1/supplier/rfqs/{id}/` | retrieveSupplierRfqDetail | supplier | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/rfqs/{id}/messages/` | createSupplierRfqMessage | supplier | yes | 201,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/rfqs/{id}/revisions/` | createSupplierRfqRevision | supplier | yes | 201,400,401,403,404,409,429 |
| GET | `/api/v1/supplier/stock/` | listSupplierStockSummaries | supplier | no | 200,400,401,403,404,409,429 |
| POST | `/api/v1/supplier/stock/adjustments/` | createSupplierStockAdjust | supplier | yes | 201,400,401,403,404,409,429 |

## 0.5 Auth notu (global)

DRF varsayılanı `settings.REST_FRAMEWORK` — tipik: Session + Token; `IsAuthenticated` veya view-özel.
Anonim: `health`, `auth/csrf`, `auth/login`, password-reset, invite accept, email-verify confirm, payments/webhook (özel).
Kanıt: view dosyaları `backend/config/api/views/*.py`.

