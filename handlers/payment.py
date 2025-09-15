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


# Payment router is currently unused; all payment flows are handled in handlers/shop.py
# This module keeps token wiring for future providers if needed.
