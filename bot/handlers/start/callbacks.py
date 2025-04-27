import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from bot.handlers.start.subscriptions import check_subscriptions
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID, SUPPORT_TELEGRAM
from bot.handlers.start.messages import welcome_message, format_user_profile
from bot.handlers.start.keyboards import main_menu_keyboard, profile_keyboard, price_list_keyboard
from bot.handlers.cart.models import async_get_or_create_user, async_get_cart_quantity

router = Router()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info(
    "Загружен start/callbacks.py версии 2025-04-27 с async_get_or_create_user")


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} возвращается в главное меню.")

    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        language_code=callback.from_user.language_code
    )
    has_cart = (await async_get_cart_quantity(user)) > 0
    welcome_text = welcome_message(callback.from_user.first_name, has_cart)

    try:
        await callback.message.edit_text(
            welcome_text,
            reply_markup=await main_menu_keyboard(callback.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")
        await callback.message.delete()
        await callback.message.answer(
            welcome_text,
            reply_markup=await main_menu_keyboard(callback.bot, user_id),
            disable_web_page_preview=True,
            parse_mode="Markdown"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("locked_"))
async def handle_locked_button(callback: CallbackQuery):
    """Обработка нажатия на заблокированные кнопки."""
    user_id = callback.from_user.id
    logger.info(
        f"Пользователь {user_id} нажал на заблокированную кнопку: {callback.data}")

    _, message_text = await check_subscriptions(callback.bot, user_id)
    if not message_text:
        message_text = "📢 Пожалуйста, подпишитесь на канал/группу, чтобы разблокировать эту функцию."

    try:
        await callback.message.edit_text(
            message_text,
            disable_web_page_preview=True,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                              [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
        )
    except TelegramBadRequest:
        await callback.message.answer(
            message_text,
            disable_web_page_preview=True,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                              [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
        )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показ профиля."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил профиль.")

    # Проверка подписки
    if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
        subscription_result, message_text = await check_subscriptions(callback.bot, user_id, "profile")
        if not subscription_result:
            try:
                await callback.message.edit_text(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                      [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                      [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
                )
            await callback.answer()
            return

    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        language_code=callback.from_user.language_code
    )
    text = await format_user_profile(user)
    keyboard = await profile_keyboard(user)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("price_list_"))
async def show_price_list(callback: CallbackQuery):
    """Показ прайс-листа."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил прайс-лист.")

    # Проверка подписки
    if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
        subscription_result, message_text = await check_subscriptions(callback.bot, user_id, "price_list")
        if not subscription_result:
            try:
                await callback.message.edit_text(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                      [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
                )
            except TelegramBadRequest:
                await callback.message.answer(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                      [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]])
                )
            await callback.answer()
            return

    page = int(callback.data.split("_")[-1])
    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        language_code=callback.from_user.language_code
    )
    from .messages import get_price_list
    price_list_text, total_pages = await get_price_list(page)

    try:
        await callback.message.edit_text(
            price_list_text,
            reply_markup=await price_list_keyboard(user, page, total_pages),
            parse_mode="Markdown"
        )
    except TelegramBadRequest:
        await callback.message.answer(
            price_list_text,
            reply_markup=await price_list_keyboard(user, page, total_pages),
            parse_mode="Markdown"
        )
    await callback.answer()


@router.callback_query(F.data == "about")
async def show_about(callback: CallbackQuery):
    """Показ информации 'О боте' через callback."""
    user_id = callback.from_user.id
    logger.info(
        f"Пользователь {user_id} запросил информацию 'О боте' через callback.")

    text = (
        "ℹ️ О нас\n\n"
        "Мы - ваш любимый магазин! 🛍️\n"
        "Здесь вы найдёте всё, что нужно, и даже больше!\n\n"
        f"📩 По любым вопросам обращайтесь в поддержку: {SUPPORT_TELEGRAM}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="main_menu")]
    ])

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка при отправке информации 'О боте': {e}")
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    await callback.answer()
