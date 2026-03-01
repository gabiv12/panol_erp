import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-cambiar-en-produccion")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# ============================================================
# HOSTS (local + túneles)
# ============================================================
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    ".ngrok-free.app",
    ".ngrok-free.dev",
    ".ngrok.io",
]

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "django_filters",
    "django_htmx",
    "import_export",

    # Apps
    "core",
    "usuarios",
    "flota",
    "inventario.apps.InventarioConfig",
    "adjuntos.apps.AdjuntosConfig",
    "auditoria.apps.AuditoriaConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditoria.middleware.AuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # HTMX
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.nav_visibility",
                "core.context_processors.nav_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite (dev)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Cordoba"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
# Volvemos al home (que ya redirige según permisos / estado)
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"

# ============================================================
# NGROK / PROXY / CSRF (sin desactivar)
# ============================================================
# Recomendado: setear PUBLIC_ORIGIN con la URL https exacta del túnel.
# Ej: https://tactless-concepcion-nonmanifestly.ngrok-free.dev
PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "").strip().rstrip("/")
PUBLIC_TUNNEL = os.getenv("PUBLIC_TUNNEL", "0") == "1"

TUNNEL_MODE = PUBLIC_TUNNEL or bool(PUBLIC_ORIGIN)

_public_is_https = PUBLIC_ORIGIN.lower().startswith("https://")

# Confianza en proxy https (ngrok termina TLS y reenvía a http local)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if TUNNEL_MODE else None
USE_X_FORWARDED_HOST = bool(TUNNEL_MODE)

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = []

if PUBLIC_ORIGIN:
    parsed = urlparse(PUBLIC_ORIGIN)
    if parsed.scheme and parsed.netloc:
        origin_exact = f"{parsed.scheme}://{parsed.netloc}"
        if origin_exact not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin_exact)
        # También permitimos host exacto en ALLOWED_HOSTS (por si no está en sufijos)
        if parsed.hostname and parsed.hostname not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(parsed.hostname)

# Fallback para ngrok random (si NO seteás PUBLIC_ORIGIN)
if TUNNEL_MODE:
    for o in (
        "https://*.ngrok-free.app",
        "https://*.ngrok-free.dev",
        "https://*.ngrok.io",
    ):
        if o not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(o)

# Cookies seguras SOLO si estás en HTTPS real (ngrok)
SESSION_COOKIE_SECURE = bool(TUNNEL_MODE and _public_is_https)
CSRF_COOKIE_SECURE = bool(TUNNEL_MODE and _public_is_https)

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# No forzamos SSL redirect en dev
SECURE_SSL_REDIRECT = os.getenv("FORCE_SSL_REDIRECT", "0") == "1"
# Uploads (fotos desde celulares pueden ser pesadas)
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024  # 60MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024  # 60MB

