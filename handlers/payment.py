import asyncio
import utils
import logging
import keyboards as kb
from decimal import Decimal
from aiogram import types, Router, F, Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery
from database import user, lesson
from aiogram.fsm.context import FSMContext

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s"
)

u = user.User()
l = lesson.Lesson()
p = lesson.Purchase()
s = lesson.SystemSettings()
promo = lesson.Promocode()

payment_router = Router()

# This will be set in main file
PAYMENT_PROVIDER_TOKEN = "PROVIDER_TOKEN_PLACEHOLDER"


def set_payment_token(token):
    """Set payment provider token"""
    global PAYMENT_PROVIDER_TOKEN
    PAYMENT_PROVIDER_TOKEN = token


# For now, create simple placeholder payment handlers
@payment_router.callback_query(lambda F: F.data.startswith('pay:'))
async def create_invoice(call: types.CallbackQuery, state: FSMContext):
    """Create payment placeholder"""
    await call.answer()
    
    # For now, just show a message that payment is not configured yet
    await call.message.edit_text(
        "💳 Платежная система в разработке.\n\nПока что система готова, нужно только настроить Payment Provider Token в @BotFather.",
        reply_markup=kb.markup_main_menu()
    )


@payment_router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """Handle successful payment placeholder"""
    await message.answer(
        "✅ Платеж успешно обработан!",
        reply_markup=kb.markup_main_menu()
    )