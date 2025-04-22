import logging
from django_app.shop.models import Category

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Загружен breadcrumbs.py версии 2025-04-22 без sync_to_async")


def get_category_path(category_id: str) -> str:
    """
    Формирует путь категорий (breadcrumb) для отображения.
    :param category_id: ID категории или "root".
    :return: Строка с путём категорий (например, "Каталог > Электроника > Смартфоны").
    """
    logger.debug(f"Формирование пути для категории: category_id={category_id}")
    if category_id == "root":
        return "🛍️ Каталог"

    try:
        path = []
        current_category = Category.objects.get(id=category_id)
        while current_category:
            path.append(current_category.name)
            current_category = current_category.parent
        path.reverse()
        result = "🛍️ " + " > ".join(path)
        logger.debug(f"Путь категории сформирован: {result}")
        return result
    except Category.DoesNotExist:
        logger.warning(f"Категория с ID {category_id} не найдена.")
        return "🛍️ Каталог"
    except Exception as e:
        logger.error(
            f"Ошибка при формировании пути категории {category_id}: {e}")
        return "🛍️ Каталог"
