"""
Django settings for config project.

Gizli değerler (SECRET_KEY, DB şifresi vb.) koda yazılmaz, .env dosyasından
veya ortam değişkenlerinden okunur.
"""

from decimal import Decimal
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    DB_HOST=(str, "localhost"),
    DB_PORT=(str, "5432"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
)
# .env dosyası varsa oku (canlıda gerçek ortam değişkenleri de çalışır)
environ.Env.read_env(BASE_DIR / ".env")

# --- Güvenlik ---------------------------------------------------------------
# Varsayılan yok: tanımlı değilse proje bilerek hata verip açılmaz.
SECRET_KEY = env("SECRET_KEY")

# Varsayılan False: DEBUG'ı yalnızca geliştirme .env dosyasında True yap.
DEBUG = env("DEBUG")

# Örn. .env içinde: ALLOWED_HOSTS=kuyumbank.com,www.kuyumbank.com
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # sorunsuzsa artır
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # Reverse proxy (nginx vb.): env ile aç (varsayılan kapalı).
    if env.bool("SECURE_PROXY_SSL_HEADER", default=False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ADR-0017 NX-1 — session cookie (Secure: prod bloğunda; SameSite Lax her ortam)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # JS / Next BFF X-CSRFToken okuyabilsin
# Aynı-origin reverse proxy; cross-site origin listesi (CSRF). CORS B1'de yok (ADR-0017 erteli).
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if DEBUG and not CSRF_TRUSTED_ORIGINS:
    # Next.dev default origins (rewrite same-host tercih; CSRF host kontrolü için)
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
# Ortak üst alan (opsiyonel cookie paylaşımı): .kuyumbank.local
SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default="") or None
CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default="") or None
# Mutlak oturum süresi (varsayılan 8 saat) + boşta kalma (varsayılan 30 dk)
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=28800)
SESSION_IDLE_TIMEOUT = env.int("SESSION_IDLE_TIMEOUT", default=1800)

# AUD-001b — X-Forwarded-For güvenilir proxy hop sayısı (0 = yalnız REMOTE_ADDR)
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)

# --- Cache (DRF throttle + HTML login throttle; çoklu worker için db/redis) ---
# DEBUG: LocMem OK. Prod (!DEBUG): varsayılan DatabaseCache; LocMem yalnız
# ALLOW_LOCMEM_CACHE=1 ile (system check Error).
_CACHE_BACKEND = env(
    "CACHE_BACKEND",
    default=(
        "django.core.cache.backends.locmem.LocMemCache"
        if DEBUG
        else "django.core.cache.backends.db.DatabaseCache"
    ),
)
_CACHE_LOCATION = env(
    "CACHE_LOCATION",
    default="kuyumbank-default" if DEBUG else "kuyumbank_cache",
)
CACHES = {
    "default": {
        "BACKEND": _CACHE_BACKEND,
        "LOCATION": _CACHE_LOCATION,
    }
}
ALLOW_LOCMEM_CACHE = env.bool("ALLOW_LOCMEM_CACHE", default=False)
# Admin login POST throttle — LoginThrottleMiddleware (ADR-0029)
LOGIN_THROTTLE_RATE = env("LOGIN_THROTTLE_RATE", default="10/min")
LOGIN_THROTTLE_USERNAME_RATE = env(
    "LOGIN_THROTTLE_USERNAME_RATE", default="20/min"
)

# --- Uygulamalar ------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # ExclusionConstraint / btree_gist (ADR-0007 K-008)

    # modüller
    'import_export',
    'rest_framework',
    'rest_framework.authtoken',  # SEC-001: TokenAuthentication
    'drf_spectacular',  # OpenAPI 3 + Swagger/ReDoc (TECH-OPENAPI-02)
    'tanimlar.apps.TanimlarConfig',
    'firmalar.apps.FirmalarConfig',
    'fiyatlama.apps.FiyatlamaConfig',
    'urunler.apps.UrunlerConfig',
    'stok.apps.StokConfig',
    'siparis.apps.SiparisConfig',
    'finans.apps.FinansConfig',
    'kalite.apps.KaliteConfig',
    'lojistik.apps.LojistikConfig',
    'belgeler.apps.BelgelerConfig',
    'piyasa.apps.PiyasaConfig',
    'bildirim.apps.BildirimConfig',
    'api.apps.ApiConfig',

]

