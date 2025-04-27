from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.handlers.start.subscriptions import check_subscriptions
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID
from bot.handlers.cart.models import async_get_or_create_user, async_get_cart_quantity


async def main_menu_keyboard(bot, user_id):
    """Формирует клавиатуру главного меню с учётом подписки."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Проверяем подписку
    has_subscription = True
    if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
        subscription_result, _ = await check_subscriptions(bot, user_id)
        has_subscription = subscription_result

    # Получаем объект пользователя
    user, _ = await async_get_or_create_user(tg_id=user_id)

    # Формируем текст кнопки корзины
    cart_quantity = await async_get_cart_quantity(user)
    cart_text = f"🛒 Корзина: {cart_quantity} шт." if cart_quantity > 0 else "🛒 Корзина"

    # Определяем кнопки (структура как на скриншоте: 2 кнопки в ряду)
    if has_subscription:
        # Кнопки для подписанных пользователей
        keyboard.inline_keyboard.extend([
            [
                InlineKeyboardButton(
                    text="🛍 Каталог", callback_data="catalog"),
                InlineKeyboardButton(text="📋 Прайс-лист",
                                     callback_data="price_list_1"),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            ],
            [
                InlineKeyboardButton(text=cart_text, callback_data="cart"),
                InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
            ],
        ])
    else:
        # Кнопки для неподписанных пользователей (с замочками)
        keyboard.inline_keyboard.extend([
            [
                InlineKeyboardButton(text="🔒 🛍 Каталог",
                                     callback_data="locked_catalog"),
                InlineKeyboardButton(text="🔒 📋 Прайс-лист",
                                     callback_data="locked_price_list"),
            ],
            [
                InlineKeyboardButton(text="🔒 👤 Профиль",
                                     callback_data="locked_profile"),
                InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            ],
            [
                InlineKeyboardButton(
                    text=f"🔒 {cart_text}", callback_data="locked_cart"),
                InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
            ],
        ])

    return keyboard


async def profile_keyboard(user):
    """Формирует клавиатуру профиля."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]
    ])
    return keyboard


async def price_list_keyboard(user, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Формирует клавиатуру для пагинации прайс-листа."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Пагинация
    pagination = []
    if page > 1:
        pagination.append(InlineKeyboardButton(
            text="⬅️", callback_data=f"price_list_{page - 1}"))
    pagination.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        pagination.append(InlineKeyboardButton(
            text="➡️", callback_data=f"price_list_{page + 1}"))
    if pagination:
        keyboard.inline_keyboard.append(pagination)

    # Кнопка "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")
    ])

    return keyboard
