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
    logging.info("admin.py: Обработчик /admin вызван")
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


# Закомментировано - используется универсальный cancel_handler
# @router.message(F.text == '❌ Отмена')
# async def cancel(message: types.Message, state: FSMContext):
#     print(f"🚨 admin.py: Обработчик отмены вызван! Текст: '{message.text}'")
#     # Не обрабатывать, если активно состояние рассылки
#     current_state = await state.get_state()
#     logging.info(f"🔍 admin.py cancel: текущее состояние = {current_state}")
#     print(f"🔍 admin.py cancel: текущее состояние = {current_state}")
#     
#     if current_state and 'FSMMail' in current_state:
#         logging.info(f"⏭️ admin.py: пропускаем, т.к. активно состояние рассылки {current_state}")
#         print(f"⏭️ admin.py: пропускаем, т.к. активно состояние рассылки {current_state}")
#         # Пропускаем - пусть обработчик mail.py сам обработает
#         return
#     
#     if current_state != None:
#         await state.clear()
#         
#     data_admins = utils.get_admins()
# 
#     if message.from_user.id in config.ADMINS or message.from_user.id in data_admins:    
#         await message.answer('❌ Отмено', reply_markup=kb.markup_remove())
#         await message.answer(' ', reply_markup=kb.markup_remove())
#         await admin(message, state)
    
    
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
    await state.update_data(mode='add')  # Режим добавления
    await call.answer()
    await call.message.edit_text(
        '👉 Введите название урока:',
        reply_markup=None
    )


# ===== FSMLesson Message Handlers =====

@router.message(FSMLesson.title)
async def add_lesson_title(message: types.Message, state: FSMContext):
    """Handle lesson title input"""
    data = await state.get_data()
    mode = data.get('mode', 'add')
    
    title = message.text.strip()
    if not title:
        await message.answer('❌ Название не может быть пустым. Введите название урока:')
        return
    
    if mode == 'edit':
        # Режим редактирования
        lesson_id = data.get('edit_lesson_id')
        if lesson_id:
            success = await l.update_lesson(lesson_id, title=title)
            if success:
                await message.answer('✅ Название урока обновлено', reply_markup=kb.markup_remove())
                await state.clear()
                # Обновляем экран редактирования
                await edit_lesson_fields_refresh(message, state, lesson_id)
            else:
                await message.answer('❌ Ошибка обновления названия')
        return
    
    # Режим добавления
    await state.update_data(title=title)
    await state.set_state(FSMLesson.description)
    await message.answer('👉 Введите описание урока:')


@router.message(FSMLesson.description)
async def add_lesson_description(message: types.Message, state: FSMContext):
    """Handle lesson description input"""
    data = await state.get_data()
    mode = data.get('mode', 'add')
    
    description = message.text.strip()
    if not description:
        await message.answer('❌ Описание не может быть пустым. Введите описание урока:')
        return
    
    if mode == 'edit':
        # Режим редактирования
        lesson_id = data.get('edit_lesson_id')
        if lesson_id:
            success = await l.update_lesson(lesson_id, description=description)
            if success:
                await message.answer('✅ Описание урока обновлено', reply_markup=kb.markup_remove())
                await state.clear()
                await edit_lesson_fields_refresh(message, state, lesson_id)
            else:
                await message.answer('❌ Ошибка обновления описания')
        return
    
    # Режим добавления
    await state.update_data(description=description)
    await state.set_state(FSMLesson.price)
    await message.answer('👉 Введите цену урока в USD (0 для бесплатного):')


@router.message(FSMLesson.price)
async def add_lesson_price(message: types.Message, state: FSMContext):
    """Handle lesson price input"""
    from decimal import Decimal, InvalidOperation
    
    data = await state.get_data()
    mode = data.get('mode', 'add')
    
    try:
        price = Decimal(message.text.strip())
        if price < 0:
            await message.answer('❌ Цена не может быть отрицательной. Введите корректную цену:')
            return
    except (InvalidOperation, ValueError):
        await message.answer('❌ Неверный формат цены. Введите число:')
        return
    
    is_free = (price == 0)
    
    if mode == 'edit':
        # Режим редактирования
        lesson_id = data.get('edit_lesson_id')
        if lesson_id:
            success = await l.update_lesson(lesson_id, price_usd=price, is_free=is_free)
            if success:
                await message.answer('✅ Цена урока обновлена', reply_markup=kb.markup_remove())
                await state.clear()
                await edit_lesson_fields_refresh(message, state, lesson_id)
            else:
                await message.answer('❌ Ошибка обновления цены')
        return
    
    # Режим добавления
    await state.update_data(price_usd=price, is_free=is_free)
    await state.set_state(FSMLesson.content)
    await message.answer('👉 Отправьте видео для урока (или текст /skip для пропуска):')


