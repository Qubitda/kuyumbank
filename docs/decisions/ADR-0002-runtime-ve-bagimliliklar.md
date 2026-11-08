# ADR-0002 — Runtime ve bağımlılıklar

**Durum:** Kabul edildi (Faz 0 denetim turu ile güncellendi)  
**Tarih:** 2026-11-08

## Karar

1. **Django 6.1.x** pin: `Django==6.1.2`. Matris: Python 3.12–3.14 ([FAQ](https://docs.djangoproject.com/en/6.1/faq/install/)).
2. PostgreSQL zorunlu; test varsayılanı proje DB’sidir.
3. `requirements.txt` **yalnızca doğrudan bağımlılık** içerir (import / INSTALLED_APPS kanıtlı).
4. Ortamda yüklü DRF, Celery, redis **projeye eklenmez** — kod kullanmıyor (DOĞRULANDI: `INSTALLED_APPS`, `urls.py`).
5. `django-environ` zorunlu: `settings.py` L10 `import environ` (HEAD requirements’ta eksikti).
6. DB sürücü: geliştirme ortamında `psycopg==3.3.6` var; HEAD’deki `psycopg2==2.9.13` ile uyumsuzluk vardı → pin `psycopg[binary]==3.3.6` (`ENGINE=django.db.backends.postgresql`).
7. `django-import-export` pin ortamla hizalı: `4.4.3` (HEAD 4.4.4 idi; ortam 4.4.3).

## Bilinçli dışarıda bırakılanlar

- Transitive pin yağmuru (asgiref/sqlparse/tablib…) — pip çözer; gereksiz drift yaratmayız.
- colorama — proje import etmiyor.

## Kanıt

| Paket | Neden | Sınıf |
|-------|-------|--------|
| Django | framework | DOĞRULANDI |
| django-environ | settings import | DOĞRULANDI |
| django-import-export | INSTALLED_APPS | DOĞRULANDI |
| psycopg | DATABASES ENGINE + pip freeze | DOĞRULANDI |
| djangorestframework | freeze’te var, projede yok | DOĞRULANDI — requirements’a **konmaz** |
