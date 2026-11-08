# Kuyumbank — Agent Talimatı

Bu dosya proje genelinde bağlayıcıdır. Teknik doğruluk ve veri güvenliği, hızdan önce gelir.
Proje bağlamını burada tekrar etme; kanonik durum için master’a git.

## Proje (kısa)

Jewelry B2B platform. Django modular monolith. Alıcı–tedarikçi **kör havuz**; fiyat **snapshot/kilit**; stok **ledger + rezervasyon**; `siparis` **Cart → Checkout → Order** (+ iptal/IADE).

## İlk okuma sırası

1. Bu `AGENTS.md`
2. `docs/KUYUMBANK_MASTER.md` — özellikle **§2** (gerçek durum) ve **§12** (sıradaki adım)
3. Görevle ilgili **tek** skill (aşağıdaki tablo)
4. İlgili mevcut kod (model/servis/test) — yeniden yazmadan önce

Kurulum komutları: kök `README.md` → `backend/README.md`.

## Bilgi kaynakları (tek sahiplik)

| Bilgi | Tek kaynak |
|-------|------------|
| Agent kuralları / yasaklar / süreç | **Bu dosya** |
| Vizyon, mimari, ADR, faz, backlog, U-*, risk, §12 | **`docs/KUYUMBANK_MASTER.md`** |
| Kurulum / migrate / test / run | **`README.md` + `backend/README.md`** |
| Framework API | Django 6.1 docs / kaynak |
| İş/mimari skill | `.cursor/skills/*` (Django resmi skill değil) |

`docs/` = yalnız `KUYUMBANK_MASTER.md`. Yeni faz raporu, ikinci yol haritası, dağınık backlog veya ayrı `ADR-*.md` **üretilmez**. Cursor indeksindeki silinmiş dosya adı kanıt sayılmaz (diskte `Test-Path` / `ls`).

## Hedef runtime

- Python: 3.12–3.14 (geliştirme: 3.14.6)
- Django: **6.1.x** (pin: 6.1.2)
- DB: PostgreSQL (`backend/config/requirements.txt`)
- `manage.py`: `backend/config/`

## Django docs vs proje skill’leri

- Django docs/kaynak = framework kullanımı için normatif.
- `.cursor/skills/` = yalnız Kuyumbank kuralları; Django docs yerine geçmez.

## Görev yürütme protokolü (token tasarrufu)

1. Master §2 / §10 / §11 / §12 + ilgili ADR satırına bak.
2. Yalnız görev dosyalarını oku; tüm repoyu yeniden tarama.
3. Kabul edilmiş ADR’yi yeniden tartışma; Taslak’ı kendi kendine Kabul etme.
4. Analiz yeterliyse kodla; bitince master’ı güncelle (kod + test + docs birlikte).
5. Odak test → (dilim kapanışında) suite bir kez. PG kısıtını SQLite ile “geçti” sayma.
6. Üretim `migrate` / secret / yıkıcı git **kullanıcı onayı olmadan yok**.
7. Rapor: Tamamlananlar / Testler / Riskler / Sonraki faz (+ değişen dosyalar).

## Skill yükleme (görev başına bir)

| Görev | Skill |
|-------|--------|
| Model, ORM, servis, migration, admin | `.cursor/skills/django-engineering/SKILL.md` |
| Tenant, RBAC, kör havuz, API yetki | `.cursor/skills/multi-tenant-security/SKILL.md` |
| Katalog, teklif, fiyat, stok, sipariş kuralları | `.cursor/skills/business-domain/SKILL.md` |
| Test yazma / çalıştırma | `.cursor/skills/testing-quality/SKILL.md` |

## Faz sırası (bağlayıcı)

Kod: master §6’da ilgili ADR **Kabul** + açık talimat olmadan o fazın uygulaması başlamaz.

1. Faz 0 — standartlar (tarihsel)
2. Faz 1 — firma, kullanıcı, RBAC, izolasyon
3. Faz 2 — katalog
4. Faz 3 — teklif / fiyatlama / quote / PriceLock (3a–3b uygulandı; ADR-0010 **Kabul**)
5. Faz 4 — stok ledger → rezervasyon → cart → checkout/lock → order+iptal (ADR-0011 **Kabul**; dilim 1–7 uygulandı: WH…Order+IADE)
6. Faz 5+ — finans, QC, API, ops, portal — master §9–§10

Canlı durum: master **§2** + **§12** (YAPILDI / SIRADA). Suite **348 OK**. Sıradaki: PRE-005 → F4-081. Finans ADR-0012 **Taslak**.

## Temel iş kuralları

- Kullanıcı tek firmaya bağlı; platform firması tekil.
- Firma verisi tenant-scoped; client `firma_id` / `tedarikci_id` güvenilmez.
- Kör havuz: alıcı↔tedarikçi kimlik/maliyet sızıntısı yok.
- Katalog platform; teklif tedarikçi; alıcı fiyatı quote.
- Fiyat: Decimal; siparişte snapshot zorunlu (`OrderLine` + L-11 `price_lock`).
- Stok: Movement (immutable) ≠ Balance (projeksiyon) ≠ Reservation (TTL hold); sipariş tüketimi SATIS, iptal IADE.
- Kritik işlem audit; fail audit `domain_atomic` dışında durable.
- Alanın modelde olması kuralın uygulandığı anlamına gelmez.

## Teknik standartlar

- Django public API; domain logic serviste (ADR-0004 paketleri).
- `transaction.atomic` / stok-finans: `select_for_update` + DB constraint.
- Decimal; secret koda/log’a yazılmaz.
- Onaysız toplu refactor / ölü soyutlama yok.

## Test ve migration

- Yeni özellik: model + service + (varsa) API + yetki + tenant + sınır test; concurrency → PG.
- Çalıştırılmayan test başarılı gösterilmez.
- `makemigrations` üretilebilir; **üretim migrate kullanıcı onayı**.
- Migration’ı oku; veri kaybı riskini açıkla.

## Ek kural A — Kanıt etiketleri

- **DOĞRULANDI** — dosya/satır veya komut çıktısı
- **DOĞRULANAMADI** — ortam/erişim yok
- **PLANLAMA BULGUSU** — mimari; runtime yok

## Ek kural C — Fayda/maliyet

Önce işlev + güvenlik + ticari doğruluk; sonra odaklı test; gereksiz mükemmelleştirme yok. P0 güvenlik/finans derhal; P2 kaydet-akışı-kesme.

## Yasaklar

- `.env` / secret çıktıya yazma
- İzinsiz üretim DB / migrate / DB silme
- `git reset --hard` / force push / kullanıcı değişikliklerini ezme
- Uygulanmamış özelliği UYGULANDI yazma
- Kabul ADR’yi ajanın Kabul etmesi

## Belirsizlik

Net gereksinim → uygula. Eksik detay → güvenli varsayım + master §6 **Taslak** ADR. Veri kaybı / finans / güvenlik / geri dönülemez mimari → dur, karar iste.
