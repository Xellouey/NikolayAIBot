import config
import logging
import utils
import os
import json
import re
import keyboards as kb
from message_utils import send_msg
from database import user, lesson
from datetime import datetime
from aiogram import Bot, types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from states import FSMAdminRights, FSMLesson, FSMSettings, FSMPromocode, FSMTranslations
from typing import Optional

# Добавляем импорт глобального bot из bot_instance
from bot_instance import bot
from localization import get_text

router = Router()

u = user.User()
l = lesson.Lesson()
p = lesson.Purchase()
s = lesson.SystemSettings()
promo = lesson.Promocode()

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
)


@router.message(Command('admin'))
async def admin(message: types.Message, state: FSMContext):
    data_admins = utils.get_admins()
    
    if(await state.get_state() != None):
        await state.clear()

    if(message.from_user.id not in config.ADMINS and message.from_user.id not in data_admins):
        await message.answer('⚠️ Ошибка доступа')    
        return
    
    if(message.from_user.id in config.ADMINS):
        text_rights = "Вы обладаетe всиими правами главного администратора! 🔑"
    elif(message.from_user.id in data_admins):
        text_rights = "Вы обладаетe правами администратора! 🔑"
        
    await message.answer(f"""
## Добро пожаловать, Администратор! 👽

Ваше имя: <b>{message.from_user.full_name}</b>
ID пользователя: <b>{message.from_user.id}</b>

{text_rights}
""", parse_mode='html', reply_markup=kb.markup_admin(message.from_user.id))
    
    
@router.callback_query(F.data == 'backAdmin')
async def backAdmin(call: types.CallbackQuery, state: FSMContext):
    data_admins = utils.get_admins()

    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')    
        return
    
    if(call.from_user.id in config.ADMINS):
        text_rights = "Вы обладаетe всиими правами главного администратора! 🔑"
    elif(call.from_user.id in data_admins):
        text_rights = "Вы обладаетe правами администратора! 🔑"
        
    await call.answer()
    await call.message.edit_text(f"""
## Добро пожаловать, Администратор! 👽

Ваше имя: <b>{call.from_user.full_name}</b>
ID пользователя: <b>{call.from_user.id}</b>

{text_rights}
""", parse_mode='html', reply_markup=kb.markup_admin(call.from_user.id))


@router.message(F.text == '❌ Отмена')
async def cancel(message: types.Message, state: FSMContext):
    if await state.get_state() != None:
        await state.clear()
        
    data_admins = utils.get_admins()

    if message.from_user.id in config.ADMINS or message.from_user.id in data_admins:    
        await message.answer('❌ Отменено', reply_markup=kb.markup_remove())
        await message.answer(' ', reply_markup=kb.markup_remove())
        await admin(message, state)
    
    
@router.callback_query(F.data == 'adminRights')
async def adminRights(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMAdminRights.user)
    
    await call.answer()
    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data='cancel_admin_rights')]
    ])
    await call.message.edit_text("👉 Введите ID пользователя:", reply_markup=cancel_markup)
    
    
@router.callback_query(F.data == 'cancel_admin_rights')
async def cancel_admin_rights(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    data_admins = utils.get_admins()
    
    if call.from_user.id in config.ADMINS:
        text_rights = "Вы обладаетe всиими правами главного администратора! 🔑"
    elif call.from_user.id in data_admins:
        text_rights = "Вы обладаетe правами администратора! 🔑"
        
    await call.answer("❌ Отменено")
    await call.message.edit_text(f"""
## Добро пожаловать, Администратор! 👽

Ваше имя: <b>{call.from_user.full_name}</b>
ID пользователя: <b>{call.from_user.id}</b>

{text_rights}
""", parse_mode='html', reply_markup=kb.markup_admin(call.from_user.id))


@router.message(FSMAdminRights.user)
async def userAdminRights(message: types.Message, state: FSMAdminRights):
    data_admins = utils.get_admins()
    
    user = message.text
    if user and user.isdigit():
        user_id = int(user)
        
        if user_id not in data_admins:
            data_admins.append(user_id)
            await message.answer(f"✅ Пользователь ID: <code>{user}</code> успешно <b>добавлен</b>", parse_mode='html', reply_markup=kb.markup_remove())
        elif user_id in data_admins:
            data_admins.remove(user_id)
            await message.answer(f"✅ Пользователь ID: <code>{user}</code> успешно <b>удален</b>", parse_mode='html', reply_markup=kb.markup_remove())
            
        utils.update_admins(data_admins)
        return
    
    else:
        cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data='cancel_admin_rights')]
        ])
        await message.answer("👉 Введите корректный ID пользователя:", reply_markup=cancel_markup)


# ===== NEW SHOP ADMIN HANDLERS =====

@router.callback_query(F.data == 'lessons_mgmt')
async def lessons_management(call: types.CallbackQuery, state: FSMContext):
    """Lessons management menu"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')
        return
    
    await call.answer()
    await call.message.edit_text(
        '📚 Управление уроками',
        reply_markup=kb.markup_lessons_management()
    )


@router.callback_query(F.data == 'settings')
async def settings_menu(call: types.CallbackQuery, state: FSMContext):
    """Settings menu"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    await call.message.edit_text(
        '⛙️ Настройки',
        reply_markup=kb.markup_admin_settings()
    )


@router.callback_query(F.data == 'add_lesson')
async def add_lesson_start(call: types.CallbackQuery, state: FSMContext):
    """Start adding new lesson"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await state.set_state(FSMLesson.title)
    await call.answer()
    await call.message.edit_text(
        '👉 Введите название урока:',
        reply_markup=None
    )


# End of file - other handlers should be in separate files
