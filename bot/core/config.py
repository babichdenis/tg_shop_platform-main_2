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

# Количество знаков после запятой для цен (0 - без дробной части, 2 - два знака и т.д.)
PRICE_DECIMAL_PLACES = 0

# Настройки каталога
CATEGORIES_PER_PAGE = 5  # Количество категорий на одной странице
CATEGORIES_PER_ROW = 2  # Количество категорий в одном ряду клавиатуры
PRODUCTS_PER_PAGE = 5  # Количество товаров на одной странице
PRODUCTS_PER_ROW = 1  # Количество товаров в одном ряду клавиатуры
CART_ITEMS_PER_PAGE = 5  # Количество товаров на странице в корзине
SHOW_PRODUCT_PRICE_IN_CATALOG = True  # Отображать цену товара в каталоге

# Текстовые сообщения
CATALOG_MESSAGE = "🛍️ Выберите товар:"  # Текст при отображении товаров
# Сообщение при отсутствии категорий
CATEGORY_NOT_FOUND = "Категории не найдены."
PRODUCT_NOT_FOUND = "Товары не найдены."  # Сообщение при отсутствии товаров
CATALOG_ERROR = "❌ Ошибка загрузки каталога."  # Сообщение об ошибке каталога

# Ограничения
MAX_BREADCRUMB_LENGTH = 100  # Максимальная длина breadcrumb
MAX_BUTTON_TEXT_LENGTH = 30  # Максимальная длина текста кнопки

# Настройки корзины
CART_EMOJI = "🛒"  # Эмодзи для корзины
CART_LABEL = "Корзина"  # Текст метки корзины
CART_CURRENCY = "₽"  # Символ валюты
CART_EMPTY_TEXT = "пуста"  # Текст для пустой корзины

# Настройки для отображения родительской категории товара
# Показывать родительскую категорию товара (Категория > Товар)
SHOW_PARENT_CATEGORY = True
CATEGORY_SEPARATOR = " > "  # Разделитель между категорией и товаром

# Настройки страницы продукта
PRODUCT_CATEGORY_EMOJI = "🏷️"  # Эмодзи для категории
PRODUCT_NO_CATEGORY_TEXT = "Без категории"  # Текст для отсутствия категории
PRODUCT_PRICE_EMOJI = "💰"  # Эмодзи для цены
PRODUCT_DESCRIPTION_EMOJI = "📝"  # Эмодзи для описания
PRODUCT_NO_DESCRIPTION_TEXT = "Нет описания"  # Текст для отсутствия описания

# Настройки клавиатуры категорий и товаров
PAGINATION_PREV_EMOJI = "⬅️"  # Эмодзи для кнопки "Назад" (пагинация)
PAGINATION_NEXT_EMOJI = "➡️"  # Эмодзи для кнопки "Вперёд" (пагинация)
PAGINATION_TEXT_FORMAT = "{page}/{total_pages}"  # Формат текста пагинации
PRICE_LIST_EMOJI = "📋"  # Эмодзи для кнопки "Прайс-лист"
PRICE_LIST_LABEL = "Прайс-лист"  # Текст кнопки "Прайс-лист"
PRICE_LIST_CALLBACK = "price_list_1"  # Callback для кнопки "Прайс-лист"
BACK_BUTTON_EMOJI = "⬅️"  # Эмодзи для кнопки "Назад"
BACK_BUTTON_TEXT = "Назад"  # Текст кнопки "Назад"
MENU_BUTTON_TEXT = "⚓️ В меню"  # Текст кнопки "В меню"
NOOP_CALLBACK = "noop"  # Callback для неактивных кнопок
