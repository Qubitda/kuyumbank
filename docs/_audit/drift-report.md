# Drift Report (ADIM 1)

**Tarih:** 2026-11-11  
**Kural:** şüphede kod + OpenAPI kazanır (`API_CONTRACT` §üst).  
**Sonra (ADIM 2–3):** HTML miras / path sayısı dökümanlarda düzeltildi; auth password/MFA OpenAPI bağları eklendi. Aşağıdaki §c satırları **önce** bulgularıdır (tarihsel).

## a) Dökümanda/OpenAPI var, kodda yok (eksik implementasyon)

_OpenAPI operation’larının tamamı Django norm path setinde (normalize sonrası)._

## b) Kodda var, OpenAPI/dökümanda yok (dökümansız)

| Metot | Path (Django norm) | Not |
|-------|--------------------|-----|
| GET | `/api/docs/` | Route var; OpenAPI paths’te yok veya path normalize farkı |
| GET | `/api/redoc/` | Route var; OpenAPI paths’te yok veya path normalize farkı |
| GET | `/api/schema/` | Route var; OpenAPI paths’te yok veya path normalize farkı |
| GET | `/api/v1/schema/` | Route var; OpenAPI paths’te yok veya path normalize farkı |

## c) İkisinde de var ama farklı / bayat döküman iddiaları

| Döküman kanıtı | İddia | Kod gerçeği |
|----------------|-------|-------------|
| docs/API_CONTRACT.md:112 | F9 Django HTML miras (`/buyer/`) korunur | ADR-0029 + config/urls.py — /buyer|/supplier|/ops HTML yok |
| docs/MASTER.md (match /buyer/) | HTML path /buyer/ UYGULANDI tablosunda | ADR-0029 HTML kaldırıldı; test/view dosyaları kontrol edilmeli |
| docs/MASTER.md (match /buyer/finance/) | HTML path /buyer/finance/ UYGULANDI tablosunda | ADR-0029 HTML kaldırıldı; test/view dosyaları kontrol edilmeli |
| docs/MASTER.md (match /buyer/approvals/) | HTML path /buyer/approvals/ UYGULANDI tablosunda | ADR-0029 HTML kaldırıldı; test/view dosyaları kontrol edilmeli |
| docs/MASTER.md (match /buyer/rfq/) | HTML path /buyer/rfq/ UYGULANDI tablosunda | ADR-0029 HTML kaldırıldı; test/view dosyaları kontrol edilmeli |
| docs/API_CONTRACT.md:89 | OpenAPI paths **81** | Gerçek openapi-v1.json path sayısı **98** |

## HTML portal dosya kanıtı (ADR-0029)

| Glob | Bulunan |
|------|---------|
| siparis *buyer* | 9 → ['siparis\\services\\buyer_dashboard_servisi.py', 'siparis\\__pycache__\\urls_buyer.cpython-314.pyc', 'siparis\\views\\__pycache__\\buyer_catalog_ui.cpython-314.pyc', 'siparis\\views\\__pycache__\\buyer_rfq_ui.cpython-314.pyc', 'siparis\\views\\__pycache__\\buyer_ui.cpython-314.pyc', 'siparis\\tests\\__pycache__\\test_buyer_catalog_f9_011.cpython-314.pyc', 'siparis\\tests\\__pycache__\\test_buyer_dashboard_f9_010.cpython-314.pyc', 'siparis\\tests\\__pycache__\\test_buyer_ui_f4_062.cpython-314.pyc'] |
| *finance_ui* | 3 → ['backend\\config\\finans\\views\\__pycache__\\buyer_finance_ui.cpython-314.pyc', 'backend\\config\\finans\\views\\__pycache__\\ops_finance_ui.cpython-314.pyc', 'backend\\config\\finans\\tests\\__pycache__\\test_finance_ui_f5_032.cpython-314.pyc'] |
| *approval_ui* | 2 |
| *rfq_ui* | 2 |

## Normalize farkları (bilinçli)

- Django: `/api/v1/schema/` + `/api/schema/` (çift mount)
- Django: `/api/docs/`, `/api/redoc/` (OpenAPI UI; ops listesinde olmayabilir)
- Django: `/act-as/start/<user_id>/`, `/act-as/stop/` (Admin redirect; API: `/api/v1/act-as/*`)
- OpenAPI path param: `{id}` vs Django `<int:pk>`

