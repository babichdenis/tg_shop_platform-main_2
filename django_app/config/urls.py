import os
import logging
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static


# Настройка логирования для данного модуля
logger = logging.getLogger(__name__)
logger.info('Загрузка конфигурации URL-адресов.')

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),  # Административная панель Django
]

# Добавление маршрутов для обслуживания медиа-файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    logger.info('Маршруты для медиа-файлов добавлены в режиме отладки.')

logger.info('Конфигурация URL-адресов успешно загружена.')
