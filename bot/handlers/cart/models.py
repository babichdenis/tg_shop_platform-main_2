import os
import django
from asgiref.sync import sync_to_async
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, F
from django_app.shop.models import TelegramUser, Cart, CartItem, Order, OrderItem
from bot.core.config import SHOW_PARENT_CATEGORY, CATEGORY_SEPARATOR, CART_CURRENCY, PRICE_DECIMAL_PLACES

# Проверка инициализации Django
if not django.apps.apps.ready:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "django_app.config.settings")
    django.setup()

logger = logging.getLogger(__name__)


def get_or_create_user(tg_id: int, first_name: str = None, last_name: str = None, username: str = None, language_code: str = None):
    """Получает или создаёт пользователя по Telegram ID."""
    try:
        defaults = {'is_active': True}
        if first_name:
            defaults['first_name'] = first_name
        if last_name:
            defaults['last_name'] = last_name
        if username:
            defaults['username'] = username
        if language_code:
            defaults['language_code'] = language_code

        user, created = TelegramUser.objects.get_or_create(
            telegram_id=tg_id,
            defaults=defaults
        )
        if not created and any([first_name, last_name, username, language_code]):
            update_fields = {}
            if first_name and user.first_name != first_name:
                update_fields['first_name'] = first_name
            if last_name and user.last_name != last_name:
                update_fields['last_name'] = last_name
            if username and user.username != username:
                update_fields['username'] = username
            if language_code and user.language_code != language_code:
                update_fields['language_code'] = language_code
            if update_fields:
                for field, value in update_fields.items():
                    setattr(user, field, value)
                user.save(update_fields=list(update_fields.keys()))
                logger.info(
                    f"Обновлены данные пользователя {tg_id}: {update_fields}")

        logger.info(
            f"Пользователь {tg_id} {'создан' if created else 'найден'} в базе данных.")
        return user, created
    except Exception as e:
        logger.error(
            f"Ошибка при получении/создании пользователя {tg_id}: {e}")
        raise


def get_cart(user):
    """Получает или создаёт активную корзину пользователя."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart, _ = Cart.objects.get_or_create(user=user, is_active=True)
        logger.info(
            f"Корзина ID {cart.id} найдена/создана для пользователя {user.telegram_id}.")
        return cart
    except Exception as e:
        logger.error(
            f"Ошибка при получении корзины для пользователя {user.telegram_id}: {e}")
        raise


def get_cart_items(user):
    """Получает активные элементы корзины пользователя."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        items = list(CartItem.objects.filter(
            cart__user=user,
            cart__is_active=True,
            is_active=True
        ).select_related("product").select_related("product__category"))
        logger.info(
            f"Найдено {len(items)} активных элементов в корзине пользователя {user.telegram_id}.")
        return items
    except Exception as e:
        logger.error(
            f"Ошибка при получении элементов корзины для пользователя {user.telegram_id}: {e}")
        raise


def update_cart_item_quantity(user, product_id, delta):
    """Обновляет количество товара в корзине."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart = Cart.objects.get(user=user, is_active=True)
        item = CartItem.objects.filter(
            cart=cart, product_id=product_id, is_active=True).first()
        if item:
            new_quantity = item.quantity + delta
            if new_quantity <= 0:
                item.is_active = False
                item.save()
                logger.info(
                    f"Товар {product_id} удалён из корзины ID {cart.id} (количество стало 0).")
            else:
                item.quantity = new_quantity
                item.save()
                logger.info(
                    f"Количество товара {product_id} в корзине ID {cart.id} обновлено до {new_quantity}.")
            if not CartItem.objects.filter(cart=cart, is_active=True).exists():
                cart.is_active = False
                cart.save()
                logger.info(
                    f"Корзина ID {cart.id} стала неактивной, так как все элементы удалены.")
    except ObjectDoesNotExist:
        logger.warning(
            f"Корзина или товар {product_id} не найдены для пользователя {user.telegram_id}.")
    except Exception as e:
        logger.error(
            f"Ошибка при обновлении количества товара {product_id} для пользователя {user.telegram_id}: {e}")
        raise


def remove_item_from_cart(user, product_id):
    """Удаляет товар из корзины."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart = Cart.objects.get(user=user, is_active=True)
        items = CartItem.objects.filter(
            cart=cart, product_id=product_id, is_active=True)
        for item in items:
            item.is_active = False
            item.save()
        logger.info(f"Товар {product_id} удалён из корзины ID {cart.id}.")
        if not CartItem.objects.filter(cart=cart, is_active=True).exists():
            cart.is_active = False
            cart.save()
            logger.info(
                f"Корзина ID {cart.id} стала неактивной, так как все элементы удалены.")
    except ObjectDoesNotExist:
        logger.warning(
            f"Корзина или товар {product_id} не найдены для пользователя {user.telegram_id}.")
    except Exception as e:
        logger.error(
            f"Ошибка при удалении товара {product_id} из корзины пользователя {user.telegram_id}: {e}")
        raise


