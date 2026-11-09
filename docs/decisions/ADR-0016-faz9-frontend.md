# ADR-0016 — Faz 9 frontend teknolojisi (F9-001)

**Durum:** **Taslak** (ürün sahibi Kabul’ü bekleniyor — agent Kabul etmez)
**Bağımlılık:** PRE/F7 API UYGULANDI; F4-062 `/buyer/` minimal UI UYGULANDI; ADR-0002/0004 **Kabul**
**Kod:** Bu ADR **Kabul** + açık talimat olmadan F9-010… portal kodu başlamaz

> F9-001 kartı. Amaç: alıcı/tedarikçi portal deneyiminin teknoloji seçimi; kör havuz ve tenant kuralları bozulmaz.

## Bağlam (kod gerçeği)

- Mevcut HTTP: Django admin + ince DRF `/api/v1/` + session `/buyer/` (sepet/sipariş/finans/onay/RFQ) + `/ops/finance/`.
- Next.js / SPA paketleri `requirements` / repo kökünde **yok** (bilinçli).
- Celery/Redis yok; auth Token + Session + Basic.

## Seçenekler

| ID | Seçenek | Artı | Eksi |
|----|---------|------|------|
| **A** | **Django template portal** — `/buyer/`, `/supplier/` büyütülür; aynı servis/selector | Hızlı; CSRF/session hazır; RBAC aynı; ek runtime yok | SPA UX / PWA sınırlı; zengin bileşen maliyeti |
| **B** | **Next.js (App Router) SPA** — yalnız `/api/v1/` tüketir | Modern UX; ayrı deploy | Yeni stack; CORS/auth; çift yüzey riski; F9 öncesi maliyet |
| **C** | **Hibrit** — v1 = A; v2 = B (API kontratı F7 sabiti) | Erken değer + ileride SPA | İki yüzey geçici borç |

## Öneri (Taslak — bağlayıcı değil)

**C → önce A:** F9-010…015’i Django template ile kapat; API kontratını F7’de sertleştir; Next.js ayrı ADR/dilim (ürün talebi + kapasite).

Gerekçe: `/buyer/` zaten F4/F5/F10 UI taşıyor; Prosperer parity henüz runtime DOĞRULANAMADI; erken Next.js, F8 kalanları (Sentry/perf) ve F10-022’den önce risk/maliyet yüksek.

## Kabul kararları (ürün sahibi doldurur)

| ID | Soru | Karar (boş = bekliyor) |
|----|------|------------------------|
| FE-1 | v1 portal yüzeyi? | A / B / C |
| FE-2 | Supplier portal yolu? | `/supplier/` Django / Next route / ertelenir |
| FE-3 | Auth | Session (Django) / Token-only SPA / ikisi |
| FE-4 | PWA (F9-016) | v1 zorunlu / sonra |
| FE-5 | Design system | Minimal mevcut CSS / ayrı paket |

## Kapsam dışı

- Celery; gerçek ödeme/kargo UI
- Dynamic Pricing (U-015 kilitli)
- Bu ADR Kabul edilmeden Next.js iskeleti veya F9-010 kodu

## Uygulama sırası (Kabul sonrası)

1. Bu ADR **Kabul** (FE-1…FE-5 dolu)
2. F9-010 dashboard iskeleti (seçilen stack)
3. F9-011…015 dilimleri (kör havuz testleri zorunlu)
4. F9-016/017 P2

## İlişkili

- BACKLOG: F9-001…017  
- ROADMAP Faz 9; MASTER §12  
- Mevcut: `siparis.views.buyer_ui`, `buyer_rfq_ui`, `buyer_approval_ui`
