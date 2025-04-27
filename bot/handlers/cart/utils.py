import logging
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.text_decorations import html_decoration as html
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from .models import async_get_cart, async_get_cart_items, async_get_cart_quantity, async_get_cart_total, async_get_cart_details, async_get_order_details
from .keyboards import generate_cart_keyboard, generate_back_keyboard, generate_skip_keyboard, generate_confirmation_keyboard, generate_empty_cart_keyboard
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID, CART_ITEMS_PER_PAGE, PRICE_DECIMAL_PLACES, CART_EMOJI, CART_LABEL, CART_CURRENCY, CART_EMPTY_TEXT
from bot.handlers.start.subscriptions import check_subscriptions

# Настройка логирования
logger = logging.getLogger(__name__)


async def ensure_subscription(request: Message | CallbackQuery, user_id: int, command: str) -> bool:
    """Проверяет подписку пользователя и возвращает True, если доступ разрешён."""
    if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
        subscription_result, message_text = await check_subscriptions(request.bot, user_id, command)
        if not subscription_result:
            await request.answer(
                message_text,
                disable_web_page_preview=True,
                parse_mode="Markdown"
            )
            return False
    return True


async def delete_previous_message(request: Message | CallbackQuery, state: FSMContext) -> None:
    """Удаляет предыдущее сообщение, если его ID сохранён в состоянии."""
    data = await state.get_data()
    message_id = data.get("message_id")
    if message_id:
        try:
            if isinstance(request, Message):
                await request.bot.delete_message(chat_id=request.chat.id, message_id=message_id)
            else:
                await request.message.delete()
        except Exception as e:
            logger.warning(
                f"Не удалось удалить сообщение (message_id={message_id}): {e}")


async def send_message_with_state(
    request: Message | CallbackQuery,
    text: str,
    state: FSMContext,
    reply_markup: InlineKeyboardMarkup = None,
    parse_mode: str = None
) -> None:
    """Отправляет сообщение и сохраняет его ID в состоянии."""
    msg = await (request.message if isinstance(request, CallbackQuery) else request).answer(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
    await state.update_data(message_id=msg.message_id)


async def generate_order_text(user, state: FSMContext, cart_id: int) -> tuple[str, int]:
    """Формирует текст с данными заказа."""
    data = await state.get_data()
    items_text, total, _ = await async_get_cart_details(cart_id)
    formatted_total = f"{float(total):.{PRICE_DECIMAL_PLACES}f}"
    text = (
        f"📋 Проверьте данные заказа:\n\n"
        f"📍 Адрес: {html.quote(data.get('address'))}\n"
        f"📞 Телефон: {html.quote(data.get('phone'))}\n"
        f"💬 Пожелания: {html.quote(data.get('wishes')) if data.get('wishes') else 'Нет'}\n"
        f"⏰ Время доставки: {html.quote(data.get('desired_delivery_time')) if data.get('desired_delivery_time') else 'Не указано'}\n\n"
        f"🛒 Состав заказа:\n{items_text}\n\n"
        f"💵 Итого: {html.bold(f'{formatted_total} {CART_CURRENCY}')}\n\n"
    )
    return text, total


async def back_to_previous_state(
    callback: CallbackQuery,
    state: FSMContext,
    previous_state: str,
    prompt: str,
    keyboard: InlineKeyboardMarkup
) -> None:
    """Универсальная функция для возврата к предыдущему состоянию."""
    await delete_previous_message(callback, state)
    await send_message_with_state(
        callback,
        prompt,
        state,
        reply_markup=keyboard
    )
    await state.set_state(previous_state)


async def _send_cart_message(
    message: Message | CallbackQuery,
    text: str,
    kb: InlineKeyboardMarkup,
    photo: str | None = None
) -> None:
    """Внутренняя функция для отправки или редактирования сообщения корзины."""
    try:
        if isinstance(message, Message):
            if photo:
                await message.answer_photo(
                    photo=photo,
                    caption=text,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.answer(
                    text,
                    reply_markup=kb,
                    parse_mode=ParseMode.HTML
                )
        else:
            if photo:
                media = InputMediaPhoto(
                    media=photo,
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
                try:
                    await message.message.edit_media(media=media, reply_markup=kb)
                except TelegramBadRequest:
                    await message.message.delete()
                    await message.message.answer_photo(
                        photo=photo,
                        caption=text,
                        reply_markup=kb,
                        parse_mode=ParseMode.HTML
                    )
            else:
                try:
                    await message.message.edit_text(
                        text,
                        reply_markup=kb,
                        parse_mode=ParseMode.HTML
                    )
                except TelegramBadRequest:
                    await message.message.delete()
                    await message.message.answer(
                        text,
                        reply_markup=kb,
                        parse_mode=ParseMode.HTML
                    )
            await message.answer()
    except TelegramBadRequest as e:
        logger.error(
            f"Ошибка при отображении корзины для пользователя {message.from_user.id}: {e}")
        if isinstance(message, Message):
            await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            await message.message.delete()
            await message.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


async def show_cart(user, message: Message | CallbackQuery, page: int = 1) -> None:
    """Показывает корзину пользователю с поддержкой пагинации."""
    items = await async_get_cart_items(user)

    if not items:
        text = f"{CART_EMOJI} {CART_LABEL}: {CART_EMPTY_TEXT}"
        kb = generate_empty_cart_keyboard()
        await _send_cart_message(message, text, kb)
        return

    # Получаем активную корзину пользователя
    cart = await async_get_cart(user)
    cart_id = cart.id

    # Получаем данные корзины
    # Сумма quantity всех CartItem
    cart_quantity = await async_get_cart_quantity(user)
    cart_total = await async_get_cart_total(user)
    items_text, _, first_item_photo = await async_get_cart_details(cart_id)

    # Логируем для проверки
    logger.info(
        f"Количество элементов (CartItem): {len(items)}, общее количество товаров: {cart_quantity}")

    # Форматируем сумму
    formatted_total = f"{float(cart_total):.{PRICE_DECIMAL_PLACES}f}"

    text = (
        f"{html.bold('Корзина:')}\n\n"
        f"{items_text}\n\n"
        f"Всего {cart_quantity} шт. на сумму {html.bold(f'{formatted_total} {CART_CURRENCY}')}"
    )

    # Генерируем клавиатуру с пагинацией
    kb = generate_cart_keyboard(
        user,
        items,
        cart_quantity=cart_quantity,
        cart_total=cart_total,
        page=page,
        items_per_page=CART_ITEMS_PER_PAGE
    )

    await _send_cart_message(message, text, kb, photo=first_item_photo)


def format_cart_button_text(cart_total: float, cart_quantity: int) -> str:
    """Форматирует текст для кнопки корзины."""
    try:
        if cart_quantity > 0:
            cart_total_str = f"{cart_total:.{PRICE_DECIMAL_PLACES}f} {CART_CURRENCY}"
            text = f"{CART_EMOJI} {CART_LABEL}: {cart_total_str} ({cart_quantity} шт.)"
        else:
            text = f"{CART_EMOJI} {CART_LABEL}: {CART_EMPTY_TEXT}"
        logger.debug(f"Сгенерирован текст кнопки корзины: {text}")
        return text
    except Exception as e:
        logger.error(f"Ошибка при форматировании текста кнопки корзины: {e}")
        return f"{CART_EMOJI} {CART_LABEL}: ошибка"
