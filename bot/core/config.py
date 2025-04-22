import os
from dotenv import load_dotenv

load_dotenv()

# Общие настройки бота
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPPORT_TELEGRAM = os.getenv("SUPPORT_TELEGRAM", "@SupportBot")

# Настройки подписки
SUBSCRIPTION_CHANNEL_ID = os.getenv("SUBSCRIPTION_CHANNEL_ID", None)
SUBSCRIPTION_GROUP_ID = os.getenv("SUBSCRIPTION_GROUP_ID", None)
FREE_ACCESS_COMMANDS = ['/faq', '/about']

# Логирование
LOGGING_CONFIG = {
    "level": "DEBUG",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "filename": "logs/bot.log",
    "filemode": "a"
}

# Настройки FAQ
FAQ_PER_PAGE = 5  # Количество вопросов FAQ на одной странице
FAQ_SEARCH_PER_PAGE = 5  # Количество результатов поиска FAQ на одной странице

# Настройки каталога
CATEGORIES_PER_PAGE = 5  # Количество категорий на одной странице
CATEGORIES_PER_ROW = 2  # Количество категорий в одном ряду клавиатуры
PRODUCTS_PER_PAGE = 5  # Количество товаров на одной странице
PRODUCTS_PER_ROW = 2  # Количество товаров в одном ряду клавиатуры
CART_ITEMS_PER_PAGE = 5  # Количество товаров на странице в корзине
CART_ITEMS_PER_ROW = 2  # Количество товаров в одном ряду в корзине

# Текстовые сообщения
CATALOG_MESSAGE = "🛍️ Выберите товар:"  # Текст при отображении товаров
# Сообщение при отсутствии категорий
CATEGORY_NOT_FOUND = "Категории не найдены."
PRODUCT_NOT_FOUND = "Товары не найдены."  # Сообщение при отсутствии товаров
CATALOG_ERROR = "❌ Ошибка загрузки каталога."  # Сообщение об ошибке каталога

# Ограничения
MAX_BREADCRUMB_LENGTH = 100  # Максимальная длина breadcrumb
MAX_BUTTON_TEXT_LENGTH = 30  # Максимальная длина текста кнопки
