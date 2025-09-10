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
from states import FSMAdminRights, FSMEditor, FSMCreateStep, FSMLesson, FSMSettings, FSMPromocode, FSMTranslations
from typing import Optional

# Добавляем импорт глобального bot из bot_instance
from bot_instance import bot

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
        # Remove return to allow cancel handler to process if needed
        
@router.callback_query(F.data == 'editor')
async def editor(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    
@router.callback_query(lambda F: 'edit:' in F.data)
async def edit(call: types.CallbackQuery, state: FSMContext):
    key = call.data.split(':')[1]
    
    await state.set_state(FSMEditor.action)
    await state.update_data(key=key)
    
    steps = utils.get_steps()
    step = steps[key]
    
    # Send the step message using global bot
    if step['content_type'] == 'text':
        await bot.send_message(
            chat_id=call.message.chat.id,
            text=step['text'],
            reply_markup=None,
            parse_mode='HTML'
        )
    else:
        # For non-text, fallback to text or handle accordingly
        fallback_text = step['caption'] or step['text'] or "Шаг недоступен"
        await bot.send_message(
            chat_id=call.message.chat.id,
            text=fallback_text,
            reply_markup=None,
            parse_mode='HTML'
        )
    
    if(key in ('join', 'start')):
        disable_default = True
    else:
        disable_default = False
    
    await call.answer()
    await call.message.delete()
    await call.message.answer('👉 Что вы хотите изменить:', reply_markup=kb.markup_edit(disable_default=disable_default))
    

@router.message(FSMEditor.action)
async def actionEditor(message: types.Message, state: FSMEditor):
    action = message.text
    
    await state.set_state(FSMEditor.value)
    
    if(action == '👟 Шаг'):
        await state.update_data(action='step')
        await message.answer('👉 Отправьте новое сообщение:', reply_markup=kb.markup_cancel())
    
    elif(action == '🖌 Позицию'):
        await state.update_data(action='position')
        await message.answer('👉 Отправьте новую позицию для переноса шага:', reply_markup=kb.markup_cancel())
    
    elif(action == '⏳ Задержку'):
        await state.update_data(action='delay')
        await message.answer('👉 Отправьте новую задержку для шага:', reply_markup=kb.markup_pass())
    
    elif(action == '🔗 Кнопки'):
        await state.update_data(action='keyboard')
        await message.answer('👉 Отправьте новые кнопки для шага в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', reply_markup=kb.markup_pass())
    
    elif(action == '⛔️ Удалить'):
        await state.update_data(action='delete')
        await message.answer('👉 Отправьте слово <code>Подтвердить</code> для удаления шага:', reply_markup=kb.markup_cancel())
    
    
@router.message(FSMEditor.value)
async def msgEditor(message: types.Message, state: FSMEditor):
    if message.content_type not in ('text', 'document', 'photo', 'video', 'audio', 'video_note', 'voice'):
        await message.answer('👉 Отправьте новое корректное сообщение:', reply_markup=kb.markup_cancel())
        return
    
    try:
        state_data = await state.get_data()
        if not state_data or 'key' not in state_data or 'action' not in state_data:
            await message.answer('❌ Ошибка: некорректное состояние. Попробуйте сначала.', reply_markup=kb.markup_editor())
            await state.clear()
            return
            
        key = state_data['key']
        action = state_data['action']
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error getting state data in msgEditor: {e}")
        await message.answer('❌ Ошибка получения данных состояния. Попробуйте сначала.', reply_markup=kb.markup_editor())
        await state.clear()
        return
    
    steps = utils.get_steps()
    
    if action == 'step':
        content_type = message.content_type
        text = message.text
        caption = message.caption  
        
        if content_type != 'text':
            if message.caption_entities != None:
                custom_entities = []
                for entity in message.caption_entities:
                    if entity.type == 'custom_emoji':
                        continue
                    if entity.custom_emoji_id != None:
                        continue
                    
                    custom_entities.append(types.MessageEntity(type=entity.type, offset=entity.offset, length=entity.length, url=entity.url, user=entity.user, language=entity.language))
                
                msg_caption = await message.answer(text=caption, entities=custom_entities, parse_mode=None)
                await msg_caption.delete()
                caption = msg_caption.html_text
        
        if content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif content_type == 'document':
            file_id = message.document.file_id
        elif content_type == 'video':
            file_id = message.video.file_id
        elif content_type == 'audio':
            file_id = message.audio.file_id
        elif content_type == 'video_note':
            file_id = message.video_note.file_id
        elif content_type == 'voice':
            file_id = message.voice.file_id
        else:
            file_id = None
        
        steps[key]["content_type"] = content_type
        steps[key]["text"] = text
        steps[key]["caption"] = caption
        steps[key]["file_id"] = file_id
        utils.update_steps(steps)
        
        await message.answer('✅ Шаг успешно обновлен', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
        
    elif action == 'position':
        position = message.text
        
        try:
            position = int(position)
            if position < 1:
                raise
        except:
            await message.answer('👉 Отправьте новую корректную позицию:', reply_markup=kb.markup_cancel())
            return
        
        new_steps = utils.move_dict_item(steps, key, position + 1)
        utils.update_steps(new_steps)
        
        await message.answer('✅ Позиция шага успешно изменена', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'delay':
        delay = message.text
        
        if delay.lower() == '➡️ пропустить':
            delay = 0
        else:
            try:
                delay = int(delay)
                if delay < 1:
                    raise
            except:
                await message.answer('👉 Отправьте новую корректную задержку:', reply_markup=kb.markup_cancel())
                return
            
        steps[key]['delay'] = delay
        utils.update_steps(steps)
        
        await message.answer('✅ Задержка шага успешно изменена', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'keyboard':
        keyboard = message.text

        if message.text.lower() == '➡️ пропустить':
            keyboard = None
        else:
            keyboard = message.text

            try:
                keyboard = json.loads(keyboard)
            except:
                await message.answer('👉 Отправьте корректные кнопки для шага в формате JSON: [{"Название": "ссылка"}, {"Название": "ссылка"}], например <code>[{"Google": "google.com"}, {"Yandex": "yandex.ru"}]</code>', parse_mode='html', reply_markup=kb.markup_pass())
                return
            
        steps[key]['keyboard'] = keyboard
        utils.update_steps(steps)
        
        await message.answer('✅ Кнопки шага успешно изменены', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    elif action == 'delete':
        if message.text != 'Подтвердить':
            await message.answer('👉 Отправьте слово <code>Подтвердить</code> для удаления шага:', reply_markup=kb.markup_cancel())
            return
        
        new_steps = utils.remove_dict_item(steps, key)
        utils.update_steps(new_steps)
        
        await message.answer('✅ Шаг успешно удалён', reply_markup=kb.markup_remove())
        await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())
    
    
@router.callback_query(F.data == 'createStep')
async def createStep(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(FSMCreateStep.step)
    
    await call.answer()
    await call.message.answer('👉 Отправьте сообщение для нового шага:', reply_markup=kb.markup_cancel())
    
    
@router.message(FSMCreateStep.step)
async def stepCreate(message: types.Message, state: FSMCreateStep):
    steps = utils.get_steps()
    
    content_type = message.content_type
    text = message.text
    caption = message.caption  

    if content_type != 'text':
        if message.caption_entities != None:
            custom_entities = []
            for entity in message.caption_entities:
                if entity.type == 'custom_emoji':
                    continue
                if entity.custom_emoji_id != None:
                    continue
                
                custom_entities.append(types.MessageEntity(type=entity.type, offset=entity.offset, length=entity.length, url=entity.url, user=entity.user, language=entity.language))
                
            msg_caption = await message.answer(text=caption, entities=custom_entities, parse_mode=None)
            await msg_caption.delete()
            caption = msg_caption.html_text
        
    if content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif content_type == 'document':
        file_id = message.document.file_id
    elif content_type == 'video':
        file_id = message.video.file_id
    elif content_type == 'audio':
        file_id = message.audio.file_id
    elif content_type == 'video_note':
        file_id = message.video_note.file_id
    elif content_type == 'voice':
        file_id = message.voice.file_id
    else:
        file_id = None
    
    key = utils.get_new_key()
    steps.update({
        key: {
            "content_type": content_type,
            "text": text,
            "caption": caption,
            "file_id": file_id,
            "keyboard": None,
            "delay": 0
        }
    })
    utils.update_steps(steps)
    
    await message.answer('✅ Шаг успешно добавлен', reply_markup=kb.markup_remove())
    await message.answer("👉 Выберите шаг, который вы хотите отредактировать", parse_mode='html', reply_markup=kb.markup_editor())


# ===== NEW SHOP ADMIN HANDLERS =====

def markup_admin_settings():
    """Admin settings keyboard"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.currency_settings')), callback_data='currency_rate')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.text_settings')), callback_data='text_settings')],
        [InlineKeyboardButton(text="🌐 Переводы", callback_data='translations')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)

@router.callback_query(F.data == 'lessons_mgmt')
async def lessons_management(call: types.CallbackQuery, state: FSMContext):
    """Lessons management menu"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        await call.message.answer(utils.get_text('messages.access_denied'))
        return
    
    await call.answer()
    await call.message.edit_text(
        utils.get_text('admin.messages.lesson_management'),
        reply_markup=kb.markup_lessons_management()
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
        utils.get_text('admin.messages.add_lesson_title'),
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMLesson.title)
async def add_lesson_title(message: types.Message, state: FSMLesson):
    """Process lesson title"""
    await state.update_data(title=message.text)
    await state.set_state(FSMLesson.description)
    
    await message.answer(
        utils.get_text('admin.messages.add_lesson_description'),
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMLesson.description)
async def add_lesson_description(message: types.Message, state: FSMLesson):
    """Process lesson description"""
    await state.update_data(description=message.text)
    await state.set_state(FSMLesson.price)
    
    await message.answer(
        utils.get_text('admin.messages.add_lesson_price'),
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMLesson.price)
async def add_lesson_price(message: types.Message, state: FSMLesson):
    """Process lesson price"""
    try:
        price = float(message.text.replace(',', '.'))
        if(price < 0):
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный формат цены. Введите число (например: 25.00):",
            reply_markup=kb.markup_cancel()
        )
        return
    
    await state.update_data(price=price, is_free=(price == 0))
    await state.set_state(FSMLesson.content)
    
    await message.answer(
        utils.get_text('admin.messages.add_lesson_content'),
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMLesson.content)
async def add_lesson_content(message: types.Message, state: FSMLesson):
    """Process lesson main content"""
    if(message.content_type not in ['video', 'text']):
        await message.answer(
            "❌ Отправьте видео или текстовое сообщение:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    # Store content data
    content_data = {
        'content_type': message.content_type,
        'text_content': message.text if message.content_type == 'text' else message.caption,
        'video_file_id': message.video.file_id if message.content_type == 'video' else None
    }
    
    await state.update_data(**content_data)
    await state.set_state(FSMLesson.preview)
    
    await message.answer(
        utils.get_text('admin.messages.add_lesson_preview'),
        reply_markup=kb.markup_pass()
    )


@router.message(FSMLesson.preview)
async def add_lesson_preview(message: types.Message, state: FSMLesson):
    """Process lesson preview content"""
    preview_data = {}
    
    if(message.text and message.text == "➡️ Пропустить"):
        # Skip preview
        pass
    elif(message.content_type == 'video'):
        preview_data['preview_video_file_id'] = message.video.file_id
        preview_data['preview_text'] = message.caption
    elif(message.content_type == 'text'):
        preview_data['preview_text'] = message.text
    else:
        await message.answer(
            "❌ Отправьте видео, текст или нажмите 'Пропустить':",
            reply_markup=kb.markup_pass()
        )
        return
    
    # Create lesson
    try:
        state_data = await state.get_data()
        
        lesson_data = {
            'title': state_data['title'],
            'description': state_data['description'],
            'price_usd': state_data['price'],
            'is_free': state_data['is_free'],
            'content_type': state_data['content_type'],
            'text_content': state_data.get('text_content'),
            'video_file_id': state_data.get('video_file_id'),
            **preview_data
        }
        
        new_lesson = await l.create_lesson(**lesson_data)
        
        await state.clear()
        await message.answer(
            utils.get_text('admin.messages.lesson_created'),
            reply_markup=kb.markup_remove()
        )
        
        # Return to lessons management
        await message.answer(
            utils.get_text('admin.messages.lesson_management'),
            reply_markup=kb.markup_lessons_management()
        )
        
    except Exception as e:
        logging.error(f"Error creating lesson: {e}")
        await state.clear()
        await message.answer(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_lessons_management()
        )


@router.callback_query(F.data == 'edit_lesson')
async def edit_lesson_list(call: types.CallbackQuery, state: FSMContext):
    """Show list of lessons for editing"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    
    try:
        lessons = await l.get_all_lessons(active_only=False)  # Include inactive
        
        if(not lessons):
            await call.message.edit_text(
                utils.get_text('admin.messages.no_lessons'),
                reply_markup=kb.markup_lessons_management()
            )
            return
        
        await call.message.edit_text(
            utils.get_text('admin.messages.select_lesson'),
            reply_markup=kb.markup_lesson_edit_list(lessons)
        )
        
    except Exception as e:
        logging.error(f"Error in edit_lesson_list: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_lessons_management()
        )


@router.callback_query(lambda F: F.data.startswith('edit_lesson_id:'))
async def edit_lesson_fields(call: types.CallbackQuery, state: FSMContext):
    """Show lesson editing options"""
    await call.answer()
    
    try:
        lesson_id = int(call.data.split(':')[1])
        lesson_data = await l.get_lesson(lesson_id)
        
        if(not lesson_data):
            await call.message.edit_text(
                utils.get_text('admin.messages.lesson_not_found'),
                reply_markup=kb.markup_lessons_management()
            )
            return
        
        status = "Активен" if lesson_data.is_active else "Неактивен"
        price_text = "БЕСПЛАТНО" if lesson_data.is_free else f"${lesson_data.price_usd}"
        
        text = f"✏️ <b>Редактирование урока</b>\n\n📚 {lesson_data.title}\n💰 {price_text}\n📊 {status}\n\nВыберите что изменить:"
        
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_lesson_edit_fields(lesson_id)
        )
        
    except Exception as e:
        logging.error(f"Error in edit_lesson_fields: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_lessons_management()
        )


@router.callback_query(lambda F: F.data.startswith('toggle_active:'))
async def toggle_lesson_active(call: types.CallbackQuery, state: FSMContext):
    """Toggle lesson active status"""
    await call.answer()
    
    try:
        lesson_id = int(call.data.split(':')[1])
        lesson_data = await l.get_lesson(lesson_id)
        
        if(not lesson_data):
            await call.answer("❌ Урок не найден")
            return
        
        new_status = not lesson_data.is_active
        await l.update_lesson(lesson_id, is_active=new_status)
        
        status_text = "активирован" if new_status else "деактивирован"
        await call.answer(f"✅ Урок {status_text}")
        
        # Refresh the edit page - modify callback data to match expected format
        call.data = f"edit_lesson_id:{lesson_id}"
        await edit_lesson_fields(call, state)
        
    except Exception as e:
        logging.error(f"Error in toggle_lesson_active: {e}")
        await call.answer("❌ Ошибка")


@router.callback_query(lambda F: F.data.startswith('toggle_free:'))
async def toggle_lesson_free(call: types.CallbackQuery, state: FSMContext):
    """Toggle lesson free status"""
    await call.answer()
    
    try:
        lesson_id = int(call.data.split(':')[1])
        lesson_data = await l.get_lesson(lesson_id)
        
        if(not lesson_data):
            await call.answer("❌ Урок не найден")
            return
        
        new_free_status = not lesson_data.is_free
        update_data = {'is_free': new_free_status}
        
        # If making free, set price to 0
        if(new_free_status):
            update_data['price_usd'] = 0
        
        await l.update_lesson(lesson_id, **update_data)
        
        status_text = "бесплатным" if new_free_status else "платным"
        await call.answer(f"✅ Урок стал {status_text}")
        
        # Refresh the edit page - modify callback data to match expected format
        call.data = f"edit_lesson_id:{lesson_id}"
        await edit_lesson_fields(call, state)
        
    except Exception as e:
        logging.error(f"Error in toggle_lesson_free: {e}")
        await call.answer("❌ Ошибка")


@router.callback_query(F.data == 'delete_lesson')
async def delete_lesson_input(call: types.CallbackQuery, state: FSMContext):
    """Ask for lesson ID to delete"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await state.set_state(FSMLesson.delete_confirm)
    await call.answer()
    await call.message.edit_text(
        utils.get_text('admin.messages.enter_lesson_id'),
        reply_markup=None
    )


@router.message(FSMLesson.delete_confirm)
async def delete_lesson_confirm(message: types.Message, state: FSMLesson):
    """Confirm lesson deletion"""
    try:
        lesson_id = int(message.text)
        lesson_data = await l.get_lesson(lesson_id)
        
        if(not lesson_data):
            await message.answer(
                utils.get_text('admin.messages.lesson_not_found'),
                reply_markup=kb.markup_lessons_management()
            )
            await state.clear()
            return
        
        await state.update_data(lesson_id=lesson_id)
        
        text = utils.get_text('admin.messages.confirm_delete', title=lesson_data.title)
        await message.answer(
            text,
            reply_markup=kb.markup_cancel()
        )
        
    except ValueError:
        await message.answer(
            "❌ Введите корректный ID урока (число):",
            reply_markup=kb.markup_cancel()
        )
    except Exception as e:
        logging.error(f"Error in delete_lesson_confirm: {e}")
        await message.answer(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_lessons_management()
        )
        await state.clear()


@router.message(lambda message: message.text == "Подтвердить" and message.from_user)
async def delete_lesson_execute(message: types.Message, state: FSMContext):
    """Execute lesson deletion"""
    current_state = await state.get_state()
    if(current_state != FSMLesson.delete_confirm):
        return
    
    try:
        state_data = await state.get_data()
        lesson_id = state_data.get('lesson_id')
        
        if(lesson_id):
            await l.delete_lesson(lesson_id)  # Soft delete
            
            await message.answer(
                utils.get_text('admin.messages.lesson_deleted'),
                reply_markup=kb.markup_remove()
            )
            
            await message.answer(
                utils.get_text('admin.messages.lesson_management'),
                reply_markup=kb.markup_lessons_management()
            )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in delete_lesson_execute: {e}")
        await message.answer(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_lessons_management()
        )
        await state.clear()


@router.callback_query(F.data == 'statDiagram')
async def show_statistics(call: types.CallbackQuery, state: FSMContext):
    """Show admin statistics"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    
    try:
        text = utils.get_text('admin.messages.gen_stats')
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_admin_shop(call.from_user.id)
        )
        
    except Exception as e:
        logging.error(f"Error in show_statistics: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_admin_shop(call.from_user.id)
        )


@router.callback_query(F.data == 'statistics')
async def show_statistics(call: types.CallbackQuery, state: FSMContext):
    """Show admin statistics"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    
    try:
        # Get user statistics
        all_users = await u.get_all_users()
        users_total = len(all_users)
        
        # Users registered today
        today_start = utils.get_period_start(1)
        users_today = len([u for u in all_users if u['date_registered'] >= today_start])
        
        # Users registered this week
        week_start = utils.get_period_start(7)
        users_week = len([u for u in all_users if u['date_registered'] >= week_start])
        
        # Get sales statistics
        sales_today = await p.get_purchases_stats(days=1)
        sales_week = await p.get_purchases_stats(days=7)
        sales_total = await p.get_purchases_stats()
        
        # Get admin count (unique admins from both sources)
        config_admins = set(config.ADMINS)
        json_admins = set(utils.get_admins())
        all_unique_admins = config_admins.union(json_admins)
        admin_count = len(all_unique_admins)
        
        text = utils.get_text('admin.messages.statistics_title',
                            users_day=users_today,
                            users_week=users_week,
                            users_total=users_total,
                            sales_day_count=sales_today['count'],
                            sales_day_usd=f"{sales_today['total_usd']:.2f}",
                            sales_week_count=sales_week['count'],
                            sales_week_usd=f"{sales_week['total_usd']:.2f}",
                            sales_total_count=sales_total['count'],
                            sales_total_usd=f"{sales_total['total_usd']:.2f}",
                            admins_count=admin_count)
        
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=utils.get_text('admin.buttons.back_admin'), callback_data='backAdmin')]
            ])
        )
        
    except Exception as e:
        logging.error(f"Error in show_statistics: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_admin_shop(call.from_user.id)
        )


