from aiogram import Router
from .commands import router as commands_router
from .callbacks import router as callbacks_router

router = Router()
router.include_router(commands_router)
router.include_router(callbacks_router)
