import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.start.messages import welcome_message, format_user_profile
from bot.handlers.start.keyboards import main_menu_keyboard, profile_keyboard
from bot.handlers.start.subscriptions import check_subscriptions
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID, SUPPORT_TELEGRAM
from bot.handlers.cart.models import async_get_or_create_user, async_get_cart_quantity

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/start")
async def start_command(message: Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    logger.info(f"Получена команда /start от пользователя {user_id}")

    user_data = message.from_user
    user, _ = await async_get_or_create_user(
        tg_id=user_data.id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        language_code=user_data.language_code
    )

    # Проверка наличия товаров в корзине
    try:
        has_cart = (await async_get_cart_quantity(user)) > 0
    except Exception as e:
        logger.error(
            f"Ошибка при проверке корзины для пользователя {user_id}: {e}")
        has_cart = False

    welcome_text = welcome_message(user_data.first_name, has_cart)

    try:
        await message.answer(
            welcome_text,
            reply_markup=await main_menu_keyboard(message.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(
            f"Ошибка при отправке приветственного сообщения пользователю {user_id}: {e}")
        await message.answer(
            welcome_text,
            reply_markup=await main_menu_keyboard(message.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    logger.info(f"Приветственное сообщение отправлено пользователю {user_id}.")


@router.message(F.text == "/profile")
async def profile_command(message: Message):
    """Обработчик команды /profile с проверкой подписки."""
    user_id = message.from_user.id
    logger.info(f"Получена команда /profile от пользователя {user_id}")

    # Проверка подписки
    if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
        subscription_result, message_text = await check_subscriptions(message.bot, user_id, "/profile")
        if not subscription_result:
            await message.answer(
                message_text,
                disable_web_page_preview=True,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                  [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
            )
            return

    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=message.from_user.first_name
    )

    text = await format_user_profile(user)
    keyboard = await profile_keyboard(user)

    try:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    except TelegramBadRequest as e:
        logger.error(
            f"Ошибка при отправке профиля пользователю {user_id}: {e}")
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
