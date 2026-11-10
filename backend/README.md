# Kuyumbank backend

Django **6.1.2** modular monolith. Proje paketi: `config/` · `manage.py` bu dizinde.

## Dokümantasyon

| Bilgi | Dosya |
|-------|--------|
| Agent kuralları | [`../AGENTS.md`](../AGENTS.md) |
| Kanonik ürün/teknik durum | [`../docs/KUYUMBANK_MASTER.md`](../docs/KUYUMBANK_MASTER.md) (§2, §12) |
| Repo özeti | [`../README.md`](../README.md) |

## Gereksinimler

- Python 3.12–3.14 (geliştirme: 3.14.x)
- PostgreSQL
- Bağımlılıklar: [`config/requirements.txt`](config/requirements.txt) (DRF var; Celery **yok**)

## Ortam kurulumu

Tek sanal ortam yolu: **`backend/.venv`** (bu dizinde). `config/` altında `.venv` oluşturma.

```powershell
# repo kökünden
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r config\requirements.txt
```

IDE: workspace `.vscode/settings.json` interpreter’ı `backend/.venv` olarak sabitler.  
Aynı klasörde ikinci bir venv açma (`config/.venv` vb.).

## Kurulum

```powershell
cd backend
.\.venv\Scripts\Activate.ps1   # yoksa yukarıdaki Ortam kurulumu
cd config
copy .env.example .env
# .env zorunlu: SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD
# isteğe bağlı: DB_HOST (localhost), DB_PORT (5432), DEBUG, ALLOWED_HOSTS
python manage.py migrate
python manage.py seed_role_permissions
python manage.py bootstrap_platform
python manage.py seed_tanimlar
python manage.py createsuperuser
python manage.py runserver
```

Opsiyonel: `audit_user_assignments`, `seed_fiyat_gruplari`, `seed_urunler`.  
Admin: http://127.0.0.1:8000/admin/ · API: http://127.0.0.1:8000/api/v1/health/

## Kontroller ve testler

```powershell
cd backend\config
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test firmalar.tests urunler.tests fiyatlama.tests tanimlar.tests stok.tests siparis.tests api.tests --verbosity=1
```

PostgreSQL kullan (varsayılan settings). Constraint/`select_for_update` testlerini SQLite ile doğrulanmış sayma.  
Çıplak `manage.py test fiyatlama` yerine `*.tests` paketleri tercih et.  
Güncel sayı: master **§12**.

## Uygulamalar (kodda mevcut)

| App | Sorumluluk | Durum (özet) |
|-----|------------|--------------|
| `firmalar` | Firma, kullanıcı, RBAC, `AuditOlay` | UYGULANDI |
| `tanimlar` | Metal, kur, kanal, PB dönüşüm | UYGULANDI |
| `urunler` | Katalog, eşleştirme, onay | UYGULANDI |
| `fiyatlama` | Teklif, sözleşme, quote, PriceLock | UYGULANDI |
| `stok` | Warehouse, Movement, Balance, Reservation | UYGULANDI (F4 dilim 1–3) |
| `siparis` | Cart, Checkout, Order (+ iptal/IADE/reorder) | UYGULANDI (F4 dilim 4–8) |
| `api` | İnce PRE `/api/v1/` (health/me/cart/order/schema) | UYGULANDI (PRE-001…004) |

Faz / sıradaki iş: master **§12**.
