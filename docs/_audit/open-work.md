# Open Work (ADIM 4) — 2026-11-11 sonrası

## Kod tarama (tests/migrations hariç)

| Öncelik | Bulgu | Durum |
|---------|-------|--------|
| — | TODO/FIXME/HACK/XXX / NotImplementedError | **Yok** (rg) |
| — | `api/views` içinde çıplak `pass` | **Yok** |
| — | Bare `except:` | **Yok** |
| — | APIView `permission_classes` eksik | **Yok** (örneklenen view’larda var) |

## Bilinçli stub (dokunulmaz)

FakeERP / FakeCRM / punchout ack / FakePayment / FakeCarrier — F7/F5/F6 iskelet.

## P2 (açık, düzeltme bu turda yok)

| Öncelik | Konu | Not |
|---------|------|-----|
| P2 | Meta `/api/schema|docs|redoc` OpenAPI paths dışı | Bilinçli |
| P2 | Admin `/act-as/` redirect OpenAPI dışı | API eşleniği var |
| P2 | FE-SUITE dışında Next portal dilimleri | MASTER §12.3 |
| P2 | Staging Sentry event | DOĞRULANAMADI |
| P2 | Celery/Redis, gerçek ödeme/kargo | Bilinçli erteli |
| P2 | Teklif create / RFQ eşleştirme HTTP | FE v1 dışı (ADIM 7) |