# --- DRF (PRE ince API, U-012 / ADR-0017) ----------------------------------
# Session birincil; Token S2S (TTL); Basic varsayılan kapalı (DEBUG’ta açık).
_API_BASIC_AUTH_ENABLED = env.bool(
    "API_BASIC_AUTH_ENABLED", default=bool(DEBUG)
)
_DRF_AUTH = [
    "api.authentication.SessionAuthentication",
    "api.authentication.ExpiringTokenAuthentication",
]
if _API_BASIC_AUTH_ENABLED:
    _DRF_AUTH.append("rest_framework.authentication.BasicAuthentication")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": _DRF_AUTH,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("DRF_THROTTLE_ANON", default="60/min"),
        "user": env("DRF_THROTTLE_USER", default="600/min"),
        # F7-013: yüzey bazlı ek scope (view throttle_classes)
        "buyer": env("DRF_THROTTLE_BUYER", default="300/min"),
        "supplier": env("DRF_THROTTLE_SUPPLIER", default="300/min"),
        "ops": env("DRF_THROTTLE_OPS", default="600/min"),
        # API-B1: login brute-force
        "login": env("DRF_THROTTLE_LOGIN", default="10/min"),
        # Webhook AllowAny — provider retry (IP başına)
        "webhook": env("DRF_THROTTLE_WEBHOOK", default="120/min"),
    },
    "EXCEPTION_HANDLER": "api.exception_handler.problem_exception_handler",
    # Path keşfi: DRF AutoSchema (APIView). DTO: api.openapi_components.enrich.
    # Swagger/ReDoc UI: drf-spectacular views (/api/docs/, /api/redoc/).
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
}

# TECH-OPENAPI-02 — Swagger/ReDoc UI (şema üretimi DRF+enrich; bkz. schema_views)
SPECTACULAR_SETTINGS = {
    "TITLE": "Kuyumbank API",
    "DESCRIPTION": "API v1 — ADR-0017 / API_CONTRACT",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
# Prod’da docs kapalı (!DEBUG && !API_DOCS_PUBLIC).
API_DOCS_PUBLIC = env.bool("API_DOCS_PUBLIC", default=False)

# F7-015: API major sürüm yolu sabit /api/v1/ (breaking change → yeni major).
API_VERSION = "v1"
# API-B1: Idempotency-Key saklama süresi (saniye); varsayılan 24s.
IDEMPOTENCY_TTL_SECONDS = env.int("IDEMPOTENCY_TTL_SECONDS", default=86400)
# Advisory lock bekleme tavanı (pg_try_advisory_lock); sonsuz blok yok.
IDEMPOTENCY_LOCK_WAIT_SECONDS = env.float(
    "IDEMPOTENCY_LOCK_WAIT_SECONDS", default=5.0
)
# S2S Token TTL (sn). 0 = süresiz (kaçının). Varsayılan 7 gün.
AUTH_TOKEN_TTL_SECONDS = env.int("AUTH_TOKEN_TTL_SECONDS", default=604800)
# Basic auth ayrı sıkı throttle (middleware; yalnız Basic header’da)
DRF_THROTTLE_BASIC = env("DRF_THROTTLE_BASIC", default="5/min")
API_BASIC_AUTH_ENABLED = _API_BASIC_AUTH_ENABLED

# F7-023 CRM sync opt-in (varsayılan kapalı)
CRM_SYNC_ENABLED = env.bool("CRM_SYNC_ENABLED", default=False)

AUTH_USER_MODEL = "firmalar.Kullanici"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'api.middleware.RequestIdMiddleware',  # F8-002: X-Request-ID + log context
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'firmalar.middleware.SessionIdleTimeoutMiddleware',
    'firmalar.middleware.ActAsMiddleware',  # ADR-0021: act-as (Authentication sonrası)
    'firmalar.middleware.MfaEnforceMiddleware',  # platform e-posta OTP (MFA_ENFORCE_PLATFORM)
    'firmalar.middleware.LoginThrottleMiddleware',  # Admin login IP+username
    'firmalar.middleware.BasicAuthThrottleMiddleware',  # Basic brute-force
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.IdempotencyKeyMiddleware',  # PRE-005: header → request.idempotency_key
    'api.middleware.ApiNoStoreMiddleware',  # API-B1: no-store (kimlikli /api/v1/)
]

# F8-002 — yapılandırılmış log (JSON opt-in; secret anahtar dump yok)
LOG_JSON = env.bool("LOG_JSON", default=False)
_LOG_FORMATTERS = {
    "verbose": {
        "format": "[{asctime}] {levelname} request_id={request_id} {name}: {message}",
        "style": "{",
    },
    "structured": {
        "()": "config.logging_utils.StructuredFormatter",
    },
}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "config.logging_utils.RequestIdFilter",
        },
    },
    "formatters": _LOG_FORMATTERS,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "structured" if LOG_JSON else "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

ROOT_URLCONF = 'config.urls'

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/admin/login/"
# Act-as / davet linkleri için FE kökü (boş → /admin/)
FRONTEND_PORTAL_BASE_URL = env("FRONTEND_PORTAL_BASE_URL", default="")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # proje HTML yok (ADR-0029); Admin Django paket şablonları
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'firmalar.context_processors.act_as',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- Veritabanı -------------------------------------------------------------
IMPORT_EXPORT_USE_TRANSACTIONS = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
        # Bağlantı yeniden kullanımı (0 = her istekte yeni; prod önerisi 60+)
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=60),
    }
}

# --- Şifre doğrulama --------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': env.int("PASSWORD_MIN_LENGTH", default=12)},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Yerelleştirme ----------------------------------------------------------
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'  # veri yine UTC saklanır (USE_TZ=True), gösterim yerel
USE_I18N = True
USE_TZ = True

