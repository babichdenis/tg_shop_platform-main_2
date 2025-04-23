import logging
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)
logger.info("Загружен product/keyboards.py версии 2025-04-23-4")


def product_detail_keyboard(
    product_id: int,
    quantity: int,
    cart_total: float,
    cart_quantity: int,
    back_data: str = "main_menu"
) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для страницы продукта."""
    try:
        buttons = [
            [
                InlineKeyboardButton(
                    text="−", callback_data=f"dec:{product_id}"),
                InlineKeyboardButton(text=str(quantity), callback_data="noop"),
                InlineKeyboardButton(
                    text="+", callback_data=f"inc:{product_id}"),
            ],
            [
                InlineKeyboardButton(
                    text=f"Добавить в корзину ({quantity} шт.)",
                    callback_data=f"add:{product_id}:{quantity}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🛒 Корзина: {cart_total} ₽ ({cart_quantity} шт.)" if cart_quantity > 0 else "🛒 Корзина: пуста",
                    callback_data="cart"
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data=back_data),
                InlineKeyboardButton(text="В меню", callback_data="main_menu")
            ]
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        logger.debug(
            f"Сгенерирована клавиатура для продукта ID {product_id} с back_data={back_data}")
        return markup
    except Exception as e:
        logger.error(
            f"Ошибка при генерации клавиатуры для продукта ID {product_id}: {e}")
        raise
