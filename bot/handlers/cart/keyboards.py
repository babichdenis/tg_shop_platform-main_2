from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.core.config import SHOW_PARENT_CATEGORY, CATEGORY_SEPARATOR, MAX_BUTTON_TEXT_LENGTH, CART_CURRENCY, PRICE_DECIMAL_PLACES


def _format_number(value) -> str:
    """Форматирует число с учётом PRICE_DECIMAL_PLACES."""
    return f"{float(value):.{PRICE_DECIMAL_PLACES}f}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезает текст до указанной длины, добавляя суффикс, если текст слишком длинный."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def generate_cart_keyboard(user, items, cart_quantity: int, cart_total, page: int = 1, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для корзины с пагинацией."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if not items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🛒 Корзина пуста", callback_data="noop")
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="📋 Перейти в каталог",
                                 callback_data="catalog"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
        ])
    else:
        formatted_total = _format_number(cart_total)

        # Пагинация
        total_items = len(items)
        total_pages = max(
            1, (total_items + items_per_page - 1) // items_per_page)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        current_items = items[start_idx:end_idx]

        # Отображаем каждый товар
        for item in current_items:
            product = item.product
            item_total = float(product.price) * \
                item.quantity  # Приводим к float
            formatted_item_total = _format_number(item_total)
            if SHOW_PARENT_CATEGORY and product.category:
                product_display = f"{product.category.name}{CATEGORY_SEPARATOR}{product.name}"
                product_display = truncate_text(
                    product_display, MAX_BUTTON_TEXT_LENGTH)
            else:
                product_display = truncate_text(
                    product.name, MAX_BUTTON_TEXT_LENGTH)
            button_text = f"{product_display} x{item.quantity} | {formatted_item_total} {CART_CURRENCY}"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data="noop"
                )
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="−", callback_data=f"decrease_item_{product.id}"),
                InlineKeyboardButton(
                    text=f"{item.quantity}", callback_data="noop"),
                InlineKeyboardButton(
                    text="+", callback_data=f"increase_item_{product.id}"),
                InlineKeyboardButton(
                    text="❌", callback_data=f"remove_item_{product.id}")
            ])

        # Пагинация (только если больше 1 страницы)
        if total_pages > 1:
            pagination = []
            if page > 1:
                pagination.append(InlineKeyboardButton(
                    text="⬅️", callback_data=f"cart_page_{page - 1}"))
            pagination.append(InlineKeyboardButton(
                text=f"{page}/{total_pages}", callback_data="noop"))
            if page < total_pages:
                pagination.append(InlineKeyboardButton(
                    text="➡️", callback_data=f"cart_page_{page + 1}"))
            keyboard.inline_keyboard.append(pagination)

        # Итоговая сумма
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Итого: {formatted_total} {CART_CURRENCY}", callback_data="noop")
        ])

        # Кнопка оформления заказа
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"✅ Оформить за {formatted_total} {CART_CURRENCY}", callback_data="checkout")
        ])

        # Кнопки "Очистить корзину" и "Назад"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🗑️ Очистить",
                                 callback_data="clear_cart"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
        ])

    return keyboard


def generate_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для пустой корзины."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Перейти в каталог",
                              callback_data="catalog")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])


def generate_back_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с кнопкой 'Назад'."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def generate_skip_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с кнопками 'Пропустить' и 'Назад'."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пропустить", callback_data="skip"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])


def generate_confirmation_keyboard(total) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для подтверждения заказа."""
    formatted_total = _format_number(total)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"Заказ на {formatted_total} {CART_CURRENCY}. Оформить?", callback_data="confirm"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="edit")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
    ])


def generate_edit_choice_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора редактирования заказа."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📍 Адрес", callback_data="edit_address"),
            InlineKeyboardButton(text="📞 Телефон", callback_data="edit_phone")
        ],
        [
            InlineKeyboardButton(text="💬 Пожелания",
                                 callback_data="edit_wishes"),
            InlineKeyboardButton(text="⏰ Время доставки",
                                 callback_data="edit_delivery_time")
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад", callback_data="back_to_confirmation")
        ]
    ])
