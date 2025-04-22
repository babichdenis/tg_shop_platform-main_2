from aiogram import Router
from .display import router as display_router
from .checkout import router as checkout_router

router = Router()
router.include_router(display_router)
router.include_router(checkout_router)

__all__ = ["router"]
