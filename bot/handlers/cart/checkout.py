import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.utils.text_decorations import html_decoration as html

from .models import async_get_or_create_user, async_get_cart, async_get_cart_items, async_create_order, async_get_order_details
from .keyboards import generate_edit_choice_keyboard, generate_back_keyboard, generate_skip_keyboard, generate_confirmation_keyboard  # Обновлённый импорт
from .states import OrderState
from .utils import (
    ensure_subscription, delete_previous_message, send_message_with_state,
    generate_order_text, back_to_previous_state, show_cart
)
from bot.core.config import SUPPORT_TELEGRAM

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс оформления заказа."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} начинает оформление заказа.")

    # Проверка подписки
    if not await ensure_subscription(callback, user_id, "checkout"):
        return

    user, _ = await async_get_or_create_user(user_id)
    cart_items = await async_get_cart_items(user)

    if not cart_items:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
        return

    await delete_previous_message(callback, state)
    await send_message_with_state(
        callback,
        "📍 Пожалуйста, укажите адрес доставки:",
        state,
        reply_markup=generate_back_keyboard()
    )
    await state.set_state(OrderState.waiting_for_address)


@router.callback_query(F.data == "back", OrderState.waiting_for_address)
async def back_from_address(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к корзине из шага ввода адреса."""
    user, _ = await async_get_or_create_user(callback.from_user.id)
    data = await state.get_data()
    page = data.get("cart_page", 1)
    await state.clear()
    await show_cart(user, callback, page=page)


@router.message(OrderState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обрабатывает введённый адрес."""
    address = message.text.strip()
    if not address:
        await message.answer("❌ Адрес не может быть пустым. Пожалуйста, введите снова:")
        return

    await state.update_data(address=address)
    await delete_previous_message(message, state)
    await send_message_with_state(
        message,
        "📞 Пожалуйста, укажите ваш номер телефона:",
        state,
        reply_markup=generate_back_keyboard()
    )
    await state.set_state(OrderState.waiting_for_phone)


@router.callback_query(F.data == "back", OrderState.waiting_for_phone)
async def back_from_phone(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к вводу адреса."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_address,
        "📍 Пожалуйста, укажите адрес доставки:",
        generate_back_keyboard()
    )


@router.message(OrderState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обрабатывает введённый номер телефона."""
    phone = message.text.strip()
    if not re.match(r'^\+?\d{10,15}$', phone):
        await message.answer("❌ Некорректный номер телефона. Пожалуйста, введите снова:")
        return

    await state.update_data(phone=phone)
    await delete_previous_message(message, state)
    await send_message_with_state(
        message,
        "💬 Укажите пожелания к заказу (или нажмите 'Пропустить'):",
        state,
        reply_markup=generate_skip_keyboard()
    )
    await state.set_state(OrderState.waiting_for_wishes)


@router.callback_query(F.data == "back", OrderState.waiting_for_wishes)
async def back_from_wishes(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к вводу телефона."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_phone,
        "📞 Пожалуйста, укажите ваш номер телефона:",
        generate_back_keyboard()
    )


@router.message(OrderState.waiting_for_wishes)
@router.callback_query(F.data == "skip", OrderState.waiting_for_wishes)
async def process_wishes(request: Message | CallbackQuery, state: FSMContext):
    """Обрабатывает пожелания к заказу."""
    wishes = request.text.strip() if isinstance(request, Message) else None
    await state.update_data(wishes=wishes)

    await delete_previous_message(request, state)
    await send_message_with_state(
        request,
        "⏰ Укажите желаемое время доставки (или нажмите 'Пропустить'):",
        state,
        reply_markup=generate_skip_keyboard()
    )
    await state.set_state(OrderState.waiting_for_delivery_time)


@router.callback_query(F.data == "back", OrderState.waiting_for_delivery_time)
async def back_from_delivery_time(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к вводу пожеланий."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_wishes,
        "💬 Укажите пожелания к заказу (или нажмите 'Пропустить'):",
        generate_skip_keyboard()
    )


@router.message(OrderState.waiting_for_delivery_time)
@router.callback_query(F.data == "skip", OrderState.waiting_for_delivery_time)
async def process_delivery_time(request: Message | CallbackQuery, state: FSMContext):
    """Обрабатывает желаемое время доставки."""
    delivery_time = request.text.strip() if isinstance(request, Message) else None
    await state.update_data(desired_delivery_time=delivery_time)

    user, _ = await async_get_or_create_user(request.from_user.id)
    cart = await async_get_cart(user)
    text, total = await generate_order_text(user, state, cart.id)

    await delete_previous_message(request, state)
    await send_message_with_state(
        request,
        text,
        state,
        reply_markup=generate_confirmation_keyboard(total),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(OrderState.waiting_for_confirmation)


@router.callback_query(F.data == "back", OrderState.waiting_for_confirmation)
async def back_from_confirmation(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к вводу времени доставки."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_delivery_time,
        "⏰ Укажите желаемое время доставки (или нажмите 'Пропустить'):",
        generate_skip_keyboard()
    )


@router.callback_query(F.data == "confirm", OrderState.waiting_for_confirmation)
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обрабатывает подтверждение заказа."""
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} подтверждает заказ.")

    data = await state.get_data()
    user, _ = await async_get_or_create_user(user_id)

    try:
        order = await async_create_order(
            user_id=user.telegram_id,
            address=data.get("address"),
            phone=data.get("phone"),
            wishes=data.get("wishes"),
            desired_delivery_time=data.get("desired_delivery_time")
        )

        items_text, total = await async_get_order_details(order.id)

        user_text = (
            f"✅ Заказ {html.bold(f'#{order.id}')} оформлен!\n\n"
            f"📍 Адрес: {html.quote(data.get('address'))}\n"
            f"📞 Телефон: {html.quote(data.get('phone'))}\n"
            f"💬 Пожелания: {html.quote(data.get('wishes')) if data.get('wishes') else 'Нет'}\n"
            f"⏰ Время доставки: {html.quote(data.get('desired_delivery_time')) if data.get('desired_delivery_time') else 'Не указано'}\n\n"
            f"🛒 Состав заказа:\n{items_text}\n\n"
            f"💵 Итого: {html.bold(f'{total} ₽')}"
        )

        await delete_previous_message(callback, state)
        await callback.message.answer(
            user_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⬅️ В меню", callback_data="main_menu")]
            ]),
            parse_mode=ParseMode.HTML
        )

        # Уведомление администратору
        if SUPPORT_TELEGRAM and SUPPORT_TELEGRAM.strip():
            try:
                admin_chat_id = int(SUPPORT_TELEGRAM)
                admin_text = (
                    f"🔔 Новый заказ #{order.id}!\n\n"
                    f"👤 Пользователь: {user.telegram_id} (@{user.username if user.username else 'Нет ника'})\n"
                    f"📞 Телефон: {data.get('phone')}\n"
                    f"📍 Адрес: {data.get('address')}\n"
                    f"💬 Пожелания: {data.get('wishes') if data.get('wishes') else 'Нет'}\n"
                    f"⏰ Время доставки: {data.get('desired_delivery_time') if data.get('desired_delivery_time') else 'Не указано'}\n\n"
                    f"🛒 Товары:\n{items_text}\n"
                    f"💵 Сумма: {total} ₽"
                )
                await bot.send_message(
                    chat_id=admin_chat_id,
                    text=admin_text,
                    parse_mode=ParseMode.HTML
                )
                logger.info(
                    f"Уведомление о заказе #{order.id} успешно отправлено администратору в чат {admin_chat_id}")
            except ValueError:
                logger.error(
                    f"Некорректный формат SUPPORT_TELEGRAM: {SUPPORT_TELEGRAM}. Ожидается числовой ID чата.")
            except Exception as e:
                logger.error(
                    f"Ошибка отправки уведомления администратору: {e}")
        else:
            logger.warning(
                "SUPPORT_TELEGRAM не указан в .env, уведомление администратору не отправлено.")

    except Exception as e:
        logger.error(
            f"Ошибка создания заказа для пользователя {user_id}: {e}", exc_info=True)
        await callback.message.answer(
            f"❌ Ошибка при оформлении заказа: {str(e)}. Пожалуйста, попробуйте снова или обратитесь в поддержку: {SUPPORT_TELEGRAM}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="⬅️ В меню", callback_data="main_menu")]
            ])
        )

    await state.clear()


