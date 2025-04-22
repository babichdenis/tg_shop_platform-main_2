import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from .models import (
    async_get_or_create_user, async_update_cart_item_quantity, async_remove_item_from_cart, async_clear_cart
)
from .utils import ensure_subscription, show_cart

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "cart")
@router.message(F.text == "/cart")
async def handle_cart(request: Message | CallbackQuery, state: FSMContext) -> None:
    """Обработчик кнопки/команды 'Корзина'."""
    user_id = request.from_user.id
    logger.info(f"Пользователь {user_id} запросил корзину.")

    # Проверка подписки
    if isinstance(request, Message):
        if not await ensure_subscription(request, user_id, "/cart"):
            return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    await state.update_data(cart_page=1)
    await show_cart(user, request, page=1)


@router.callback_query(F.data.startswith("increase_item_"))
async def increase_item(callback: CallbackQuery, state: FSMContext):
    """Увеличивает количество товара в корзине."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} увеличивает количество товара.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "increase_item"):
        return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    product_id = int(callback.data.split("_")[-1])

    await async_update_cart_item_quantity(user, product_id, 1)
    await callback.answer("Количество увеличено")
    logger.info(
        f"Пользователь {user_id} увеличил количество товара {product_id}.")

    data = await state.get_data()
    page = data.get("cart_page", 1)
    await show_cart(user, callback, page=page)


@router.callback_query(F.data.startswith("decrease_item_"))
async def decrease_item(callback: CallbackQuery, state: FSMContext):
    """Уменьшает количество товара в корзине."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} уменьшает количество товара.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "decrease_item"):
        return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    product_id = int(callback.data.split("_")[-1])

    await async_update_cart_item_quantity(user, product_id, -1)
    await callback.answer("Количество уменьшено")
    logger.info(
        f"Пользователь {user_id} уменьшил количество товара {product_id}.")

    data = await state.get_data()
    page = data.get("cart_page", 1)
    await show_cart(user, callback, page=page)


@router.callback_query(F.data.startswith("remove_item_"))
async def remove_item(callback: CallbackQuery, state: FSMContext):
    """Удаляет товар из корзины."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} удаляет товар из корзины.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "remove_item"):
        return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    product_id = int(callback.data.split("_")[-1])

    await async_remove_item_from_cart(user, product_id)
    await callback.answer("Товар удалён из корзины")
    logger.info(
        f"Пользователь {user_id} удалил товар {product_id} из корзины.")

    data = await state.get_data()
    page = data.get("cart_page", 1)
    await show_cart(user, callback, page=page)


@router.callback_query(F.data.startswith("cart_page_"))
async def handle_cart_pagination(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает пагинацию в корзине."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} переключает страницу корзины.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "cart_page"):
        return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    page = int(callback.data.split("_")[-1])

    await state.update_data(cart_page=page)
    await show_cart(user, callback, page=page)
    await callback.answer()


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery, state: FSMContext):
    """Очищает корзину."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} очищает корзину.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "clear_cart"):
        return

    user, _ = await async_get_or_create_user(tg_id=user_id)
    await async_clear_cart(user)
    await callback.answer("Корзина очищена")
    logger.info(f"Пользователь {user_id} очистил корзину.")

    await state.update_data(cart_page=1)
    await show_cart(user, callback, page=1)