@router.message(FSMLesson.content)
async def add_lesson_content(message: types.Message, state: FSMContext):
    """Handle lesson content input"""
    data = await state.get_data()
    mode = data.get('mode', 'add')
    
    content_type = None
    file_id = None
    
    if message.text == '/skip':
        content_type = 'text'
        file_id = None
    elif message.video:
        content_type = 'video'
        file_id = message.video.file_id
    elif message.document:
        content_type = 'document'
        file_id = message.document.file_id
    elif message.text:
        content_type = 'text'
        file_id = None
        await state.update_data(text_content=message.text)
    else:
        await message.answer('❌ Неподдерживаемый тип контента. Отправьте видео, документ или текст:')
        return
    
    if mode == 'edit':
        # Режим редактирования
        lesson_id = data.get('edit_lesson_id')
        if lesson_id:
            update_data = {'content_type': content_type}
            if content_type == 'video':
                update_data['video_file_id'] = file_id
            elif content_type == 'document':
                update_data['document_file_id'] = file_id
            elif content_type == 'text' and message.text != '/skip':
                update_data['text_content'] = message.text
            
            success = await l.update_lesson(lesson_id, **update_data)
            if success:
                await message.answer('✅ Контент урока обновлен', reply_markup=kb.markup_remove())
                await state.clear()
                await edit_lesson_fields_refresh(message, state, lesson_id)
            else:
                await message.answer('❌ Ошибка обновления контента')
        return
    
    # Режим добавления
    await state.update_data(content_type=content_type, video_file_id=file_id)
    await state.set_state(FSMLesson.preview)
    await message.answer('👉 Отправьте превью видео (трейлер) или текст для превью (или /skip для пропуска):')


@router.message(FSMLesson.preview)
async def add_lesson_preview(message: types.Message, state: FSMContext):
    """Handle lesson preview input"""
    data = await state.get_data()
    mode = data.get('mode', 'add')
    
    preview_video_file_id = None
    preview_text = None
    
    if message.text == '/skip':
        pass
    elif message.video:
        preview_video_file_id = message.video.file_id
    elif message.text:
        preview_text = message.text
    else:
        await message.answer('❌ Отправьте видео или текст для превью:')
        return
    
    if mode == 'edit':
        # Режим редактирования
        lesson_id = data.get('edit_lesson_id')
        if lesson_id:
            update_data = {}
            if preview_video_file_id:
                update_data['preview_video_file_id'] = preview_video_file_id
            if preview_text:
                update_data['preview_text'] = preview_text
            
            if update_data:
                success = await l.update_lesson(lesson_id, **update_data)
                if success:
                    await message.answer('✅ Превью урока обновлено', reply_markup=kb.markup_remove())
                else:
                    await message.answer('❌ Ошибка обновления превью')
            await state.clear()
            await edit_lesson_fields_refresh(message, state, lesson_id)
        return
    
    # Режим добавления - показываем превью для подтверждения
    await state.update_data(preview_video_file_id=preview_video_file_id, preview_text=preview_text)
    
    # Формируем текст превью
    title = data.get('title', 'Без названия')
    description = data.get('description', 'Без описания')
    price = data.get('price_usd', 0)
    is_free = data.get('is_free', False)
    
    price_text = '🎁 БЕСПЛАТНО' if is_free else f'💰 ${price}'
    
    preview_message = f"""📚 <b>Превью нового урока</b>

📌 Название: {title}
📝 Описание: {description}
{price_text}

✅ Сохранить урок?"""
    
    await message.answer(
        preview_message,
        parse_mode='html',
        reply_markup=kb.markup_add_preview_actions()
    )


# ===== Lesson Add Save/Cancel Callbacks =====

@router.callback_query(F.data == 'add_lesson_save')
async def add_lesson_save(call: types.CallbackQuery, state: FSMContext):
    """Save new lesson to database"""
    data = await state.get_data()
    
    try:
        # Создаем урок
        lesson_id = await l.create_lesson(
            title=data.get('title'),
            description=data.get('description'),
            price_usd=data.get('price_usd', 0),
            is_free=data.get('is_free', False),
            is_active=True,
            content_type=data.get('content_type', 'video'),
            video_file_id=data.get('video_file_id'),
            preview_video_file_id=data.get('preview_video_file_id'),
            preview_text=data.get('preview_text'),
            text_content=data.get('text_content')
        )
        
        await state.clear()
        await call.answer('✅ Урок успешно создан!')
        await call.message.edit_text(
            f'✅ Урок "{data.get("title")}" успешно создан!\n\n📚 Управление уроками',
            reply_markup=kb.markup_lessons_management()
        )
    except Exception as e:
        logging.error(f"Error creating lesson: {e}")
        await call.answer('❌ Ошибка создания урока')
        await call.message.edit_text(
            '❌ Произошла ошибка при создании урока',
            reply_markup=kb.markup_lessons_management()
        )