@router.callback_query(F.data == 'settings')
async def show_settings(call: types.CallbackQuery, state: FSMContext):
    """Show admin settings"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    await call.message.edit_text(
        "⚙️ <b>Настройки системы</b>\n\nВыберите раздел:",
        reply_markup=kb.markup_admin_settings()
    )

@router.callback_query(F.data == 'text_settings')
async def text_settings(call: types.CallbackQuery, state: FSMContext):
    """Show text settings categories"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    await call.message.edit_text(
        "📝 <b>Настройка текстов</b>\n\nВыберите категорию для редактирования:",
        reply_markup=kb.markup_text_categories()
    )

@router.callback_query(lambda F: F.data.startswith('text_category:'))
async def text_category(call: types.CallbackQuery, state: FSMContext):
    """Show keys in selected category"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    category = call.data.split(':')[1]
    texts = utils.get_interface_texts()
    
    if category not in texts:
        await call.answer("❌ Категория не найдена")
        return
    
    keys = list(texts[category].keys())
    text = f"📝 <b>Категория: {category}</b>\n\nДоступные ключи для редактирования:"
    for key in keys:
        value = texts[category][key]
        # Log type for diagnostics
        logging.info(f"Value type for key '{key}' in category '{category}': {type(value)}")
        # Type check and fallback
        if not isinstance(value, str):
            logging.warning(f"Non-string value for key '{key}' in category '{category}': {value}. Converting to str.")
            value = str(value)
        text += f"\n• {key}: {value[:50]}{'...' if len(value) > 50 else ''}"
    
    await call.answer()
    await call.message.edit_text(
        text,
        reply_markup=kb.markup_text_keys(category)
    )

@router.callback_query(lambda F: F.data.startswith('text_key:'))
async def text_key(call: types.CallbackQuery, state: FSMContext):
    """Show current text value and edit option"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    parts = call.data.split(':')
    category = parts[1]
    key = parts[2]
    texts = utils.get_interface_texts()
    
    if(category not in texts or key not in texts[category]):
        await call.answer("❌ Ключ не найден")
        return
    
    value = texts[category][key]
    text = f"📝 <b>Редактирование: {category}.{key}</b>\n\nТекущее значение:\n{value}\n\nВведите новое значение для изменения."
    
    await state.update_data(category=category, key=key)
    await state.set_state(FSMSettings.text_value)
    
    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data='cancel_text')]
    ])
    
    await call.answer()
    await call.message.edit_text(
        text,
        reply_markup=cancel_markup
    )

