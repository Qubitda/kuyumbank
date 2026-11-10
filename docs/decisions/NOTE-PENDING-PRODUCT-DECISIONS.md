# NOTE — Bekleyen ürün / finans kararları (ADR-0019 dışı)

**Tarih:** 2026-11-10  
**Durum:** Açık — hiçbiri Kabul sayılmaz  
**Ayır:** Object-level DRF → yalnız [ADR-0019](ADR-0019-object-level-drf.md) OL-1…11

Bu dosyada FXQ / DYN / I18N / AI vardır. ADR-0019 onayını bekletmez; paralel veya sonra.

---

## FXQ — F12-011 TRY dışı yuvarlama (U-009)

| ID | Mevcut | Öneri | Etki | Seçim | Durum |
|----|--------|-------|------|-------|-------|
| FXQ-1 | Tüm PB `0.01` HALF_UP | A) Aynı kalsın · B) PB hassasiyet tablosu | B = fiyat motoru + test; mevcut snapshot dokunulmaz (FXQ-3) | | Bekliyor |
| FXQ-2 | Finans onayı şart (U-009) | Finans imzası zorunlu | Onaysız kod yok | Finans: ___ | Bekliyor |
| FXQ-3 | Kayıtlar immutable | A) Dokunulmaz · B) yeniden hesap | B yasak önerilir (ticari/audit) | | Bekliyor |

**Kapı:** FXQ-1+2 (+3) dolu → F12-011 kod talimatı.

---

## DYN — CAP-DYNPRICE (U-015)

| ID | Mevcut | Öneri | Etki | Seçim | Durum |
|----|--------|-------|------|-------|-------|
| DYN-1 | Kapalı (U-015) | A) Kapalı kal · B) yalnız **yeni** quote | B açılınca kural motoru | | Bekliyor |
| DYN-2 | Quote/Lock/OrderLine immutable | **A zorunlu** (değişmez) | Snapshot bütünlüğü | A | Bekliyor (onayla) |
| DYN-3 | — | DYN-1=B ise tetik listesi: kanal / hacim / süre | Kapsam netliği | | Bekliyor |

**Kapı:** DYN-1=A → kod yok. DYN-1=B + DYN-2=A + DYN-3 dolu → uygulama talimatı.

---

## I18N — F12-001

| ID | Mevcut | Öneri | Etki | Seçim | Durum |
|----|--------|-------|------|-------|-------|
| I18N-1 | Fiilen TR | A) TR · B) TR+EN UI · C) +katalog içerik | B/C = F12-010 kapsamı | | Bekliyor |
| I18N-2 | — | C) hibrit (BE mesaj / FE UI) | Mimari | | Bekliyor |
| I18N-3 | Katalog tek dil | A) çeviri zorunlu değil | P3 erteleme | | Bekliyor |
| I18N-4 | F12-010 bekler | A) F12-001 Kabul sonrası kod | Faz kilidi | | Bekliyor |

**Kapı:** I18N-1…4 → F12-001 ADR Kabul → F12-010.

---

## AI — F11-015

| ID | Mevcut | Öneri | Etki | Seçim | Durum |
|----|--------|-------|------|-------|-------|
| AI-1 | Yok (F10-021 kural skor var) | A) Yok · B) öneri+insan onayı · C) otomatik | C yasak önerilir | | Bekliyor |
| AI-2 | Kör havuz zorunlu | **A** (sızıntı yok) | Güvenlik | A | Bekliyor (onayla) |
| AI-3 | — | A) yerel skor genişlet · B) dış LLM | Veri politikası | | Bekliyor |
| AI-4 | — | A) otomatik checkout/onay yasak | Ticari risk | | Bekliyor |

**Kapı:** AI-1≠C; AI-2=A; AI-4=A → tasarım/kod talimatı.

---

## Onay sırası (öneri)

1. ADR-0019 OL-1…11  
2. FXQ  
3. DYN  
4. I18N / AI