@router.callback_query(F.data == 'add_lesson_cancel')
async def add_lesson_cancel(call: types.CallbackQuery, state: FSMContext):
    """Cancel lesson creation"""
    await state.clear()
    await call.answer('❌ Создание урока отменено')
    await call.message.edit_text(
        '📚 Управление уроками',
        reply_markup=kb.markup_lessons_management()
    )


# ===== Edit Lesson Handlers =====

@router.callback_query(F.data == 'edit_lesson')
async def edit_lesson_list(call: types.CallbackQuery, state: FSMContext):
    """Show list of lessons for editing"""
    await call.answer()
    
    lessons = await l.get_all_lessons(active_only=False)
    
    if not lessons:
        await call.message.edit_text(
            '📚 Нет доступных уроков для редактирования',
            reply_markup=kb.markup_lessons_management()
        )
        return
    
    # Проверяем, не отображается ли уже этот экран
    current_text = '✏️ Выберите урок для редактирования:'
    if call.message.text == current_text:
        # Уже на этом экране, просто отвечаем без изменения
        return
    
    await call.message.edit_text(
        current_text,
        reply_markup=kb.markup_lesson_edit_list(lessons)
    )


@router.callback_query(F.data.startswith('edit_lesson_id:'))
async def edit_lesson_fields(call: types.CallbackQuery, state: FSMContext):
    """Show edit options for specific lesson"""
    await call.answer()
    
    lesson_id = int(call.data.split(':')[1])
    lesson = await l.get_lesson(lesson_id)
    
    if not lesson:
        await call.message.edit_text(
            '❌ Урок не найден',
            reply_markup=kb.markup_lessons_management()
        )
        return
    
    status = "✅ Активен" if lesson.is_active else "🔴 Неактивен"
    price_text = "🎁 БЕСПЛАТНО" if lesson.is_free else f"💰 ${lesson.price_usd}"
    
    text = f"""✏️ <b>Редактирование урока</b>

📚 {lesson.title}
💰 {price_text}
📊 {status}

Выберите что изменить:"""
    
    await call.message.edit_text(
        text,
        parse_mode='html',
        reply_markup=kb.markup_lesson_edit_fields(lesson_id)
    )


async def edit_lesson_fields_refresh(message_or_call, state: FSMContext, lesson_id: int):
    """Refresh edit lesson screen"""
    lesson = await l.get_lesson(lesson_id)
    
    if not lesson:
        text = '❌ Урок не найден'
        markup = kb.markup_lessons_management()
    else:
        status = "✅ Активен" if lesson.is_active else "🔴 Неактивен"
        price_text = "🎁 БЕСПЛАТНО" if lesson.is_free else f"💰 ${lesson.price_usd}"
        
        text = f"""✏️ <b>Редактирование урока</b>

📚 {lesson.title}
💰 {price_text}
📊 {status}

Выберите что изменить:"""
        markup = kb.markup_lesson_edit_fields(lesson_id)
    
    # Определяем тип объекта и используем соответствующий метод
    if isinstance(message_or_call, types.CallbackQuery):
        await message_or_call.message.edit_text(
            text,
            parse_mode='html',
            reply_markup=markup
        )
    else:
        # Для Message объекта нужно отправить новое сообщение
        await message_or_call.answer(
            text,
            parse_mode='html',
            reply_markup=markup
        )


# ===== Field Edit Handlers =====