@router.callback_query(F.data == "edit", OrderState.waiting_for_confirmation)
async def edit_order(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на 'Изменить'."""
    await delete_previous_message(callback, state)
    await send_message_with_state(
        callback,
        "Что вы хотите изменить?",
        state,
        reply_markup=generate_edit_choice_keyboard()
    )
    await state.set_state(OrderState.waiting_for_edit_choice)


@router.callback_query(F.data == "back_to_confirmation", OrderState.waiting_for_edit_choice)
async def back_to_confirmation(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к подтверждению заказа."""
    user, _ = await async_get_or_create_user(callback.from_user.id)
    cart = await async_get_cart(user)
    text, total = await generate_order_text(user, state, cart.id)

    await delete_previous_message(callback, state)
    await send_message_with_state(
        callback,
        text,
        state,
        reply_markup=generate_confirmation_keyboard(total),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(OrderState.waiting_for_confirmation)


@router.callback_query(F.data == "edit_address", OrderState.waiting_for_edit_choice)
async def edit_address(callback: CallbackQuery, state: FSMContext):
    """Позволяет пользователю отредактировать адрес."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_address,
        "📍 Пожалуйста, укажите новый адрес доставки:",
        generate_back_keyboard()
    )


@router.callback_query(F.data == "edit_phone", OrderState.waiting_for_edit_choice)
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    """Позволяет пользователю отредактировать номер телефона."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_phone,
        "📞 Пожалуйста, укажите ваш новый номер телефона:",
        generate_back_keyboard()
    )


@router.callback_query(F.data == "edit_wishes", OrderState.waiting_for_edit_choice)
async def edit_wishes(callback: CallbackQuery, state: FSMContext):
    """Позволяет пользователю отредактировать пожелания."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_wishes,
        "💬 Укажите новые пожелания к заказу (или нажмите 'Пропустить'):",
        generate_skip_keyboard()
    )


@router.callback_query(F.data == "edit_delivery_time", OrderState.waiting_for_edit_choice)
async def edit_delivery_time(callback: CallbackQuery, state: FSMContext):
    """Позволяет пользователю отредактировать время доставки."""
    await back_to_previous_state(
        callback,
        state,
        OrderState.waiting_for_delivery_time,
        "⏰ Укажите новое желаемое время доставки (или нажмите 'Пропустить'):",
        generate_skip_keyboard()
    )
