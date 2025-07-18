import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback_secret_key')

# Режим отладки
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# Разрешенные хосты
ALLOWED_HOSTS = ["*"]

# Установленные приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mptt',
    'django_app.shop',
]

# Middleware
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Указание на файл конфигурации URL
ROOT_URLCONF = 'django_app.config.urls'

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI и ASGI приложения
WSGI_APPLICATION = 'django_app.config.wsgi.application'
ASGI_APPLICATION = 'django_app.config.asgi.application'

# Настройка базы данных для асинхронной работы
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
        'CONN_MAX_AGE': 0,  # Отключаем постоянные соединения для асинхронной работы
    }
}

# Настройка асинхронного адаптера для PostgreSQL
DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
# Отключаем транзакции на уровне запросов
DATABASES['default']['ATOMIC_REQUESTS'] = False

# django_app/settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Медиа файлы
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Язык и время
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Поле по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Токен бота
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
