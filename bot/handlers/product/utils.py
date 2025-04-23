import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, FSInputFile
from aiogram.utils.markdown import hbold, hitalic
from django_app.shop.models import Product
from asgiref.sync import sync_to_async
from bot.core.config import PRICE_DECIMAL_PLACES

logger = logging.getLogger(__name__)
logger.info("Загружен product/utils.py версии 2025-04-23-10")


@sync_to_async
def get_product_category(product):
    """Синхронная функция для получения категории продукта."""
    logger.debug(f"Получение категории для продукта ID {product.id}")
    return product.category


@sync_to_async
def get_category_parent_id(category):
    """Синхронная функция для получения ID родительской категории."""
    if category:
        logger.debug(f"Получение родителя для категории ID {category.id}")
        return category.parent.id if category.parent else None
    logger.debug("Категория отсутствует")
    return None


@sync_to_async
def get_category_path(category):
    """Синхронная функция для построения пути категории."""
    path = []
    current = category
    while current:
        logger.debug(f"Добавление категории {current.name} в путь")
        path.append(current.name)
        current = current.parent
    return path


async def generate_back_data(product: Product) -> str:
    """Генерирует callback_data для кнопки 'Назад'."""
    try:
        logger.debug(f"Генерация back_data для продукта ID {product.id}")
        category = await get_product_category(product)
        if category:
            parent_id = await get_category_parent_id(category)
            if parent_id:
                callback_data = f"cat_page_{parent_id}_1"
                logger.debug(
                    f"Сгенерированы данные для кнопки 'Назад': {callback_data}")
                return callback_data
            else:
                logger.debug(
                    "У категории нет родителя, возврат к главному меню")
                return "main_menu"
        else:
            logger.warning(f"У продукта ID {product.id} нет категории")
            return "main_menu"
    except Exception as e:
        logger.error(
            f"Ошибка при генерации back_data для продукта ID {product.id}: {e}")
        return "main_menu"


async def generate_product_text(product: Product) -> str:
    """Генерирует текст для отображения продукта."""
    try:
        logger.debug(f"Генерация текста для продукта ID {product.id}")
        category = await get_product_category(product)
        category_path = await get_category_path(category) if category else []
        category_path = " > ".join(
            reversed(category_path)) if category_path else "Без категории"

        # Форматирование цены с учётом PRICE_DECIMAL_PLACES
        price = float(product.price)
        price_str = f"{price:.{PRICE_DECIMAL_PLACES}f} ₽"

        text = (
            f"🏷️ {hitalic(category_path)}\n\n"
            f"{hbold(product.name)}\n"
            f"💰 {price_str}\n\n"
            f"📝 {product.description or 'Нет описания'}"
        )
        logger.debug(f"Сгенерирован текст для продукта ID {product.id}")
        return text
    except Exception as e:
        logger.error(
            f"Ошибка при генерации текста для продукта ID {product.id}: {e}")
        return f"{product.name}\nОшибка при загрузке данных"


async def handle_photo_message(
    callback: CallbackQuery,
    product: Product,
    text: str,
    back_data: str,
    cart_total: float,
    cart_quantity: int
):
    """Обрабатывает отправку сообщения с фото."""
    try:
        from .keyboards import product_detail_keyboard
        markup = product_detail_keyboard(
            product_id=product.id,
            quantity=1,
            cart_total=cart_total,
            cart_quantity=cart_quantity,
            back_data=back_data
        )
        if product.photo:
            logger.debug(
                f"Отправка фото для продукта ID {product.id}: {product.photo.path}")
            await callback.message.delete()  # Удаляем старое сообщение
            await callback.message.answer_photo(
                photo=FSInputFile(product.photo.path),
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
            logger.debug(
                f"Отправлено сообщение с фото продукта ID {product.id}")
        else:
            logger.debug(
                f"Фото отсутствует для продукта ID {product.id}, отправка текста")
            await handle_text_message(callback, product, text, back_data, 1, cart_total, cart_quantity)
    except Exception as e:
        logger.error(
            f"Ошибка при отправке фото для продукта ID {product.id}: {e}")
        await callback.answer("Ошибка при отображении фото.", show_alert=True)


async def handle_text_message(
    callback: CallbackQuery,
    product: Product,
    text: str,
    back_data: str,
    quantity: int,
    cart_total: float,
    cart_quantity: int
):
    """Обрабатывает отправку текстового сообщения."""
    try:
        from .keyboards import product_detail_keyboard
        markup = product_detail_keyboard(
            product_id=product.id,
            quantity=quantity,
            cart_total=cart_total,
            cart_quantity=cart_quantity,
            back_data=back_data
        )
        await callback.message.edit_text(
            text=text,
            reply_markup=markup,
            parse_mode="HTML"
        )
        logger.debug(
            f"Отправлено текстовое сообщение для продукта ID {product.id}")
    except Exception as e:
        logger.error(
            f"Ошибка при отправке текста для продукта ID {product.id}: {e}")
        await callback.answer("Ошибка при отображении товара.", show_alert=True)
