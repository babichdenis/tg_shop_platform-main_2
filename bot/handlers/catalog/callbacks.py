import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async
from bot.core.config import (
    SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID,
    PRODUCT_NOT_FOUND, CATALOG_MESSAGE, CATALOG_ERROR
)
from bot.handlers.start.subscriptions import check_subscriptions
from .breadcrumbs import get_category_path
from .data import get_categories, get_products_page
from .keyboards import build_categories_keyboard, build_products_keyboard
from .utils import safe_edit_message, get_user_from_callback

router = Router()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Загружен callbacks.py версии 2025-04-22")


@router.callback_query(F.data.startswith("cat_page_"))
async def categories_pagination(callback: CallbackQuery) -> None:
    """
    Обработчик для отображения категорий с пагинацией.
    """
    try:
        # Разбираем callback_data (формат: "cat_page_<parent_id>_<page>")
        parts = callback.data.split("_")
        if len(parts) != 4:
            raise ValueError(f"Неверный формат callback_data: {callback.data}")

        parent_id = parts[2]
        page = int(parts[3])
        user_id = callback.from_user.id
        logger.info(
            f"Пользователь {user_id} запросил категории, parent_id={parent_id}, страница {page}.")

        # Получаем текст, категории и общее количество страниц
        logger.debug(f"Вызов get_categories('{parent_id}', {page}) в cat_page")
        result = await get_categories(parent_id, page)
        logger.info(f"Результат get_categories в cat_page: {result}")
        if not isinstance(result, tuple):
            logger.error(
                f"get_categories вернул не кортеж: {type(result)}: {result}")
            raise ValueError(
                f"get_categories вернул не кортеж: {type(result)}")
        text, categories, total_pages = result
        if not isinstance(text, str):
            logger.error(
                f"get_categories вернул не строку в text: {type(text)}: {text}")
            text = CATALOG_ERROR

        # Получаем данные пользователя
        user = await get_user_from_callback(callback)

        # Проверяем, есть ли подкатегории
        if parent_id != "root":
            _, subcategories, _ = await get_categories(parent_id, 1)
            if not subcategories:
                # Если подкатегорий нет, показываем товары
                products, total_count = await get_products_page(int(parent_id), page)
                if products:
                    breadcrumb = await sync_to_async(get_category_path)(parent_id)
                    if not isinstance(breadcrumb, str):
                        logger.error(
                            f"get_category_path вернул не строку: {type(breadcrumb)}: {breadcrumb}")
                        breadcrumb = "🛍️ Каталог"
                    kb = await build_products_keyboard(int(parent_id), page, products, total_count, user)
                    await safe_edit_message(callback, f"{breadcrumb}\n\n{CATALOG_MESSAGE}", kb)
                    await callback.answer()
                    return
                else:
                    breadcrumb = await sync_to_async(get_category_path)(parent_id)
                    if not isinstance(breadcrumb, str):
                        logger.error(
                            f"get_category_path вернул не строку: {type(breadcrumb)}: {breadcrumb}")
                        breadcrumb = "🛍️ Каталог"
                    text = f"{breadcrumb}\n\n{PRODUCT_NOT_FOUND}"

        # Формируем клавиатуру для категорий
        keyboard = await build_categories_keyboard(categories, parent_id, page, total_pages, user)

        # Обновляем сообщение
        await safe_edit_message(callback, text, keyboard)

    except ValueError as e:
        logger.error(f"Ошибка формата данных: {e}")
        await callback.answer("❌ Неверный формат данных", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отображении категорий: {str(e)}")
        await callback.answer("❌ Произошла ошибка при отображении категорий", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data.startswith("prod_page_"))
async def products_pagination(callback: CallbackQuery) -> None:
    """
    Обработчик пагинации товаров.
    """
    try:
        parts = callback.data.split("_")
        if len(parts) != 4:
            raise ValueError(f"Неверный формат callback_data: {callback.data}")

        category_id = int(parts[2])
        page = int(parts[3])
        logger.info(
            f"Пагинация товаров для category_id {category_id}, страница {page}.")

        # Получаем данные пользователя
        user = await get_user_from_callback(callback)

        # Получаем товары
        products, total_count = await get_products_page(category_id, page)

        if not products:
            logger.warning(
                f"Товары не найдены для категории ID {category_id}, страница {page}.")
            breadcrumb = await sync_to_async(get_category_path)(str(category_id))
            if not isinstance(breadcrumb, str):
                logger.error(
                    f"get_category_path вернул не строку: {type(breadcrumb)}: {breadcrumb}")
                breadcrumb = "🛍️ Каталог"
            await safe_edit_message(callback, f"{breadcrumb}\n\n{PRODUCT_NOT_FOUND}", None)
            await callback.answer()
            return

        # Формируем клавиатуру для товаров
        breadcrumb = await sync_to_async(get_category_path)(str(category_id))
        if not isinstance(breadcrumb, str):
            logger.error(
                f"get_category_path вернул не строку: {type(breadcrumb)}: {breadcrumb}")
            breadcrumb = "🛍️ Каталог"
        kb = await build_products_keyboard(category_id, page, products, total_count, user)
        await safe_edit_message(callback, f"{breadcrumb}\n\n{CATALOG_MESSAGE}", kb)

    except ValueError as e:
        logger.error(f"Ошибка формата данных: {e}")
        await callback.answer("❌ Неверный формат данных", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при пагинации товаров: {str(e)}")
        await callback.answer("❌ Произошла ошибка при отображении товаров", show_alert=True)
    finally:
        await callback.answer()


@router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery) -> None:
    """
    Обработчик нажатия кнопки 'Каталог'.
    """
    try:
        user_id = callback.from_user.id
        logger.info(f"Пользователь {user_id} нажал кнопку 'Каталог'.")

        # Проверка подписки
        if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
            subscription_result, message_text = await check_subscriptions(callback.bot, user_id, "catalog")
            if not subscription_result:
                try:
                    await callback.message.edit_text(
                        message_text,
                        disable_web_page_preview=True,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest:
                    await callback.message.answer(
                        message_text,
                        disable_web_page_preview=True,
                        parse_mode="HTML"
                    )
                await callback.answer()
                return

        # Получаем текст, категории и общее количество страниц
        logger.debug(f"Вызов get_categories('root', 1) в catalog_callback")
        result = await get_categories("root", 1)
        logger.info(f"Результат get_categories в catalog_callback: {result}")
        if not isinstance(result, tuple):
            logger.error(
                f"get_categories вернул не кортеж: {type(result)}: {result}")
            raise ValueError(
                f"get_categories вернул не кортеж: {type(result)}")
        text, categories, total_pages = result
        if not isinstance(text, str):
            logger.error(
                f"get_categories вернул не строку в text: {type(text)}: {text}")
            text = CATALOG_ERROR

        # Получаем данные пользователя
        user = await get_user_from_callback(callback)

        # Формируем клавиатуру для категорий
        keyboard = await build_categories_keyboard(categories, "root", 1, total_pages, user)

        # Обновляем сообщение
        await safe_edit_message(callback, text, keyboard)

    except Exception as e:
        logger.error(f"Ошибка при выполнении callback 'catalog': {e}")
        await callback.answer("❌ Произошла ошибка при открытии каталога", show_alert=True)
    finally:
        await callback.answer()