@router.callback_query(F.data == 'currency_rate')
async def currency_rate_settings(call: types.CallbackQuery, state: FSMContext):
    """Initialize currency rate settings"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')
        return
    
    try:
        current_rate = await s.get_usd_to_stars_rate()
    except Exception as e:
        logging.error(f"Error getting current rate: {e}")
        current_rate = "неизвестно"
    
    await state.set_state(FSMSettings.currency_rate)
    await call.answer()
    cancel_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data='cancel_currency')]
    ])
    await call.message.edit_text(
        f"💱 <b>Настройки курса валют</b>\n\nТекущий курс: 1 USD = {current_rate} ⭐\n\nВведите новый курс (целое положительное число):",
        reply_markup=cancel_markup
    )

@router.callback_query(F.data == 'cancel_currency')
async def cancel_currency_edit(call: types.CallbackQuery, state: FSMContext):
    """Cancel currency rate editing and return to settings"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await state.clear()
    await call.answer("❌ Отменено")
    await call.message.edit_text(
        "⚙️ <b>Настройки системы</b>\n\nВыберите раздел:",
        reply_markup=kb.markup_admin_settings()
    )

@router.callback_query(F.data == 'translations')
async def translations_menu(call: types.CallbackQuery, state: FSMContext):
    """Start translations management"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    await state.set_state(FSMTranslations.language)
    await call.answer()
    await call.message.edit_text(
        "🌐 <b>Управление переводами</b>\n\nВведите код языка (e.g. 'en' for English, 'es' for Spanish):",
        reply_markup=kb.markup_cancel()
    )

@router.message(FSMTranslations.language)
async def translations_language(message: types.Message, state: FSMTranslations):
    """Process language input"""
    lang = message.text.strip().lower()
    if len(lang) > 10 or not re.match(r'^[a-z]{2,}$', lang):
        await message.answer("❌ Неверный код языка. Введите 2-10 букв (e.g. 'en', 'es'):")
        return
    await state.update_data(language=lang)
    await state.set_state(FSMTranslations.step)
    await message.answer(
        "📝 Выберите шаг для перевода (e.g. 'welcome', 'video_caption', 'catalog_menu'):",
        reply_markup=kb.markup_cancel()
    )

@router.message(FSMTranslations.step)
async def translations_step(message: types.Message, state: FSMTranslations):
    """Process step input"""
    step = message.text.strip()
    if len(step) > 50:
        await message.answer("❌ Шаг слишком длинный. Введите до 50 символов:")
        return
    await state.update_data(step=step)
    await state.set_state(FSMTranslations.field)
    await message.answer(
        "🏷️ Выберите поле (e.g. 'text', 'caption', 'button_label'):",
        reply_markup=kb.markup_cancel()
    )

@router.message(FSMTranslations.field)
async def translations_field(message: types.Message, state: FSMTranslations):
    """Process field input"""
    field = message.text.strip()
    if len(field) > 50:
        await message.answer("❌ Поле слишком длинное. Введите до 50 символов:")
        return
    await state.update_data(field=field)
    await state.set_state(FSMTranslations.value)
    await message.answer(
        "📝 Введите перевод для этого поля:",
        reply_markup=kb.markup_cancel()
    )

@router.message(FSMTranslations.value)
async def translations_value(message: types.Message, state: FSMTranslations):
    """Process value input and save translation"""
    value = message.text
    state_data = await state.get_data()
    lang = state_data['language']
    step = state_data['step']
    field = state_data['field']
    
    from database.lesson import Translations
    t = Translations()
    
    try:
        # Try to update if exists, else create
        existing = Translations.select().where(
            (Translations.step_id == step) &
            (Translations.language == lang) &
            (Translations.text_field == field)
        ).first()
        if existing:
            await t.update_translation(step, lang, field, value)
            await message.answer("✅ Перевод обновлен!")
        else:
            await t.create_translation(step, lang, field, value)
            await message.answer("✅ Перевод создан!")
    except Exception as e:
        logging.error(f"Error saving translation: {e}")
        await message.answer("❌ Ошибка сохранения перевода. Попробуйте снова.")
    
    await state.clear()
    await message.answer(
        "🌐 <b>Управление переводами</b>\n\nВыберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить перевод", callback_data='translations')],
            [InlineKeyboardButton(text="↩️ Назад к настройкам", callback_data='settings')]
        ])
    )

# ===== PROMOCODES MANAGEMENT =====

@router.callback_query(F.data == 'promocodes')
async def promocodes_management(call: types.CallbackQuery, state: FSMContext):
    """Promocodes management menu"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    await call.message.edit_text(
        "🏷️ <b>Управление промокодами</b>\n\nВыберите действие:",
        reply_markup=kb.markup_promocodes_management()
    )


