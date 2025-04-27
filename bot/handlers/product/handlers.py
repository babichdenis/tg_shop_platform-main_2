import logging
from typing import Dict, Tuple
from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from .models import get_product_by_id, get_or_create_cart, update_cart_item
from .utils import generate_back_data, generate_product_text, handle_photo_message, handle_text_message
from .keyboards import product_detail_keyboard
from bot.core.utils import get_or_create_user
from bot.handlers.cart.models import async_get_cart_quantity, async_get_cart_total, async_get_cart_items

logger = logging.getLogger(__name__)
logger.info("Загружен product/handlers.py версии 2025-04-23-7")

router = Router()
quantity_storage: Dict[Tuple[int, int], int] = {}


async def get_cart_quantity_for_product(user, product_id: int) -> int:
    """Получает текущее количество товара в корзине."""
    try:
        items = await async_get_cart_items(user)
        for item in items:
            if item.product.id == product_id and item.is_active:
                return item.quantity
        return 0
    except Exception as e:
        logger.error(
            f"Ошибка при получении количества товара ID {product_id} из корзины: {e}")
        return 0


@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery, state: FSMContext):
    """Обработчик отображения деталей продукта."""
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    logger.info(
        f"Пользователь {user_id} запросил детали продукта ID {product_id}.")

    try:
        product = await get_product_by_id(product_id)
        user, _ = await get_or_create_user(user_id=user_id)

        # Получаем текущее количество в корзине
        cart_quantity_for_product = await get_cart_quantity_for_product(user, product_id)

        # Инициализируем quantity_storage с 1 (по умолчанию для добавления)
        key = (user_id, product_id)
        if key not in quantity_storage:
            quantity_storage[key] = 1

        try:
            cart_quantity = await async_get_cart_quantity(user)
            cart_total = await async_get_cart_total(user)
        except Exception as e:
            logger.error(
                f"Ошибка при получении данных корзины для пользователя {user.telegram_id}: {e}")
            cart_quantity = 0
            cart_total = 0

        back_data = await generate_back_data(product)
        text = await generate_product_text(product)
        # Добавляем информацию о количестве в корзине в текст
        text += f"\n\n🛒 В корзине: {cart_quantity_for_product} шт."

        if product.photo:
            await handle_photo_message(callback, product, text, back_data, cart_total, cart_quantity)
        else:
            await handle_text_message(callback, product, text, back_data, quantity=1, cart_total=cart_total, cart_quantity=cart_quantity)

    except Exception as e:
        logger.error(f"Ошибка при отображении продукта ID {product_id}: {e}")
        await callback.answer("Ошибка при отображении товара.", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("inc:"))
async def increase_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработчик увеличения количества."""
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    key = (user_id, product_id)
    current = quantity_storage.get(key, 1)
    quantity_storage[key] = current + 1
    logger.debug(
        f"Увеличено количество для продукта ID {product_id} до {quantity_storage[key]}.")
    await update_product_message(callback, product_id)


@router.callback_query(F.data.startswith("dec:"))
async def decrease_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработчик уменьшения количества."""
    product_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    key = (user_id, product_id)
    current = quantity_storage.get(key, 1)
    if current > 1:  # Не допускаем количество меньше 1
        quantity_storage[key] = current - 1
        logger.debug(
            f"Уменьшено количество для продукта ID {product_id} до {quantity_storage[key]}.")
    await update_product_message(callback, product_id)


@router.callback_query(F.data.startswith("add:"))
async def add_to_cart_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик добавления продукта в корзину."""
    _, product_id, quantity = callback.data.split(":")
    product_id = int(product_id)
    quantity = int(quantity)
    user_id = callback.from_user.id
    logger.info(
        f"Пользователь {user_id} добавляет продукт ID {product_id} с количеством {quantity}.")

    try:
        product = await get_product_by_id(product_id)
        user, _ = await get_or_create_user(user_id=user_id)
        cart, _ = await get_or_create_cart(user)
        item = await update_cart_item(cart, product, quantity)

        # Сбрасываем выбранное количество
        key = (user_id, product_id)
        quantity_storage[key] = 1  # Возвращаем к 1 после добавления

        await callback.answer(f"✅ Добавлено: {product.name} × {quantity}", show_alert=True)
        try:
            cart_quantity = await async_get_cart_quantity(user)
            cart_total = await async_get_cart_total(user)
        except Exception as e:
            logger.error(
                f"Ошибка при получении данных корзины для пользователя {user.telegram_id}: {e}")
            cart_quantity = 0
            cart_total = 0

        await update_product_message(
            callback,
            product_id,
            reset_quantity=False,
            cart_total=cart_total,
            cart_quantity=cart_quantity
        )

    except Exception as e:
        logger.error(f"Ошибка при добавлении товара ID {product_id}: {e}")
        await callback.answer("Ошибка при добавлении товара", show_alert=True)


async def update_product_message(
    callback: CallbackQuery,
    product_id: int,
    reset_quantity: bool = False,
    cart_total: float = 0,
    cart_quantity: int = 0
):
    """Обновляет сообщение с деталями продукта."""
    user_id = callback.from_user.id
    try:
        product = await get_product_by_id(product_id)
        back_data = await generate_back_data(product)
        key = (user_id, product_id)

        # Получаем количество из корзины
        user, _ = await get_or_create_user(user_id=user_id)
        cart_quantity_for_product = await get_cart_quantity_for_product(user, product_id)

        if reset_quantity:
            quantity = 1
            quantity_storage[key] = 1
        else:
            quantity = quantity_storage.get(key, 1)

        if not cart_total and not cart_quantity:
            try:
                cart_quantity = await async_get_cart_quantity(user)
                cart_total = await async_get_cart_total(user)
            except Exception as e:
                logger.error(
                    f"Ошибка при получении данных корзины для пользователя {user.telegram_id}: {e}")
                cart_quantity = 0
                cart_total = 0

        text = await generate_product_text(product)
        # Добавляем информацию о количестве в корзине в текст
        text += f"\n\n🛒 В корзине: {cart_quantity_for_product} шт."

        markup = product_detail_keyboard(
            product_id=product.id,
            quantity=quantity,  # Передаём только выбранное количество
            cart_total=cart_total,
            cart_quantity=cart_quantity,
            back_data=back_data
        )

        try:
            if product.photo:
                await callback.message.edit_caption(caption=text, reply_markup=markup)
            else:
                await callback.message.edit_text(text=text, reply_markup=markup)
        except Exception as e:
            if "message is not modified" not in str(e).lower():
                raise

    except Exception as e:
        logger.error(
            f"Ошибка при обновлении сообщения для продукта ID {product_id}: {e}")
        await callback.answer("Ошибка при обновлении сообщения.", show_alert=True)
