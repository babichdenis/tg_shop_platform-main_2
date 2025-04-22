import logging
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.handlers.cart.models import async_get_or_create_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info("Загружен utils.py версии 2025-04-22")


async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """
    Безопасное редактирование сообщения.
    """
    logger.debug(f"Вызов safe_edit_message с text типа {type(text)}")
    if not isinstance(text, str):
        logger.error(
            f"Ожидалась строка для текста сообщения, получен {type(text)}: {text}")
        text = "❌ Ошибка отображения каталога. Пожалуйста, попробуйте снова."

    try:
        await callback.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        logger.debug(f"Сообщение успешно отредактировано: {text[:50]}...")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug(
                f"Сообщение не изменено (уже актуально): {text[:50]}...")
        else:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            try:
                await callback.message.delete()
                await callback.message.answer(
                    text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as delete_error:
                logger.error(
                    f"Ошибка при удалении и отправке нового сообщения: {delete_error}")
                await callback.message.answer(
                    text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
    except Exception as e:
        logger.error(f"Неизвестная ошибка при редактировании сообщения: {e}")
        try:
            await callback.message.delete()
            await callback.message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as delete_error:
            logger.error(
                f"Ошибка при удалении и отправке нового сообщения: {delete_error}")
            await callback.message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )


async def get_user_from_callback(callback: CallbackQuery):
    """
    Получает или создаёт пользователя на основе данных callback.
    """
    user_id = callback.from_user.id
    user, _ = await async_get_or_create_user(
        tg_id=user_id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        username=callback.from_user.username,
        language_code=callback.from_user.language_code
    )
    logger.debug(f"Пользователь {user_id} получен/создан")
    return user