@router.callback_query(F.data.startswith('edit_field:'))
async def edit_field_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing specific field"""
    await call.answer()
    
    parts = call.data.split(':')
    field = parts[1]
    lesson_id = int(parts[2])
    
    await state.update_data(mode='edit', edit_lesson_id=lesson_id, edit_field=field)
    
    prompts = {
        'title': ('FSMLesson.title', '👉 Введите новое название урока:'),
        'description': ('FSMLesson.description', '👉 Введите новое описание урока:'),
        'price': ('FSMLesson.price', '👉 Введите новую цену в USD (0 для бесплатного):'),
        'video': ('FSMLesson.content', '👉 Отправьте новое видео для урока:'),
        'preview': ('FSMLesson.preview', '👉 Отправьте новое превью (видео или текст):')
    }
    
    if field in prompts:
        state_name, prompt = prompts[field]
        if state_name == 'FSMLesson.title':
            await state.set_state(FSMLesson.title)
        elif state_name == 'FSMLesson.description':
            await state.set_state(FSMLesson.description)
        elif state_name == 'FSMLesson.price':
            await state.set_state(FSMLesson.price)
        elif state_name == 'FSMLesson.content':
            await state.set_state(FSMLesson.content)
        elif state_name == 'FSMLesson.preview':
            await state.set_state(FSMLesson.preview)
        
        await call.message.edit_text(prompt)


# ===== Toggle Handlers =====

@router.callback_query(F.data.startswith('toggle_active:'))
async def toggle_lesson_active(call: types.CallbackQuery, state: FSMContext):
    """Toggle lesson active status"""
    lesson_id = int(call.data.split(':')[1])
    
    lesson = await l.get_lesson(lesson_id)
    if not lesson:
        await call.answer('❌ Урок не найден')
        return
    
    new_status = not lesson.is_active
    success = await l.update_lesson(lesson_id, is_active=new_status)
    
    if success:
        status_text = "активирован" if new_status else "деактивирован"
        await call.answer(f"✅ Урок {status_text}")
        await edit_lesson_fields_refresh(call, state, lesson_id)
    else:
        await call.answer('❌ Ошибка обновления статуса')


@router.callback_query(F.data.startswith('toggle_free:'))
async def toggle_lesson_free(call: types.CallbackQuery, state: FSMContext):
    """Toggle lesson free status"""
    lesson_id = int(call.data.split(':')[1])
    
    lesson = await l.get_lesson(lesson_id)
    if not lesson:
        await call.answer('❌ Урок не найден')
        return
    
    new_free_status = not lesson.is_free
    update_data = {'is_free': new_free_status}
    
    # Если делаем бесплатным, ставим цену 0
    if new_free_status:
        update_data['price_usd'] = 0
    
    success = await l.update_lesson(lesson_id, **update_data)
    
    if success:
        status_text = "бесплатным" if new_free_status else "платным"
        await call.answer(f"✅ Урок стал {status_text}")
        await edit_lesson_fields_refresh(call, state, lesson_id)
    else:
        await call.answer('❌ Ошибка обновления')


# ===== Delete Lesson Handlers =====

@router.callback_query(F.data == 'delete_lesson')
async def delete_lesson_list(call: types.CallbackQuery, state: FSMContext):
    """Show list of lessons for deletion"""
    await call.answer()
    
    lessons = await l.get_all_lessons(active_only=False)
    
    if not lessons:
        await call.message.edit_text(
            '📚 Нет доступных уроков для удаления',
            reply_markup=kb.markup_lessons_management()
        )
        return
    
    await call.message.edit_text(
        '🗑️ Выберите урок для удаления:',
        reply_markup=kb.markup_lesson_delete_list(lessons)
    )


@router.callback_query(F.data.startswith('delete_lesson_id:'))
async def delete_lesson_confirm(call: types.CallbackQuery, state: FSMContext):
    """Ask for deletion confirmation"""
    await call.answer()
    
    lesson_id = int(call.data.split(':')[1])
    lesson = await l.get_lesson(lesson_id)
    
    if not lesson:
        await call.message.edit_text(
            '❌ Урок не найден',
            reply_markup=kb.markup_lessons_management()
        )
        return
    
    await call.message.edit_text(
        f'⚠️ Вы уверены, что хотите удалить урок "{lesson.title}"?\n\nЭто действие необратимо!',
        reply_markup=kb.markup_confirm_delete(lesson_id)
    )


@router.callback_query(F.data.startswith('confirm_delete:'))
async def confirm_delete_lesson(call: types.CallbackQuery, state: FSMContext):
    """Confirm and delete lesson"""
    lesson_id = int(call.data.split(':')[1])
    
    success = await l.delete_lesson(lesson_id)
    
    if success:
        await call.answer('✅ Урок успешно удален')
        
        # Проверяем остались ли уроки
        lessons = await l.get_all_lessons(active_only=False)
        if lessons:
            await call.message.edit_text(
                '🗑️ Выберите урок для удаления:',
                reply_markup=kb.markup_lesson_delete_list(lessons)
            )
        else:
            await call.message.edit_text(
                '✅ Урок успешно удален\n\n📚 Управление уроками',
                reply_markup=kb.markup_lessons_management()
            )
    else:
        await call.answer('❌ Ошибка удаления урока')


@router.callback_query(F.data.startswith('cancel_delete:'))
async def cancel_delete_lesson(call: types.CallbackQuery, state: FSMContext):
    """Cancel lesson deletion"""
    await call.answer('❌ Удаление отменено')
    
    lessons = await l.get_all_lessons(active_only=False)
    
    if lessons:
        await call.message.edit_text(
            '🗑️ Выберите урок для удаления:',
            reply_markup=kb.markup_lesson_delete_list(lessons)
        )
    else:
        await call.message.edit_text(
            '📚 Управление уроками',
            reply_markup=kb.markup_lessons_management()
        )


# End of file
