import logging
from aiogram import Router
from aiogram.types import Message
from bot.core.config import SUBSCRIPTION_CHANNEL_ID, SUBSCRIPTION_GROUP_ID, CATALOG_ERROR
from bot.handlers.start.subscriptions import check_subscriptions
from .data import get_categories
from .keyboards import build_categories_keyboard
from .utils import get_user_from_callback

router = Router()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Загружен commands.py версии 2025-04-22")


@router.message(lambda message: message.text == "/catalog")
async def catalog_command(message: Message) -> None:
    """
    Обработчик команды /catalog для открытия каталога.
    """
    try:
        user_id = message.from_user.id
        logger.info(f"Пользователь {user_id} вызвал команду /catalog.")

        # Проверка подписки
        if SUBSCRIPTION_CHANNEL_ID or SUBSCRIPTION_GROUP_ID:
            subscription_result, message_text = await check_subscriptions(message.bot, user_id, "/catalog")
            if not subscription_result:
                await message.answer(
                    message_text,
                    disable_web_page_preview=True,
                    parse_mode="HTML"
                )
                return

        # Получаем текст, категории и общее количество страниц
        logger.debug(f"Вызов get_categories('root', 1) в /catalog")
        result = await get_categories("root", 1)
        logger.info(f"Результат get_categories в /catalog: {result}")
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
        user = await get_user_from_callback(message)

        # Формируем клавиатуру для категорий
        keyboard = await build_categories_keyboard(categories, "root", 1, total_pages, user)

        # Отправляем сообщение
        await message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /catalog: {e}")
        await message.answer("❌ Произошла ошибка при открытии каталога", parse_mode="HTML")
