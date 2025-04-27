import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.handlers.start.messages import welcome_message
from bot.handlers.start.keyboards import main_menu_keyboard
from bot.handlers.start.subscriptions import check_subscriptions
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID
from bot.handlers.cart.models import async_get_or_create_user, async_get_cart_quantity

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возвращает пользователя в главное меню."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} возвращается в главное меню.")

    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        language_code=callback.from_user.language_code
    )
    has_cart = await async_get_cart_quantity(user) > 0
    welcome_text = welcome_message(callback.from_user.first_name, has_cart)

    try:
        await callback.message.edit_text(
            welcome_text,
            reply_markup=await main_menu_keyboard(callback.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        await callback.message.delete()
        await callback.message.answer(
            welcome_text,
            reply_markup=await main_menu_keyboard(callback.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    await callback.answer()
