import logging
from typing import Tuple, List
from asgiref.sync import sync_to_async
from django_app.shop.models import Category, Product
from bot.core.config import CATEGORIES_PER_PAGE, PRODUCTS_PER_PAGE
from .breadcrumbs import get_category_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Загружен data.py версии 2025-04-22 с синхронным get_category_path")


@sync_to_async
def get_categories(parent_id: str, page: int) -> Tuple[str, List[Category], int]:
    """
    Получает категории для отображения с пагинацией.
    """
    logger.debug(f"Начало get_categories: parent_id={parent_id}, page={page}")

    try:
        if parent_id == "root":
            categories = Category.objects.filter(
                parent__isnull=True, is_active=True)
        else:
            categories = Category.objects.filter(
                parent_id=parent_id, is_active=True)

        total_categories = categories.count()
        total_pages = max(
            1, (total_categories + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE)
        page = max(1, min(page, total_pages))
        start = (page - 1) * CATEGORIES_PER_PAGE
        end = start + CATEGORIES_PER_PAGE
        categories_on_page = list(categories[start:end])

        breadcrumb = get_category_path(parent_id)  # Синхронный вызов
        if not isinstance(breadcrumb, str):
            logger.error(
                f"get_category_path вернул не строку: {type(breadcrumb)}: {breadcrumb}")
            breadcrumb = "🛍️ Каталог"

        if not categories_on_page:
            logger.debug(f"Категории не найдены, breadcrumb: {breadcrumb}")
            result = (f"{breadcrumb}\n\nКатегории не найдены.", [], 0)
            logger.info(f"Возвращён результат (нет категорий): {result}")
            return result

        text = f"{breadcrumb}\n\nВыберите {'категорию' if parent_id == 'root' else 'подкатегорию'}:"
        result = (text, categories_on_page, total_pages)
        logger.info(f"Возвращён результат: {result}")
        return result

    except Exception as e:
        logger.error(
            f"Ошибка при получении категорий для parent_id={parent_id}, page={page}: {e}")
        result = ("❌ Ошибка загрузки категорий", [], 0)
        logger.info(f"Возвращён результат при ошибке: {result}")
        return result


@sync_to_async
def get_products_page(category_id: int, page: int, per_page: int = PRODUCTS_PER_PAGE) -> Tuple[List[Product], int]:
    """
    Получение страницы товаров с пагинацией.
    """
    logger.debug(f"Получение товаров: category_id={category_id}, page={page}")

    try:
        qs = Product.objects.filter(category_id=category_id, is_active=True)
        total_count = qs.count()
        start = (page - 1) * per_page
        end = start + per_page
        products = list(qs[start:end])
        logger.debug(
            f"Найдено {total_count} товаров, возвращено {len(products)} на странице {page}")
        return products, total_count
    except Exception as e:
        logger.error(
            f"Ошибка при получении товаров для category_id={category_id}, page={page}: {e}")
        return [], 0