# --- Statik dosyalar --------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic için (canlı)

# --- Medya (ImageField; belge HTTP FE v1 dışı) --------------------------------
# Prod’da MEDIA_* reverse proxy / object storage ile korunmalı; Django URL ile
# public serve varsayılan değildir. Belge private storage_key modeli ayrıdır.
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

# --- Varsayılan PK tipi -----------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- E-posta ----------------------------------------------------------------
# Geliştirmede konsola yazar. Canlıda .env içinde SMTP backend'i verilir.
EMAIL_BACKEND = env("EMAIL_BACKEND")

# --- Marka / SEO (K-015, ADR-0005) ------------------------------------------
# Boşsa SEO fallback yalnızca ürün/kategori adıdır; pazarlama metni üretilmez.
PLATFORM_BRAND_NAME = env("PLATFORM_BRAND_NAME", default="")

# --- Gram bandı varsayılanı (K3, ADR-0005) ----------------------------------
# Varyant gram bandı yoksa teklif eşlemesinde kullanılan relatif tolerans.
VARYANT_GRAM_BANDI_ORAN = Decimal(env("VARYANT_GRAM_BANDI_ORAN", default="0.05"))

# --- HAS pozisyon limiti (ADR-0012 F5-K6 / FX-001) --------------------------
# 0 → limit kapalı (over_limit False). Decimal string env.
HAS_POSITION_LIMIT = Decimal(env("HAS_POSITION_LIMIT", default="0"))

# --- QC gram tolerans (ADR-0013 F6-K3 / F6-011) -----------------------------
# Bağıl ±% + isteğe bağlı mutlak taban (gram). Float yasak; Decimal string env.
QC_GRAM_TOLERANCE_PCT = Decimal(env("QC_GRAM_TOLERANCE_PCT", default="0.50"))
QC_GRAM_TOLERANCE_ABS = Decimal(env("QC_GRAM_TOLERANCE_ABS", default="0"))

# --- Ödeme sağlayıcı (F5-020) -----------------------------------------------
# "fake" = geliştirme/test. Prod'da ALLOW_FAKE_PROVIDERS=1 olmadan yasak (check).
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="fake")
PAYMENT_FAKE_FORCE_FAIL = env.bool("PAYMENT_FAKE_FORCE_FAIL", default=False)

# --- Kargo carrier (F6-021) -------------------------------------------------
CARRIER_PROVIDER = env("CARRIER_PROVIDER", default="fake")
CARRIER_FAKE_FORCE_FAIL = env.bool("CARRIER_FAKE_FORCE_FAIL", default=False)
ALLOW_FAKE_PROVIDERS = env.bool("ALLOW_FAKE_PROVIDERS", default=bool(DEBUG))

# --- MFA (e-posta OTP; platform + act-as) ------------------------------------
MFA_ENFORCE_PLATFORM = env.bool("MFA_ENFORCE_PLATFORM", default=False)
# Şifre sıfırlama link tabanı (Host header kullanılmaz). Örn. https://app.example.com
PASSWORD_RESET_BASE_URL = env("PASSWORD_RESET_BASE_URL", default="")
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=3600)
# ADR-0028 — davet TTL (saat); e-posta doğrulama yazma kapısı (varsayılan kapalı)
INVITE_TTL_HOURS = env.int("INVITE_TTL_HOURS", default=72)
EMAIL_VERIFY_REQUIRED_FOR_WRITE = env.bool(
    "EMAIL_VERIFY_REQUIRED_FOR_WRITE", default=False
)
# F6-022: True → teslim_et öncesi POD zorunlu (ADR-0013: varsayılan opsiyonel).
SHIPMENT_POD_REQUIRED = env.bool("SHIPMENT_POD_REQUIRED", default=False)
# F5-022: QC PASS sonrası hak ediş vade günü (0 = geçişte HAKEDILDI).
SUPPLIER_ACCRUAL_VADE_GUN = env.int("SUPPLIER_ACCRUAL_VADE_GUN", default=0)
# F5-021 webhook: boşsa endpoint 401 (fail-closed). Secret koda yazılmaz.
PAYMENT_WEBHOOK_SECRET = env("PAYMENT_WEBHOOK_SECRET", default="")
PAYMENT_WEBHOOK_REQUIRE_HMAC = env.bool(
    "PAYMENT_WEBHOOK_REQUIRE_HMAC", default=True
)
PAYMENT_WEBHOOK_REPLAY_SECONDS = env.int(
    "PAYMENT_WEBHOOK_REPLAY_SECONDS", default=300
)
# Virgülle CIDR/IP; boş = allow-list kapalı
PAYMENT_WEBHOOK_IP_ALLOWLIST = env.list(
    "PAYMENT_WEBHOOK_IP_ALLOWLIST", default=[]
)

# --- F8-003 Sentry (DSN boş → no-op) ----------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", default="development")
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0)
from config.sentry_init import init_sentry  # noqa: E402

SENTRY_ENABLED = init_sentry(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
)
