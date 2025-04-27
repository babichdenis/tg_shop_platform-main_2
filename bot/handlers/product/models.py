import logging
from django_app.shop.models import Product, Cart, CartItem
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
logger.info("Загружен product/models.py версии 2025-04-23-3")


async def get_product_by_id(product_id: int):
    """Получает продукт по ID."""
    try:
        product = await sync_to_async(Product.objects.get)(id=product_id, is_active=True)
        logger.info(f"Получен продукт: {product.name} (ID: {product.id})")
        return product
    except Product.DoesNotExist:
        logger.error(f"Продукт с ID {product_id} не найден")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении продукта ID {product_id}: {e}")
        raise


async def get_or_create_cart(user):
    """Получает или создаёт корзину для пользователя."""
    try:
        cart, created = await sync_to_async(Cart.objects.get_or_create)(user=user, is_active=True)
        logger.info(
            f"Корзина ID {cart.id} {'создана' if created else 'найдена'} для пользователя {user.telegram_id}")
        return cart, created
    except Exception as e:
        logger.error(
            f"Ошибка при получении/создании корзины для пользователя {user.telegram_id}: {e}")
        raise


@sync_to_async
def sync_update_cart_item(cart, product, quantity):
    """Синхронная функция для обновления элемента корзины."""
    try:
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            is_active=True,
            defaults={'quantity': quantity}
        )
        if not created:
            # Увеличиваем количество вместо перезаписи
            old_quantity = item.quantity
            item.quantity += quantity
            item.save()
            logger.info(
                f"Элемент корзины ID {item.id} обновлён для продукта ID {product.id}, количество увеличено с {old_quantity} до {item.quantity}")
        else:
            logger.info(
                f"Элемент корзины ID {item.id} создан для продукта ID {product.id} с количеством {quantity}")
        return item
    except Exception as e:
        logger.error(
            f"Ошибка при обновлении элемента корзины для продукта ID {product.id}: {e}")
        raise


async def update_cart_item(cart, product, quantity):
    """Обновляет элемент корзины."""
    return await sync_update_cart_item(cart, product, quantity)
