import config
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode='html'))