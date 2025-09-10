import asyncio
import config
import json
import logging
import utils
import keyboards as kb
from datetime import datetime as dt, timedelta
from aiogram import types, Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import FSMMail
from database import mail
from mail import mailing
from localization import get_text


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)

router = Router()
bot = Bot(config.TOKEN)
m = mail.Mail()


@router.callback_query(F.data == 'mail')
async def mailingFirstLine(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMMail.date_mail)
    
    await call.message.answer('👉 Отправьте время в формате дд.мм.гггг чч:мм или нажмите кнопку ➡️ Пропустить', reply_markup=kb.markup_pass())
    await call.answer()
    
    
@router.message(FSMMail.date_mail)
async def takeMailDatetime(message: types.Message, state: FSMMail):
    if message.text == '➡️ Пропустить':
        # Для немедленной отправки - время на 10 секунд в прошлом
        date_mail = dt.now() - timedelta(seconds=10)
        logging.info(f"🚀 Immediate send scheduled for {date_mail.strftime('%d.%m.%Y %H:%M:%S')}")
    else:
        try:
            date_mail = dt.strptime(message.text, '%d.%m.%Y %H:%M')
            logging.info(f"📅 Scheduled send for {date_mail.strftime('%d.%m.%Y %H:%M:%S')}")
        except:
            await message.answer('👉 Отправьте корректное время в формате дд.мм.гггг чч:мм или нажмите кнопку ➡️ Пропустить', reply_markup=kb.markup_pass())
            return 
        
    await state.update_data(date_mail=date_mail)
    await state.set_state(FSMMail.message)
    
    await message.answer('👉 Отправьте ваше сообщение:', reply_markup=kb.markup_cancel())

    
@router.message(FSMMail.message)
async def takeMailMessage(message: types.Message, state: FSMMail):
    message_id = message.message_id
    from_id = message.from_user.id
    
    await state.update_data(message_id=message_id, from_id=from_id)
    await state.set_state(FSMMail.keyboard)
    
    # Send help message with JSON example and copy button
    help_text = get_text('mail.messages.mail_help')
    # Кнопки для копирования конкретного примера JSON
    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=get_text('mail.buttons.copy_inline'), callback_data='copy_json_inline')],
        [types.InlineKeyboardButton(text=get_text('mail.buttons.copy_callback'), callback_data='copy_json_callback')]
    ])
    reply_kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='➡️ Пропустить'), types.KeyboardButton(text='❌ Отмена')]], resize_keyboard=True)
    
    await message.answer(help_text, reply_markup=inline_kb)
    await message.answer('👉 Отправьте клавиатуру в формате JSON или нажмите "Пропустить":', reply_markup=reply_kb)


@router.callback_query(F.data == 'copy_json_inline')
async def copy_json_inline(call: types.CallbackQuery):
    """Send INLINE JSON example for easy copying"""
    await call.answer()
    example_json = get_text('mail.messages.json_example_inline')
    await call.message.answer(
        f'📋 <b>Inline-клавиатура (JSON):</b>\n\n<code>{example_json}</code>\n\nНажмите на текст выше чтобы скопировать'
    )

@router.callback_query(F.data == 'copy_json_callback')
async def copy_json_callback(call: types.CallbackQuery):
    """Send callback buttons JSON example for easy copying"""
    await call.answer()
    example_json = get_text('mail.messages.json_example_callback')
    await call.message.answer(
        f'🔘 <b>Inline-клавиатура с callback (JSON):</b>\n\n<code>{example_json}</code>\n\nНажмите на текст выше чтобы скопировать'
    )
  
    
@router.message(FSMMail.keyboard)
async def takeMailkeyboard(message: types.Message, state: FSMMail):    
    if message.text.lower() == '➡️ пропустить':
        keyboard = None
    else:
        text = message.text.strip()
        # Поддержка двух форматов в одном сообщении: если пользователь прислал 2 блока JSON подряд,
        # вытащим первый валидный JSON из текста.
        keyboard = None
        try:
            # Попытка 1: целиком как JSON
            keyboard = json.loads(text)
        except Exception:
            # Попытка 2: найти первый валидный JSON-объект в тексте
            import re
            candidates = re.findall(r"\{[\s\S]*?\}", text)
            for c in candidates:
                try:
                    keyboard = json.loads(c)
                    break
                except Exception:
                    continue
        if keyboard is None:
            # Показать две кнопки для примеров снова
            inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=get_text('mail.buttons.copy_inline'), callback_data='copy_json_inline')],
                [types.InlineKeyboardButton(text=get_text('mail.buttons.copy_callback'), callback_data='copy_json_callback')]
            ])
            await message.answer(
                '❌ Неверный формат JSON. Попробуйте ещё раз или скопируйте пример выше:',
                reply_markup=inline_kb
            )
            return

    await state.update_data(keyboard=keyboard)
    await state.set_state(FSMMail.confirm)
    
    stateData = await state.get_data()
    message_id = stateData['message_id']
    from_id = stateData['from_id']
    
    await bot.copy_message(message.from_user.id, from_id, message_id, reply_markup=kb.markup_custom(keyboard))
    await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
    
    
@router.message(FSMMail.confirm)
async def takeMailConfirm(message: types.Message, state: FSMContext):
    try:
        if message.text.lower() != '✅ да':
            await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
            return
    except:
        await message.answer('👉 Вы уверены, что хотите разослать это сообщение?', reply_markup=kb.markup_confirm())
        return

    stateData = await state.get_data()
    date_mail = stateData['date_mail']
    message_id = stateData['message_id']
    from_id = stateData['from_id']
    keyboard = stateData['keyboard']
    await state.clear()

    date_mail_str = date_mail.strftime('%d.%m.%Y %H:%M')

    await m.create_mail(date_mail, message_id, from_id, keyboard)
    
    if date_mail < dt.now():
        await mailing(message_id, from_id, keyboard)
        await message.answer('✅ Рассылка отправлена мгновенно', reply_markup=kb.markup_remove())
    else:
        await message.answer(f'✅ Рассылка будет запущена {date_mail_str}', reply_markup=kb.markup_remove())