def clear_cart(user):
    """Очищает корзину пользователя."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart = Cart.objects.get(user=user, is_active=True)
        CartItem.objects.filter(
            cart=cart, is_active=True).update(is_active=False)
        cart.is_active = False
        cart.save()
        logger.info(
            f"Корзина ID {cart.id} очищена для пользователя {user.telegram_id}.")
    except ObjectDoesNotExist:
        logger.warning(
            f"Активная корзина не найдена для пользователя {user.telegram_id}.")
    except Exception as e:
        logger.error(
            f"Ошибка при очистке корзины пользователя {user.telegram_id}: {e}")
        raise


def create_order(user_id, address, phone, wishes=None, desired_delivery_time=None):
    """Создаёт заказ на основе активной корзины пользователя."""
    try:
        user = TelegramUser.objects.get(telegram_id=user_id)
        cart = Cart.objects.get(user=user, is_active=True)

        total = cart.items.filter(is_active=True).aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0

        order = Order.objects.create(
            user=user,
            address=address,
            phone=phone,
            wishes=wishes,
            desired_delivery_time=desired_delivery_time,
            total=total
        )

        for cart_item in cart.items.filter(is_active=True):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity
            )

        cart.is_active = False
        cart.save()

        logger.info(
            f"Заказ #{order.id} создан для пользователя {user_id} на сумму {total} ₽.")
        return order
    except ObjectDoesNotExist as e:
        logger.error(
            f"Ошибка при создании заказа: пользователь {user_id} или корзина не найдены: {e}")
        raise
    except Exception as e:
        logger.error(
            f"Ошибка при создании заказа для пользователя {user_id}: {e}")
        raise


def get_cart_quantity(user):
    """Возвращает общее количество товаров в активной корзине."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart = get_cart(user)
        quantity = cart.items.filter(is_active=True).aggregate(
            total=Sum('quantity'))['total'] or 0
        logger.info(f"Количество товаров в корзине ID {cart.id}: {quantity}.")
        return quantity
    except Exception as e:
        logger.error(
            f"Ошибка при подсчёте количества товаров для пользователя {user.telegram_id}: {e}")
        return 0


def get_cart_total(user):
    """Возвращает общую сумму активной корзины."""
    if not isinstance(user, TelegramUser):
        raise TypeError(f"Ожидается объект TelegramUser, получен {type(user)}")
    try:
        cart = get_cart(user)
        total = cart.items.filter(is_active=True).aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        logger.info(f"Общая сумма корзины ID {cart.id}: {total} ₽.")
        return total
    except Exception as e:
        logger.error(
            f"Ошибка при подсчёте суммы корзины для пользователя {user.telegram_id}: {e}")
        return 0


def get_cart_details(cart_id):
    """Возвращает детали корзины: текст, сумму и фото первого товара."""
    try:
        cart = Cart.objects.get(id=cart_id)
        items = CartItem.objects.filter(
            cart=cart, is_active=True).select_related('product').select_related('product__category')
        items_text_lines = []
        for item in items:
            product = item.product
            # Приводим к float для форматирования
            item_total = float(product.price) * item.quantity
            formatted_item_total = f"{item_total:.{PRICE_DECIMAL_PLACES}f}"
            if SHOW_PARENT_CATEGORY and product.category:
                product_display = f"{product.category.name}{CATEGORY_SEPARATOR}{product.name}"
            else:
                product_display = product.name
            items_text_lines.append(
                f"{product_display}, {item.quantity} шт., {formatted_item_total}{CART_CURRENCY}"
            )
        items_text = "\n".join(items_text_lines)
        total = sum(float(item.product.price) *
                    item.quantity for item in items)  # Приводим к float
        formatted_total = f"{total:.{PRICE_DECIMAL_PLACES}f}"
        first_item_photo = items[0].product.photo.url if items and items[0].product.photo else None
        logger.info(
            f"Детали корзины ID {cart_id}: {len(items)} товаров, итого {formatted_total} ₽.")
        return items_text, total, first_item_photo
    except ObjectDoesNotExist:
        logger.error(f"Корзина ID {cart_id} не найдена.")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении деталей корзины ID {cart_id}: {e}")
        raise


def get_order_details(order_id):
    """Возвращает детали заказа: текст и сумму."""
    try:
        items = OrderItem.objects.filter(
            order_id=order_id).select_related('product').select_related('product__category')
        items_text_lines = []
        for item in items:
            product = item.product
            item_total = float(product.price) * \
                item.quantity  # Приводим к float
            formatted_item_total = f"{item_total:.{PRICE_DECIMAL_PLACES}f}"
            if SHOW_PARENT_CATEGORY and product.category:
                product_display = f"{product.category.name}{CATEGORY_SEPARATOR}{product.name}"
            else:
                product_display = product.name
            items_text_lines.append(
                f"{product_display}, {item.quantity} шт., {formatted_item_total}{CART_CURRENCY}"
            )
        items_text = "\n".join(items_text_lines)
        total = sum(float(item.product.price) *
                    item.quantity for item in items)  # Приводим к float
        logger.info(
            f"Детали заказа #{order_id}: {len(items)} товаров, итого {total} ₽.")
        return items_text, total
    except Exception as e:
        logger.error(f"Ошибка при получении деталей заказа #{order_id}: {e}")
        raise

# Асинхронные обёртки


@sync_to_async
def async_get_or_create_user(tg_id: int, first_name: str = None, last_name: str = None, username: str = None, language_code: str = None):
    return get_or_create_user(tg_id, first_name, last_name, username, language_code)


@sync_to_async
def async_get_cart(user):
    return get_cart(user)


@sync_to_async
def async_get_cart_items(user):
    return get_cart_items(user)


@sync_to_async
def async_update_cart_item_quantity(user, product_id, delta):
    return update_cart_item_quantity(user, product_id, delta)


@sync_to_async
def async_remove_item_from_cart(user, product_id):
    return remove_item_from_cart(user, product_id)


@sync_to_async
def async_clear_cart(user):
    return clear_cart(user)


@sync_to_async
def async_create_order(user_id, address, phone, wishes=None, desired_delivery_time=None):
    return create_order(user_id, address, phone, wishes, desired_delivery_time)


@sync_to_async
def async_get_cart_quantity(user):
    return get_cart_quantity(user)


@sync_to_async
def async_get_cart_total(user):
    return get_cart_total(user)


@sync_to_async
def async_get_cart_details(cart_id):
    return get_cart_details(cart_id)


@sync_to_async
def async_get_order_details(order_id):
    return get_order_details(order_id)
