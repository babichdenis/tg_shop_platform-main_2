import os
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Настройка базового конфигурации логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("logs/asgi.log"),
        logging.StreamHandler()
    ]
)

# Создание логгера для данного модуля
logger = logging.getLogger(__name__)

# Установка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_app.config.settings')
logger.info('Переменная окружения DJANGO_SETTINGS_MODULE установлена.')

try:
    # Получение ASGI-приложения Django
    django_asgi_app = get_asgi_application()
    logger.info('ASGI-приложение Django успешно инициализировано.')
except Exception as e:
    logger.error(
        'Ошибка при инициализации ASGI-приложения Django:', exc_info=True)
    raise

# Настройка маршрутизации для ASGI
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(),
})