@router.callback_query(F.data == 'add_promocode')
async def add_promocode_start(call: types.CallbackQuery, state: FSMContext):
    """Start adding new promocode"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await state.set_state(FSMPromocode.code)
    await call.answer()
    await call.message.edit_text(
        "🏷️ <b>Создание промокода</b>\n\nВведите код промокода (например: SALE20):",
        reply_markup=None
    )


@router.message(FSMPromocode.code)
async def add_promocode_code(message: types.Message, state: FSMContext):
    """Process promocode code"""
    code = message.text.strip().upper()
    
    # Check if promocode already exists
    existing_promocode = await promo.get_promocode(code)
    if(existing_promocode):
        await message.answer(
            "❌ Промокод с таким кодом уже существует. Введите другой код:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    await state.update_data(code=code)
    await state.set_state(FSMPromocode.discount_type)
    
    await message.answer(
        "💰 <b>Тип скидки</b>\n\nВыберите тип скидки:\n\n1️⃣ - Процентная скидка (например: 20 = 20%)\n2️⃣ - Фиксированная сумма в USD\n\nОтправьте 1 или 2:",
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMPromocode.discount_type)
async def add_promocode_discount_type(message: types.Message, state: FSMContext):
    """Process discount type"""
    if(message.text not in ['1', '2']):
        await message.answer(
            "❌ Выберите 1 или 2:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    discount_type = 'percent' if message.text == '1' else 'fixed'
    await state.update_data(discount_type=discount_type)
    await state.set_state(FSMPromocode.discount_value)
    
    if(discount_type == 'percent'):
        prompt = "📊 Введите размер скидки в процентах (от 1 до 100):"
    else:
        prompt = "💵 Введите размер скидки в долларах (например: 5.00):"
    
    await message.answer(
        prompt,
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMPromocode.discount_value)
async def add_promocode_discount_value(message: types.Message, state: FSMContext):
    """Process discount value"""
    try:
        value = float(message.text.replace(',', '.'))
        if(value <= 0):
            raise ValueError
        
        state_data = await state.get_data()
        
        if(state_data['discount_type'] == 'percent' and value > 100):
            await message.answer(
                "❌ Процентная скидка не может быть больше 100%. Введите значение от 1 до 100:",
                reply_markup=kb.markup_cancel()
            )
            return
        
        await state.update_data(discount_value=value)
        await state.set_state(FSMPromocode.usage_limit)
        
        await message.answer(
            "🔢 <b>Лимит использований</b>\n\nВведите максимальное количество использований промокода.\nДля неограниченного использования введите 0:",
            reply_markup=kb.markup_cancel()
        )
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число:",
            reply_markup=kb.markup_cancel()
        )


@router.message(FSMPromocode.usage_limit)
async def add_promocode_usage_limit(message: types.Message, state: FSMContext):
    """Process usage limit"""
    try:
        limit = int(message.text)
        if(limit < 0):
            raise ValueError
        
        usage_limit = limit if limit > 0 else None
        await state.update_data(usage_limit=usage_limit)
        await state.set_state(FSMPromocode.expiry_date)
        
        await message.answer(
            "📅 <b>Срок действия</b>\n\nВведите количество дней действия промокода.\nДля бессрочного промокода введите 0:",
            reply_markup=kb.markup_cancel()
        )
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число (0 или больше):",
            reply_markup=kb.markup_cancel()
        )


@router.message(FSMPromocode.expiry_date)
async def add_promocode_expiry_date(message: types.Message, state: FSMContext):
    """Process expiry date and create promocode"""
    try:
        days = int(message.text)
        if(days < 0):
            raise ValueError
        
        # Calculate expiry date
        expires_at = None
        if(days > 0):
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=days)
        
        # Create promocode
        state_data = await state.get_data()
        
        promocode_data = {
            'code': state_data['code'],
            'usage_limit': state_data['usage_limit'],
            'expires_at': expires_at
        }
        
        if(state_data['discount_type'] == 'percent'):
            promocode_data['discount_percent'] = int(state_data['discount_value'])
            promocode_data['discount_amount_usd'] = None
        else:
            promocode_data['discount_percent'] = 0
            promocode_data['discount_amount_usd'] = state_data['discount_value']
        
        new_promocode = await promo.create_promocode(**promocode_data)
        
        # Format summary
        discount_text = f"{state_data['discount_value']:.0f}%" if state_data['discount_type'] == 'percent' else f"${state_data['discount_value']:.2f}"
        limit_text = f"{state_data['usage_limit']} раз" if state_data['usage_limit'] else "Неограниченно"
        expiry_text = f"{days} дней" if days > 0 else "Бессрочно"
        
        summary = f"✅ <b>Промокод создан!</b>\n\n🏷️ Код: <code>{state_data['code']}</code>\n💰 Скидка: {discount_text}\n🔢 Лимит: {limit_text}\n📅 Действует: {expiry_text}"
        
        await message.answer(
            summary,
            reply_markup=kb.markup_remove()
        )
        
        await message.answer(
            "🏷️ <b>Управление промокодами</b>\n\nВыберите действие:",
            reply_markup=kb.markup_promocodes_management()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Введите корректное число (0 или больше):",
            reply_markup=kb.markup_cancel()
        )
    except Exception as e:
        logging.error(f"Error creating promocode: {e}")
        await message.answer(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_promocodes_management()
        )
        await state.clear()


@router.callback_query(F.data == 'list_promocodes')
async def list_promocodes(call: types.CallbackQuery, state: FSMContext):
    """Show list of promocodes"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    
    await call.answer()
    
    try:
        promocodes = await promo.get_all_promocodes()
        
        if(not promocodes):
            await call.message.edit_text(
                "📋 <b>Список промокодов</b>\n\nПромокодов пока нет.",
                reply_markup=kb.markup_promocodes_management()
            )
            return
        
        text = "📋 <b>Список промокодов</b>\n\n"
        
        for promo_data in promocodes:
            status = "🟢 Активен" if promo_data['is_active'] else "🔴 Неактивен"
            
            if(promo_data['discount_amount_usd']):
                discount = f"${promo_data['discount_amount_usd']:.2f}"
            else:
                discount = f"{promo_data['discount_percent']}%"
            
            usage_info = f"{promo_data['used_count']}"
            if(promo_data['usage_limit']):
                usage_info += f"/{promo_data['usage_limit']}"
            
            expires_info = "Бессрочно"
            if(promo_data['expires_at']):
                expires_info = promo_data['expires_at'].strftime("%d.%m.%Y")
            
            text += f"🏷️ <code>{promo_data['code']}</code>\n{status} | Скидка: {discount} | Использовано: {usage_info} | До: {expires_info}\n\n"
        
        if(len(text) > 4000):  # Telegram message limit
            text = text[:4000] + "\n\n... (список обрезан)"
        
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↪️ Назад", callback_data='promocodes')]
            ])
        )
        
    except Exception as e:
        logging.error(f"Error in list_promocodes: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_promocodes_management()
        )
