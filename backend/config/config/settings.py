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
    # Reverse proxy (nginx vb.) arkasındaysan aç:
    # SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
    'tanimlar.apps.TanimlarConfig',
    'firmalar.apps.FirmalarConfig',
    'fiyatlama.apps.FiyatlamaConfig',
    'urunler.apps.UrunlerConfig',
    'stok.apps.StokConfig',
    'siparis.apps.SiparisConfig',
    'api.apps.ApiConfig',

]

# --- DRF (PRE ince API, U-012) ---------------------------------------------
REST_FRAMEWORK = {
    # Basic önce: WWW-Authenticate → unauth 401 (Session yalnız header üretmez → 403)
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "api.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
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
]

ROOT_URLCONF = 'config.urls'

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
