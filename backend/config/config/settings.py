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

# AUD-001b — X-Forwarded-For güvenilir proxy hop sayısı (0 = yalnız REMOTE_ADDR)
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)

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
    'api.apps.ApiConfig',

]

# --- DRF (PRE ince API, U-012) ---------------------------------------------
# Token birincil API kimliği; Basic WWW-Authenticate/401 için korunur (Session 403 üretir).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "api.authentication.SessionAuthentication",
    ],
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
    },
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.openapi.AutoSchema",
}

AUTH_USER_MODEL = "firmalar.Kullanici"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.IdempotencyKeyMiddleware',  # PRE-005: header → request.idempotency_key
]

ROOT_URLCONF = 'config.urls'

LOGIN_URL = "/buyer/login/"
LOGIN_REDIRECT_URL = "/buyer/"
LOGOUT_REDIRECT_URL = "/buyer/login/"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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
    }
}

# --- Şifre doğrulama --------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
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
# "fake" = geliştirme/test. Canlı banka yok. Secret asla koda yazılmaz.
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="fake")
PAYMENT_FAKE_FORCE_FAIL = env.bool("PAYMENT_FAKE_FORCE_FAIL", default=False)

# --- Kargo carrier (F6-021) -------------------------------------------------
# "fake" = geliştirme/test. Canlı carrier yok. Secret koda yazılmaz.
CARRIER_PROVIDER = env("CARRIER_PROVIDER", default="fake")
CARRIER_FAKE_FORCE_FAIL = env.bool("CARRIER_FAKE_FORCE_FAIL", default=False)
# F6-022: True → teslim_et öncesi POD zorunlu (ADR-0013: varsayılan opsiyonel).
SHIPMENT_POD_REQUIRED = env.bool("SHIPMENT_POD_REQUIRED", default=False)
# F5-021 webhook: boşsa endpoint 401 (fail-closed). Secret koda yazılmaz.
PAYMENT_WEBHOOK_SECRET = env("PAYMENT_WEBHOOK_SECRET", default="")
