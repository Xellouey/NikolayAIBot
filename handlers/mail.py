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
    help_text = utils.get_text('mail.messages.mail_help')
    keyboard_items = [
        [types.InlineKeyboardButton(text=utils.get_text('mail.buttons.copy_json'), callback_data='copy_json_example')],
        [types.KeyboardButton(text='➡️ Пропустить'), types.KeyboardButton(text='❌ Отмена')]
    ]
    
    inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=utils.get_text('mail.buttons.copy_json'), callback_data='copy_json_example')]])
    reply_kb = types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text='➡️ Пропустить'), types.KeyboardButton(text='❌ Отмена')]], resize_keyboard=True)
    
    await message.answer(help_text, reply_markup=inline_kb)
    await message.answer('👉 Отправьте клавиатуру в формате JSON или нажмите "Пропустить":', reply_markup=reply_kb)


@router.callback_query(F.data == 'copy_json_example')
async def copy_json_example(call: types.CallbackQuery):
    """Send JSON example for easy copying"""
    await call.answer()
    
    example_json = utils.get_text('mail.messages.json_example')
    await call.message.answer(
        f'📋 <b>Пример JSON для копирования:</b>\n\n<code>{example_json}</code>\n\nНажмите на текст выше чтобы скопировать'
    )
  
    
@router.message(FSMMail.keyboard)
async def takeMailkeyboard(message: types.Message, state: FSMMail):    
    if message.text.lower() == '➡️ пропустить':
        keyboard = None
    else:
        keyboard = message.text

        try:
            keyboard = json.loads(keyboard)
        except:
            # Show error with copy button again
            inline_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text=utils.get_text('mail.buttons.copy_json'), callback_data='copy_json_example')]])
            await message.answer(
                '❌ Неверный формат JSON. Попробуйте ещё раз:',
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
