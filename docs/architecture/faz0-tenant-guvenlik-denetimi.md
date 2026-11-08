# Faz 0 — Tenant / yetki güvenlik denetimi (derin)

**Tarih:** 2026-11-08  
**Normatif iş kuralı:** rapor K-002, K-003, K-004, K-005, §8  
**Framework referansı (skill değil):** [Django 6.1 Security](https://docs.djangoproject.com/en/6.1/topics/security/)

Her bulgu Ek kural A ile etiketlidir. Satır referanssız kesin iddia yok.

---

## T-01 — HTTP yüzeyi yalnız admin

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `Backend/config/config/urls.py` L20–22: yalnızca `path('admin/', admin.site.urls)` |
| **Sonuç** | Tenant izolasyonunu API permission ile kanıtlayacak endpoint yok. Admin session auth tek yüzey. |
| **Risk** | İleride API eklenince scope unutulursa IDOR kaçınılmaz. |

## T-02 — Kullanıcı tek firma (model kuralı)

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `firmalar/models/kullanici.py` L49–56 (`firma` FK), L70–71 (`firma_id` yoksa ValidationError), L91–105 (`save` → `full_clean` if not superuser) |
| **Sonuç** | Normal kullanıcı için tek firma iş kuralı `clean`/`save` ile zorlanıyor. |
| **Boşluk** | DB kolonu `null=True` (L53); superuser muafiyeti (L103). |

## T-03 — `is_superuser` break-glass

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `kullanici.py` L98–105; `onay_servisi.py` L27–31 (`is_superuser` → platform sayılır); test tabanı `urunler/tests/_base.py` L28–29 platformu superuser ile kuruyor |
| **Sonuç** | Teknik superuser = iş platform yetkisi. Rapor K-003 ile çelişir. |
| **Runtime test** | Bu oturumda ayrı superuser-without-firma create/save test komutu çalıştırılmadı → ek davranış **DOĞRULANAMADI** (kod yolu okundu). |

## T-04 — Tek platform firması (DB)

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `firmalar/models/firma.py` L32–37 `UniqueConstraint` `tek_platform_firmasi`; migration `firmalar/migrations/0001_initial.py` aynı constraint |
| **Sonuç** | En fazla bir `platform_mu=True` satırı. |

## T-05 — Admin’de tenant queryset yok

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `firmalar/admin/kullanici_admin.py` — `get_queryset` override yok (dosya L1–33); `urunler/admin/` altında `get_queryset` eşleşmesi yok (repo grep) |
| **Sonuç** | `is_staff` admin kullanıcısı, ModelAdmin varsayılanı ile tüm firmaların kayıtlarını görebilir/düzenleyebilir (Django admin varsayılan davranışı). |
| **Not** | Bu, Django’nun bilinen admin modelidir; “bug” değil, **eksik proje kısıtı**. Runtime ile iki staff kullanıcısı çapraz erişim testi yapılmadı → UI sonucu **DOĞRULANAMADI**. |

## T-06 — Rol → Group sync admin’e bağlı değil

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `rol_servisi.py` L43–54 `assign_user_role`; `kullanici_admin.py` içinde `save_model` / `assign_user_role` / `sync_user_role_groups` çağrısı yok (grep yalnızca model docstring ve services) |
| **Sonuç** | Admin’den rol değişince Group senkronu garanti değil. Comment L9–10 “otomatik senkron” iddiası kodla çelişiyor. |
| **Permission seed** | Rol gruplarına Permission atayan data migration/seed **bulunamadı** → DOĞRULANDI (yokluk). |

## T-07 — `onaya_gonder` sahiplik kontrolü yok

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `onay_servisi.py` L78–94: `kullanici` parametresi imzada var, gövdede kullanılmıyor; `urun.tedarikci_id == kullanici.firma_id` yok |
| **Sonuç** | K-004 doğrulanır. `onayla` L98–99 platform şartı var; gönderme tarafı açık. |

## T-08 — Platform kontrolü kaba taneli

| | |
|--|--|
| **Sınıf** | DOĞRULANDI |
| **Kanıt** | `onay_servisi.platform_kullanicisi_mi` L27–31: superuser **veya** `firma.platform_mu` — rol/permission kodu yok |
| **Sonuç** | Platform firmasındaki herhangi bir kullanıcı platform işlemi yapabilir (firma bayrağı yeterli). Granular RBAC yok. |

## T-09 — Kör havuz (blind pool) uygulama yüzeyi

| | |
|--|--|
| **Sınıf** | DOĞRULANDI (uygulanmamış) |
| **Kanıt** | Buyer-facing serializer/API yok (`urls.py`); `Urun.tedarikci` FK katalogda (`urunler/models/urun.py`); admin `list_select_related = ("tedarikci", ...)` (`urun_admin.py` L57) |
| **Sonuç** | Maskeleme katmanı yok; admin’de tedarikçi kimliği görünür. API olmadığı için “alıcı API sızdırıyor” runtime iddiası kurulamaz. |
| **PLANLAMA BULGUSU** | API gelince response masking zorunlu (rapor §6.3–6.5). |

## T-10 — Tenant-owned tablolar / FK envanteri

| Model | Firma bağı | Sınıf |
|-------|------------|-------|
| `Kullanici.firma` | Doğrudan FK | DOĞRULANDI (`kullanici.py`) |
| `FirmaAdresi.firma` / `FirmaBankaHesabi.firma` | Doğrudan FK | DOĞRULANDI (model dosyaları) |
| `Urun.tedarikci` | Tedarikçi firma FK | DOĞRULANDI |
| `TedarikciTeklif.tedarikci` | FK | DOĞRULANDI |
| `FiyatSozlesmesi.firma` | FK | DOĞRULANDI |
| `Varyant` | Dolaylı (`urun`) | DOĞRULANDI |
| Sipariş / ödeme / RFQ | Yok | DOĞRULANDI (app yok) |

**PLANLAMA BULGUSU:** Ortak `TenantQuerySet` / `firma_id` denormalizasyonu Faz 1 tasarımında ele alınmalı; şema değişikliği bu denetimde yapılmaz.

## T-11 — Orta katman izolasyon primitives

| Aranan | Sonuç | Sınıf |
|--------|--------|-------|
| Tenant middleware | Yok | DOĞRULANDI (settings MIDDLEWARE L66–74) |
| Default manager `for_firma()` | Yok | DOĞRULANDI (managers yok) |
| DRF permission class | Yok (DRF kurulu değil / INSTALLED değil) | DOĞRULANDI |
| Object-level permission | Yok | DOĞRULANDI |

## T-12 — Settings güvenlik tabanı (framework)

| Ayar | Durum | Sınıf |
|------|-------|--------|
| `SECRET_KEY` env zorunlu | Var | DOĞRULANDI (`settings.py` L26) |
| `DEBUG` default False | Var | DOĞRULANDI (L14–15, L29) |
| Prod secure cookies / HSTS | `not DEBUG` bloğu | DOĞRULANDI (L36–42) |
| Canlı deploy doğrulaması | Yapılmadı | DOĞRULANAMADI |

---

## Özet: Faz 1’e taşınacak güvenlik işleri

1. Platform personeli → platform firması + iş rolü; `is_superuser` iş akışından çıkar (K-003).
2. `assign_user_role` tek yazma yolu; admin `save_model` bağla (K-005).
3. Rol → permission seed + test matrisi.
4. Tenant scope helper’ları (queryset/service); admin `get_queryset` firma kısıtı (staff platform hariç).
5. `onaya_gonder` sahiplik (K-004) — ürün servisi; Faz 1 kimlik ile birlikte veya hemen ardından.
6. Cross-firma IDOR testleri (PostgreSQL) — çalıştırılmadan “güvenli” denmez.
