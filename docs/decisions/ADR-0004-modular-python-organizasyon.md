# ADR-0004 — Modüler Python Dosya Organizasyonu

**Durum:** Kabul edildi  
**Tarih:** 2026-11-08  
**Onaylayan:** Proje sahibi  
**Bağlam:** Faz 0 tamam; Faz 1 uygulama standardı. Ayrı talimat olmadan mevcut WIP topluca yeniden düzenlenmez.

## Karar

Kuyumbank projesinde modeller, view'lar, serializer'lar, admin sınıfları, servisler, selector'lar ve testler sorumluluklarına göre ayrı Python dosyalarında tutulacaktır.

### 1. Model organizasyonu

- Her ana model ayrı bir Python dosyasında tanımlanır.
- Modeller `models/` paketi altında tutulur.
- `models/__init__.py` dışa aktarımları yönetir.
- Birbiriyle doğrudan ilişkili küçük yardımcı sınıflar, gerekçesi belgelenerek aynı dosyada bulunabilir.

### 2. View organizasyonu

- View sınıfları ve fonksiyonları sorumluluklarına göre ayrı dosyalara ayrılır.
- HTTP işlemleri dışında iş mantığı view içine yerleştirilmez.
- URL yapılandırması merkezi `urls.py` üzerinden ilgili view dosyalarına bağlanır.

### 3. Diğer katmanlar

- `services/`: İş kuralları ve yazma işlemleri.
- `selectors/`: Okuma ve veri sorgulama işlemleri.
- `serializers/`: API veri doğrulama ve dönüşüm.
- `admin/`: Django Admin yapılandırmaları.
- `tests/`: Testler, konu ve sorumluluğa göre ayrı dosyalar.

### 4. Bağlayıcı kurallar

- Yeni kod mevcut dosyalara yalnızca dosyanın sorumluluğuyla uyumluysa eklenebilir.
- Büyük ve birden fazla sorumluluk taşıyan dosyalar uygun paketlere ayrılır.
- Gereksiz küçük dosyalar oluşturulmaz.
- Circular import oluşturulmaz.
- Django model keşfi, migration sistemi, admin keşfi ve test keşfi korunur.
- Dosya taşıma ve yeniden düzenleme işlemlerinde import yolları ve geriye dönük uyumluluk kontrol edilir.
- Agent, yalnızca biçimsel gerekçeyle mevcut kodu topluca yeniden düzenlemez.

### 5. AI agent yükümlülüğü

Yeni modül ve kod geliştirmelerinde bu organizasyon standardı zorunludur. Her fazda değiştirilen dosyalar ve sorumlulukları raporlanır.

## Hedef paket iskeleti (örnek: `urunler`)

```text
urunler/
├── models/
│   ├── __init__.py
│   ├── kategori.py
│   ├── urun.py
│   ├── urun_varyant.py
│   ├── urun_medya.py
│   └── tedarikci_urun.py
│
├── views/
│   ├── __init__.py
│   ├── kategori_views.py
│   ├── urun_views.py
│   └── varyant_views.py
│
├── services/
│   ├── __init__.py
│   ├── urun_service.py
│   └── varyant_service.py
│
├── selectors/
│   ├── __init__.py
│   └── urun_selectors.py
│
├── admin/
│   ├── __init__.py
│   ├── urun_admin.py
│   └── kategori_admin.py
│
├── serializers/
│   ├── __init__.py
│   └── urun_serializer.py
│
├── tests/
│   ├── __init__.py
│   ├── test_urun.py
│   ├── test_varyant.py
│   └── test_tenant_isolation.py
│
├── urls.py
└── apps.py
```

Aynı desen `firmalar`, `tanimlar`, `fiyatlama` ve sonraki app’ler için geçerlidir. App’te henüz API yoksa `views/`, `serializers/`, `urls.py` oluşturulmaz (gereksiz dosya yasağı).

## Mevcut kod / WIP

- Birçok app zaten `models/`, `admin/`, `services/` paketlerine yakın.
- **Onaysız toplu refactor yok.** Faz 1’de yalnızca dokunulan yüzey ADR-0004’e uyar; geniş taşıma ayrı talimat ister.
- Taşıma yapılırsa: import yolları, `AppConfig`, admin register, migration tarihçesi ve test keşfi doğrulanır.

## Sonuçlar

- İş mantığı `services/`; okuma sorguları `selectors/`; HTTP ince kalır.
- Tenant scope okumaları tercihen selector’da; yazma kuralları service’te (ADR-0003 ile uyum).
- Faz raporu: değişen dosya + sorumluluk listesi zorunlu.

## İlişkili

- [`AGENTS.md`](../../AGENTS.md)
- [`.cursor/skills/django-engineering/SKILL.md`](../../.cursor/skills/django-engineering/SKILL.md)
- [`ADR-0003`](ADR-0003-faz1-kimlik-rbac.md) (kimlik/RBAC; bu ADR yapısal iskelet)
