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
from states import FSMAdminRights, FSMLesson, FSMSettings, FSMPromocode, FSMTranslations, FSMOnboardingAdmin, FSMOnboardingOption
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
    else:
        text_rights = "Права администратора не определены"
        
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
    else:
        text_rights = "Права администратора не определены"
        
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
    else:
        text_rights = "Права администратора не определены"
        
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


@router.callback_query(F.data == 'onboarding_admin')
async def onboarding_admin_menu(call: types.CallbackQuery, state: FSMContext):
    """Onboarding admin menu"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer()
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb_local = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👁️ Предпросмотр', callback_data='onboarding_preview')],
        [InlineKeyboardButton(text='🧹 Убрать предпросмотр', callback_data='onboarding_preview_clear')],
        [InlineKeyboardButton(text='🧱 Конструктор шагов', callback_data='onb_steps')],
        [InlineKeyboardButton(text='📝 Править тексты', callback_data='text_settings')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='settings')]
    ])
    await call.answer()
    await call.message.edit_text('🧭 Онбординг', reply_markup=kb_local)


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
        # Check if message.text is None
        if message.text is None:
            await message.answer('❌ Неверный формат цены. Введите число:')
            return
        
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
        'document': ('FSMLesson.content', '👉 Отправьте новый документ (PDF/DOC и т.п.) для урока:'),
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


@router.callback_query(F.data.startswith('lesson_preview:'))
async def lesson_preview(call: types.CallbackQuery, state: FSMContext):
    """Send preview of lesson content (video + document) to admin, then show a separate clear button message"""
    await call.answer()
    try:
        lesson_id = int(call.data.split(':')[1])
        lesson_obj = await l.get_lesson(lesson_id)
        if not lesson_obj:
            await call.answer('❌ Урок не найден', show_alert=True)
            return
        admin_id = call.from_user.id
        from bot_instance import bot
        # Reuse tracking from shop
        from handlers.shop import add_user_preview_message
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        # Send video if present
        sent_any = False
        if lesson_obj.content_type == 'video' and getattr(lesson_obj, 'video_file_id', None):
            try:
                msg = await bot.send_video(
                    chat_id=admin_id,
                    video=lesson_obj.video_file_id,
                    caption=f"📚 <b>{lesson_obj.title}</b>\n\n{lesson_obj.description or ''}",
                    parse_mode='HTML'
                )
                await add_user_preview_message(admin_id, msg.message_id)
                sent_any = True
            except Exception:
                pass
        # Send document if present
        if getattr(lesson_obj, 'document_file_id', None):
            try:
                msg2 = await bot.send_document(
                    chat_id=admin_id,
                    document=lesson_obj.document_file_id,
                    caption="📁 Материалы урока",
                    parse_mode='HTML'
                )
                await add_user_preview_message(admin_id, msg2.message_id)
                sent_any = True
            except Exception:
                pass
        # Fallback to text preview if nothing sent
        if not sent_any:
            await call.message.answer(
                f"📚 <b>{lesson_obj.title}</b>\n\n{lesson_obj.description or ''}\n\n{lesson_obj.text_content or '📝 Контент не загружен'}",
                parse_mode='HTML'
            )
        # Send separate clear button message
        clear_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🧹 Убрать предпросмотр', callback_data=f'lesson_preview_clear:{lesson_id}')]])
        await bot.send_message(chat_id=admin_id, text='🧹 Нажмите, чтобы убрать предпросмотр', reply_markup=clear_kb)
        await call.answer('✅ Предпросмотр отправлен')
    except Exception as e:
        await call.answer('❌ Ошибка предпросмотра', show_alert=True)


@router.callback_query(F.data.startswith('lesson_preview_clear:'))
async def lesson_preview_clear(call: types.CallbackQuery, state: FSMContext):
    """Clear previously sent preview messages for admin"""
    await call.answer()
    try:
        admin_id = call.from_user.id
        from handlers.shop import clear_user_preview_messages
        from message_manager import global_message_manager
        await clear_user_preview_messages(admin_id, admin_id)
        # Удаляем и сообщение с кнопкой "Убрать предпросмотр"
        if call.message:
            await global_message_manager.delete_message_safe(call.message.chat.id, call.message.message_id)
        await call.answer('🧹 Предпросмотр удален')
    except Exception:
        await call.answer('❌ Ошибка удаления предпросмотра', show_alert=True)


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


# ===== PROMOCODES HANDLERS =====

@router.callback_query(F.data == 'promocodes')
async def promocodes_menu(call: types.CallbackQuery, state: FSMContext):
    """Promocodes management menu with list - ADMIN ONLY"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    # Получаем все промокоды
    promocodes = await promo.get_all_promocodes()
    
    # Формируем текст со списком промокодов
    text = '🎫 <b>Управление промокодами</b>\n\n'
    
    if promocodes:
        text += '📋 <b>Активные промокоды:</b>\n'
        text += '━━━━━━━━━━━━━━━━━━━━\n\n'
        
        for p in promocodes:
            # Только активные промокоды
            if not p.get('is_active', False):
                continue
                
            # Правильно получаем данные о скидке из базы
            discount_type = p.get('discount_type', 'percentage')
            discount_value = p.get('discount_value', 0)
            
            # Форматируем скидку для отображения
            if discount_type == 'percentage':
                # Для процентных скидок конвертируем из доли в проценты
                discount_percent = float(discount_value) * 100 if float(discount_value) <= 1 else float(discount_value)
                discount_text = f"{int(discount_percent)}%" if discount_percent.is_integer() else f"{discount_percent:.1f}%"
            else:  # fixed
                # Для фиксированных скидок отображаем в долларах
                discount_amount = float(discount_value)
                discount_text = f"${int(discount_amount)}" if discount_amount.is_integer() else f"${discount_amount:.2f}"
            
            usage_count = p.get('used_count', 0)  # Правильное поле - used_count, а не usage_count
            usage_limit = p.get('usage_limit')
            usage_text = f"{usage_count}/{usage_limit if usage_limit else '∞'}"
            
            # Проверяем срок действия
            expires_at = p.get('expires_at')
            if expires_at:
                from datetime import datetime
                if isinstance(expires_at, str):
                    # Поддержка ISO и 'YYYY-MM-DD HH:MM:SS'
                    try:
                        expires_at = datetime.fromisoformat(expires_at)
                    except ValueError:
                        # Fallback: заменяем пробел на 'T'
                        try:
                            expires_at = datetime.fromisoformat(expires_at.replace(' ', 'T'))
                        except Exception:
                            expires_at = None
                expires_text = f"до {expires_at.strftime('%d.%m.%Y %H:%M')}" if expires_at else 'бессрочно'
            else:
                expires_text = "бессрочно"
            
            text += f"🎫 <code>{p.get('code', 'N/A')}</code>\n"
            text += f"   💰 Скидка: {discount_text}\n"
            text += f"   📊 Использовано: {usage_text}\n"
            text += f"   ⏰ Срок: {expires_text}\n\n"
    else:
        text += '📭 <i>Промокодов пока нет</i>\n\n'
    
    text += '━━━━━━━━━━━━━━━━━━━━\n'
    text += '💡 <i>Используйте кнопки ниже для управления</i>'
    
    await call.answer()
    await call.message.edit_text(
        text,
        parse_mode='html',
        reply_markup=kb.markup_promocodes_management()
    )


@router.callback_query(F.data == 'add_promocode')
async def add_promocode_start(call: types.CallbackQuery, state: FSMContext):
    """Start adding new promocode"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    await state.set_state(FSMPromocode.code)
    await call.answer()
    await call.message.edit_text('👉 Введите код промокода:')


# Удалено - список теперь отображается сразу в меню promocodes

# ===== PROMOCODE DELETE HANDLERS =====

@router.callback_query(F.data == 'delete_promocode_menu')
async def delete_promocode_menu(call: types.CallbackQuery, state: FSMContext):
    """Menu for selecting promocode to delete"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    promocodes = await promo.get_all_promocodes(only_active=True)
    
    if not promocodes:
        await call.answer('📋 Активных промокодов нет')
        # Возвращаемся в обновлённое меню
        await promocodes_menu(call, state)
        return
    
    await call.answer()
    await call.message.edit_text(
        '🗑️ <b>Выберите промокод для удаления:</b>',
        parse_mode='html',
        reply_markup=kb.markup_promocodes_delete_list(promocodes, promo.format_discount)
    )


@router.callback_query(F.data.startswith('delete_promocode:'))
async def delete_promocode_confirm(call: types.CallbackQuery, state: FSMContext):
    """Ask for deletion confirmation"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    promo_id = int(call.data.split(':')[1])
    promocode = await promo.get_promocode_by_id(promo_id)
    
    if not promocode:
        await call.answer('❌ Промокод не найден')
        await delete_promocode_menu(call, state)
        return
    
    # Получаем данные промокода
    code = promocode.code if hasattr(promocode, 'code') else 'N/A'
    dtype = promocode.discount_type if hasattr(promocode, 'discount_type') else 'percentage'
    dval = promocode.discount_value if hasattr(promocode, 'discount_value') else 0
    discount_text = promo.format_discount(dtype, dval)
    
    await call.answer()
    await call.message.edit_text(
        f'''❌ <b>Подтверждение удаления</b>

Удалить промокод <code>{code}</code>?
Скидка: {discount_text}

⚠️ Действие необратимо!''',
        parse_mode='html',
        reply_markup=kb.markup_confirm_delete_promocode(promo_id)
    )


@router.callback_query(F.data.startswith('confirm_delete_promocode:'))
async def confirm_delete_promocode(call: types.CallbackQuery, state: FSMContext):
    """Actually delete the promocode"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    promo_id = int(call.data.split(':')[1])
    success = await promo.delete_promocode(promo_id)
    
    if success:
        await call.answer('✅ Промокод успешно удалён')
    else:
        await call.answer('❌ Ошибка удаления')
    
    # Возвращаемся в обновлённое меню промокодов со списком
    await promocodes_menu(call, state)

# ===== PROMOCODE CREATE HANDLERS (FSM) =====

@router.message(FSMPromocode.code)
async def add_promocode_code(message: types.Message, state: FSMContext):
    """Handle promocode code input"""
    import re
    
    code = message.text.strip().upper()
    
    # Валидация кода
    if not re.match(r'^[A-Z0-9_-]+$', code):
        await message.answer('❌ Некорректный код. Используйте только латинские буквы, цифры, _ и -')
        return
    
    # Проверяем уникальность среди всех промокодов (включая неактивные)
    existing = await promo.get_promocode_any(code)
    if existing:
        await message.answer('❌ Такой код уже существует. Введите другой:')
        return
    
    await state.update_data(code=code)
    await message.answer(
        '🎯 <b>Выберите тип скидки:</b>',
        parse_mode='html',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📊 Процент', callback_data='promo_disc_type:percentage')],
            [InlineKeyboardButton(text='💵 Фиксированная сумма', callback_data='promo_disc_type:fixed')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_promocode')]
        ])
    )


@router.callback_query(F.data.startswith('promo_disc_type:'))
async def add_promocode_type(call: types.CallbackQuery, state: FSMContext):
    """Handle discount type selection"""
    dtype = call.data.split(':')[1]
    await state.update_data(discount_type=dtype)
    await state.set_state(FSMPromocode.discount_value)
    
    if dtype == 'percentage':
        msg = '👉 Введите процент скидки (1-100):'
    else:
        msg = '👉 Введите сумму скидки в USD (например: 5 или 7.5):'
    
    await call.answer()
    await call.message.edit_text(msg)


@router.message(FSMPromocode.discount_value)
async def add_promocode_value(message: types.Message, state: FSMContext):
    """Handle discount value input"""
    data = await state.get_data()
    dtype = data.get('discount_type')
    
    # Парсим число (поддерживаем и точку, и запятую)
    try:
        value_str = message.text.strip().replace(',', '.')
        value = float(value_str)
    except ValueError:
        await message.answer('❌ Некорректное число. Повторите ввод:')
        return
    
    # Валидация
    if dtype == 'percentage':
        if not (1 <= value <= 100):
            await message.answer('❌ Процент должен быть от 1 до 100. Повторите ввод:')
            return
        # Сохраняем как долю (0-1) для совместимости с текущей логикой
        value = value / 100
    else:  # fixed
        if value <= 0:
            await message.answer('❌ Сумма должна быть больше 0. Повторите ввод:')
            return
    
    await state.update_data(discount_value=value)
    await state.set_state(FSMPromocode.usage_limit)
    await message.answer('👉 Введите максимальное количество использований (0 = без лимита):')


@router.message(FSMPromocode.usage_limit)
async def add_promocode_limit(message: types.Message, state: FSMContext):
    """Handle usage limit input"""
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError
    except ValueError:
        await message.answer('❌ Некорректное число. Введите целое число >= 0:')
        return
    
    # 0 = None (без лимита)
    await state.update_data(usage_limit=limit if limit > 0 else None)
    await state.set_state(FSMPromocode.expiry_date)
    from datetime import datetime, timedelta
    example_text = (datetime.now() + timedelta(days=7)).replace(hour=23, minute=59, second=0, microsecond=0).strftime('%d.%m.%Y %H:%M')
    await message.answer(
        '👉 Введите дату окончания\n'
        'Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n'
        'Или 0 для бессрочного промокода:\n\n'
        f'Например: {example_text}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_promocode')]])
    )


@router.message(FSMPromocode.expiry_date)
async def add_promocode_expiry(message: types.Message, state: FSMContext):
    """Handle expiry date input"""
    from datetime import datetime
    
    text = message.text.strip()
    
    if text == '0':
        expires_at = None
        expires_text = 'бессрочно'
    else:
        try:
            # Пытаемся распарсить дату (русский формат ДД.ММ.ГГГГ ЧЧ:ММ)
            expires_at = datetime.strptime(text, '%d.%m.%Y %H:%M')
            
            # Проверка: дата не должна быть в прошлом
            now = datetime.now()
            if expires_at <= now:
                await message.answer(
                    '⚠️ Дата окончания не может быть в прошлом.\n'
                    'Введите новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ или 0 для бессрочного:',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_promocode')]])
                )
                return
            
            expires_text = f"до {expires_at.strftime('%d.%m.%Y %H:%M')}"
        except ValueError:
            from datetime import timedelta
            example_text = (datetime.now() + timedelta(days=7)).replace(hour=23, minute=59, second=0, microsecond=0).strftime('%d.%m.%Y %H:%M')
            await message.answer(
                '❌ Некорректный формат.\n'
                'Используйте ДД.ММ.ГГГГ ЧЧ:ММ или 0:',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_promocode')]])
            )
            return
    
    await state.update_data(expires_at=expires_at)
    
    # Создаём резюме
    data = await state.get_data()
    code = data.get('code')
    dtype = data.get('discount_type')
    dvalue = data.get('discount_value')
    limit = data.get('usage_limit')
    
    # Форматируем скидку для отображения
    discount_display = promo.format_discount(dtype, dvalue)
    dtype_text = 'Процент' if dtype == 'percentage' else 'Фиксированная'
    limit_text = f'{limit} использований' if limit else 'без лимита'
    
    text = f'''🔍 <b>Проверьте данные:</b>

• Код: <code>{code}</code>
• Тип: {dtype_text}
• Скидка: {discount_display}
• Лимит: {limit_text}
• Действует: {expires_text}'''
    
    await message.answer(
        text,
        parse_mode='html',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✅ Создать', callback_data='confirm_add_promocode')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_promocode')]
        ])
    )


@router.callback_query(F.data == 'confirm_add_promocode')
async def confirm_add_promocode(call: types.CallbackQuery, state: FSMContext):
    """Confirm and create promocode"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    data = await state.get_data()
    
    try:
        # Дополнительная проверка уникальности перед созданием
        code = data.get('code')
        if await promo.get_promocode_any(code):
            await call.answer('❌ Такой код уже существует. Укажите другой код.', show_alert=True)
            return

        # Создаём промокод
        await promo.create_promocode(
            code=code,
            discount_type=data.get('discount_type'),
            discount_value=data.get('discount_value'),
            usage_limit=data.get('usage_limit'),
            expires_at=data.get('expires_at')
        )
        
        await call.answer('✅ Промокод создан')
        await state.clear()
        
        # Возвращаемся в обновлённое меню промокодов со списком
        await promocodes_menu(call, state)
        
    except Exception as e:
        logging.error(f"Ошибка создания промокода: {e}")
        # Дружелюбное сообщение при нарушении уникальности
        err_text = str(e)
        if 'UNIQUE constraint failed' in err_text or 'UNIQUE constraint' in err_text:
            await call.answer('❌ Такой код уже существует. Выберите другой.', show_alert=True)
        else:
            await call.answer(f'❌ Ошибка: {err_text[:100]}', show_alert=True)


@router.callback_query(F.data == 'cancel_promocode')
async def cancel_promocode(call: types.CallbackQuery, state: FSMContext):
    """Cancel promocode creation/editing"""
    await state.clear()
    await call.answer('❌ Отменено')
    
    # Возвращаемся в обновлённое меню промокодов со списком
    await promocodes_menu(call, state)


# ===== TEXT SETTINGS HANDLERS =====

@router.callback_query(F.data == 'text_settings')
async def text_settings_menu(call: types.CallbackQuery, state: FSMContext):
    """Text settings menu - show scenes preview directly"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    await call.answer()
    await call.message.edit_text(
        '👀 Выберите экран для предпросмотра:',
        reply_markup=kb.markup_preview_scenes()
    )


# Удалён старый интерфейс выбора категорий/ключей в пользу предпросмотра сцен


# Удалён выбор конкретного ключа — редактирование теперь запускается из предпросмотра сцен


@router.message(FSMSettings.text_value)
async def save_text_value(message: types.Message, state: FSMContext):
    """Preview and confirm new text value before saving"""
    data = await state.get_data()
    category = data.get('text_category')
    key = data.get('text_key')
    new_value = message.text.strip()

    # Проверки доступности категории
    allowed_categories = ['buttons', 'messages']
    if category not in allowed_categories:
        await message.answer('❌ Категория недоступна для редактирования')
        await state.clear()
        return

    # Базовая валидация длины
    if len(new_value) > 4096:
        await message.answer(
            '❌ <b>Ошибка!</b>\n\nТекст слишком длинный (максимум 4096 символов).\nПопробуйте сократить текст.',
            parse_mode='html'
        )
        return

    # Для кнопок — короткий лимит
    if category == 'buttons' and len(new_value) > 64:
        await message.answer(
            '❌ <b>Ошибка!</b>\n\nТекст кнопки слишком длинный (максимум 64 символа).\nПопробуйте сократить текст.',
            parse_mode='html'
        )
        return

    # Опасные теги
    dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<form']
    if any(tag in new_value.lower() for tag in dangerous_tags):
        await message.answer(
            '❌ <b>Ошибка!</b>\n\nТекст содержит недопустимые HTML теги.\nРазрешены только: b, i, u, s, code, pre, a',
            parse_mode='html'
        )
        return

    # Получаем старое значение
    texts = utils.get_interface_texts()
    old_value = (texts.get(category, {}) or {}).get(key, '')

    # Анализ плейсхолдеров
    import re
    placeholder_pattern = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
    old_placeholders = set(placeholder_pattern.findall(str(old_value))) if isinstance(old_value, str) else set()
    new_placeholders = set(placeholder_pattern.findall(new_value))
    missing = [ph for ph in old_placeholders if ph not in new_placeholders]

    # Сохраняем в state для подтверждения
    await state.update_data(pending_text_value=new_value, old_text_value=old_value)
    await state.set_state(FSMSettings.text_confirm)

    # Формируем предпросмотр: пробуем подставить мок-данные
    mock_values = {
        'price': '19.99', 'price_usd': '19.99', 'price_stars': '1999',
        'final_price': '14.99', 'final_stars': '1499', 'discount': '5.00',
        'full_name': 'Иван Иванов', 'lessons_count': '3', 'title': 'Пример урока',
        'subject': 'Пример темы', 'ticket_id': '123', 'status': '🟢 Открыт', 'created_at': '2025-01-01'
    }
    preview_text = new_value
    try:
        preview_text = new_value.format(**mock_values)
    except Exception:
        # Если форматирование упало — показываем как есть
        preview_text = new_value

    # Собираем информативную карточку
    warn_missing = ("\n⚠️ Отсутствуют плейсхолдеры: " + ', '.join('{'+m+'}' for m in missing)) if missing else ''
    diff_header = "Было -> Стало"
    preview_card = (
        f"🧪 <b>Предпросмотр изменения</b>\n\n"
        f"Плейсхолдеры (старые): {', '.join('{'+p+'}' for p in sorted(old_placeholders)) or '—'}\n"
        f"Плейсхолдеры (новые): {', '.join('{'+p+'}' for p in sorted(new_placeholders)) or '—'}{warn_missing}\n\n"
        f"<b>{diff_header}</b>\n"
        f"<b>Было:</b>\n<code>{str(old_value)[:1000]}</code>\n\n"
        f"<b>Стало (как увидит пользователь):</b>\n{preview_text[:2000]}"
    )

    await message.answer(preview_card, parse_mode='html', reply_markup=kb.markup_text_confirm())


@router.callback_query(F.data == 'text_save_confirm')
async def text_save_confirm(call: types.CallbackQuery, state: FSMContext):
    """Confirm and persist pending text value; return to scene preview if editing initiated from preview"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return

    data = await state.get_data()
    category = data.get('text_category')
    key = data.get('text_key')
    new_value = data.get('pending_text_value')
    old_value = data.get('old_text_value', '')
    return_scene = data.get('return_scene')

    if not category or not key or new_value is None:
        await call.answer('⚠️ Нет данных для сохранения', show_alert=True)
        return

    texts = utils.get_interface_texts()
    if category not in texts:
        texts[category] = {}
    texts[category][key] = new_value
    utils.save_interface_texts(texts)

    # Аудит
    try:
        import json
        from datetime import datetime
        audit_log = {
            'timestamp': datetime.now().isoformat(),
            'admin_id': call.from_user.id,
            'admin_name': call.from_user.full_name,
            'category': category,
            'key': key,
            'old_value': old_value,
            'new_value': new_value
        }
        audit_file = 'json/text_edits_audit.json'
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            audit_data = []
        audit_data.append(audit_log)
        if len(audit_data) > 1000:
            audit_data = audit_data[-1000:]
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving audit log: {e}")

    await call.answer('✅ Сохранено')

    if return_scene:
        # Вернуться в предпросмотр сцены с обновлёнными текстами
        try:
            from text_meta import build_scene_preview
            text, markup = await build_scene_preview(return_scene)
            await call.message.edit_text(text, reply_markup=markup)
        except Exception as e:
            logging.error(f"Failed to return to scene preview {return_scene}: {e}")
            await call.message.edit_text('✅ Текст успешно сохранён!', reply_markup=kb.markup_text_categories())
        finally:
            await state.clear()
    else:
        await state.clear()
        await call.message.edit_text('✅ Текст успешно сохранён!', reply_markup=kb.markup_text_categories())


@router.callback_query(F.data == 'text_edit_again')
async def text_edit_again(call: types.CallbackQuery, state: FSMContext):
    """Return to editing the same key"""
    data = await state.get_data()
    category = data.get('text_category')
    key = data.get('text_key')
    await state.set_state(FSMSettings.text_value)
    await call.answer('✏️ Измените текст и отправьте заново')


@router.callback_query(F.data == 'text_cancel_edit')
async def text_cancel_edit(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer('↩️ Отменено')
    await call.message.edit_text('📝 Настройки текстов', reply_markup=kb.markup_text_categories())


@router.callback_query(F.data == 'scene_preview')
async def scene_preview_menu(call: types.CallbackQuery, state: FSMContext):
    """Top-level scenes preview menu"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    await call.answer()
    await call.message.edit_text('👀 Выберите экран для предпросмотра:', reply_markup=kb.markup_preview_scenes())


@router.callback_query(F.data.startswith('scene_preview:'))
async def scene_preview_build(call: types.CallbackQuery, state: FSMContext):
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    scene = call.data.split(':', 1)[1]
    from text_meta import build_scene_preview
    text, markup = await build_scene_preview(scene)
    await call.answer()
    await call.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data.startswith('preview_screen_for_key:'))
async def preview_screen_for_key(call: types.CallbackQuery, state: FSMContext):
    """Open scenes menu filtered by a key (simple: open generic scenes)"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    await call.answer()
    # Можно сразу открыть подходящую сцену, но пока оставим общее меню
    await call.message.edit_text('👀 Предпросмотр экранов', reply_markup=kb.markup_preview_scenes())


@router.callback_query(F.data.startswith('scene_edit_key:'))
async def scene_edit_key(call: types.CallbackQuery, state: FSMContext):
    """Начать редактирование кнопочного ключа прямо из предпросмотра"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    _, scene, category, key = call.data.split(':', 3)
    texts = utils.get_interface_texts()
    storage_key = key.replace('btn_', '') if key.startswith('btn_') else key
    current_value = texts.get('buttons', {}).get(storage_key, '') if category == 'buttons' else ''

    await state.update_data(text_category='buttons', text_key=storage_key, return_scene=scene)
    await state.set_state(FSMSettings.text_value)
    await call.answer()
    await call.message.edit_text(
        f"📝 <b>Редактирование кнопки</b>\n\nТекущее значение:\n<code>{current_value}</code>\n\n👉 Отправьте новый текст для кнопки:",
        parse_mode='html'
    )


@router.callback_query(F.data.startswith('scene_edit_message:'))
async def scene_edit_message(call: types.CallbackQuery, state: FSMContext):
    """Начать редактирование текстового ключа экрана прямо из предпросмотра"""
    data_admins = utils.get_admins()
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    _, scene, dotted_key = call.data.split(':', 2)
    # dotted_key вида messages.welcome -> category=messages, key=welcome
    if '.' in dotted_key:
        category, key = dotted_key.split('.', 1)
    else:
        category, key = 'messages', dotted_key

    texts = utils.get_interface_texts()
    current_value = texts.get(category, {}).get(key, '')
    await state.update_data(text_category=category, text_key=key, return_scene=scene)
    await state.set_state(FSMSettings.text_value)

    await call.answer()
    await call.message.edit_text(
        f"📝 <b>Редактирование текста</b>\n\nТекущее значение:\n<code>{current_value}</code>\n\n👉 Отправьте новый текст:",
        parse_mode='html'
    )


# ===== CURRENCY RATE HANDLERS =====

@router.callback_query(F.data == 'currency_rate')
async def currency_rate_menu(call: types.CallbackQuery, state: FSMContext):
    """Currency rate settings - ADMIN ONLY"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    # Получаем текущий курс
    current_rate = await s.get_usd_to_stars_rate()
    
    await state.set_state(FSMSettings.currency_rate)
    await call.answer()
    await call.message.edit_text(
        f'''💱 <b>Настройка курса валют</b>

Текущий курс: 1 USD = {current_rate} ⭐ Stars

👉 Введите новый курс (количество Stars за 1 USD):''',
        parse_mode='html'
    )


@router.message(FSMSettings.currency_rate)
async def save_currency_rate(message: types.Message, state: FSMContext):
    """Save new currency rate"""
    try:
        new_rate = float(message.text.strip())
        if new_rate <= 0:
            await message.answer('❌ Курс должен быть положительным числом. Попробуйте еще раз:')
            return
        
        # Сохраняем новый курс
        await s.set_usd_to_stars_rate(new_rate)
        
        await state.clear()
        await message.answer(
            f'''✅ <b>Курс валют обновлен!</b>

Новый курс: 1 USD = {new_rate} ⭐ Stars

Все цены в боте будут автоматически пересчитаны по новому курсу.''',
            parse_mode='html',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='↪️ Назад', callback_data='settings')]
            ])
        )
    except ValueError:
        await message.answer('❌ Неверный формат. Введите число (например: 50 или 75.5):')


# ===== STATISTICS HANDLERS =====

@router.callback_query(F.data == 'statistics')
async def statistics_menu(call: types.CallbackQuery, state: FSMContext):
    """Statistics menu - ADMIN ONLY"""
    data_admins = utils.get_admins()
    
    if(call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins):
        await call.answer('⚠️ Ошибка доступа')
        return
    
    # Собираем статистику
    from database import user as user_module
    from datetime import datetime, timedelta
    
    # Пользователи
    total_users = await u.get_total_users()
    today_users = await u.get_users_count_since(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
    week_users = await u.get_users_count_since(datetime.now() - timedelta(days=7))
    
    # Продажи
    total_sales = await p.get_sales_stats()
    today_sales = await p.get_sales_stats_period(1)
    week_sales = await p.get_sales_stats_period(7)
    
    # Уроки
    total_lessons = len(await l.get_all_lessons(active_only=False))
    active_lessons = len(await l.get_all_lessons(active_only=True))
    
    # Промокоды
    total_promocodes = len(await promo.get_all_promocodes())
    
    text = f'''📊 <b>Статистика бота</b>

👥 <b>Пользователи:</b>
├ Всего: {total_users}
├ За сегодня: +{today_users}
└ За неделю: +{week_users}

💰 <b>Продажи:</b>
├ Всего: {total_sales['count']} шт (${total_sales['total']:.2f})
├ За сегодня: {today_sales['count']} шт (${today_sales['total']:.2f})
└ За неделю: {week_sales['count']} шт (${week_sales['total']:.2f})

📚 <b>Уроки:</b>
├ Всего: {total_lessons}
└ Активных: {active_lessons}

🎫 <b>Промокоды:</b> {total_promocodes}'''
    
    await call.answer()
    await call.message.edit_text(
        text,
        parse_mode='html',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')]
        ])
    )


# ===== ONBOARDING STEPS CONSTRUCTOR =====

from database.onboarding import OnboardingStep, OnboardingOption

ALLOWED_ONB_TYPES = ('screen', 'single_choice', 'multi_choice', 'consent')


def _build_onb_steps_kb(steps):
    rows = []
    for s in steps:
        actions = [
            InlineKeyboardButton(text='✏️', callback_data=f'onb_step_edit:{s.id}'),
        ]
        # move up/down
        actions.append(InlineKeyboardButton(text='🔼', callback_data=f'onb_move:{s.id}:up'))
        actions.append(InlineKeyboardButton(text='🔽', callback_data=f'onb_move:{s.id}:down'))
        # options only if not screen
        if s.type != 'screen':
            actions.append(InlineKeyboardButton(text='🧩', callback_data=f'onb_opts:{s.id}'))
        actions.append(InlineKeyboardButton(text='🗑️', callback_data=f'onb_step_delete:{s.id}'))
        rows.append(actions)
    rows.append([InlineKeyboardButton(text='➕ Добавить шаг', callback_data='onb_step_add')])
    rows.append([InlineKeyboardButton(text='↪️ Назад', callback_data='onboarding_admin')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_onb_steps_text(steps):
    lines = ["🧱 <b>Конструктор онбординга</b>", "\nШаги (в порядке выполнения):\n"]
    for idx, s in enumerate(steps, start=1):
        status = ('✅' if s.enabled else '🚫') + ('•' + ('❗' if s.required else '—'))
        lines.append(f"{idx}. <code>{s.key}</code> — type: <b>{s.type}</b>, order: {s.order}, text: <code>{s.text_key or '—'}</code> {status}")
    if not steps:
        lines.append('📭 Шагов пока нет. Добавьте первый шаг!')
    return '\n'.join(lines)


@router.callback_query(F.data == 'onb_steps')
async def onb_steps(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    steps = (OnboardingStep.select().order_by(OnboardingStep.order.asc()))
    text = _format_onb_steps_text(list(steps))
    kb_local = _build_onb_steps_kb(list(steps))
    await call.message.edit_text(text, parse_mode='html', reply_markup=kb_local)


@router.callback_query(F.data == 'onb_step_add')
async def onb_step_add(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(FSMOnboardingAdmin.add_key)
    await call.message.edit_text('✏️ Введите ключ шага (латинские буквы, цифры и _):\n\nНапример: <code>welcome</code>, <code>goal</code>', parse_mode='html')


@router.message(FSMOnboardingAdmin.add_key)
async def onb_add_key(message: types.Message, state: FSMContext):
    import re
    key = (message.text or '').strip().lower()
    if not re.match(r'^[a-z0-9_]+$', key):
        await message.answer('❌ Некорректный ключ. Разрешены латинские буквы, цифры и нижнее подчеркивание. Повторите ввод:')
        return
    # uniqueness
    if OnboardingStep.select().where(OnboardingStep.key == key).exists():
        await message.answer('❌ Такой ключ уже существует. Введите другой:')
        return
    await state.update_data(new_step_key=key)
    # ask type via inline
    kb_types = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='ℹ️ screen', callback_data='onb_add_type:screen')],
        [InlineKeyboardButton(text='🔘 single_choice', callback_data='onb_add_type:single_choice')],
        [InlineKeyboardButton(text='☑ multi_choice', callback_data='onb_add_type:multi_choice')],
        [InlineKeyboardButton(text='✅ consent', callback_data='onb_add_type:consent')]
    ])
    await message.answer('🧩 Выберите тип шага:', reply_markup=kb_types)


@router.callback_query(F.data.startswith('onb_add_type:'))
async def onb_add_type(call: types.CallbackQuery, state: FSMContext):
    t = call.data.split(':', 1)[1]
    if t not in ALLOWED_ONB_TYPES:
        await call.answer('❌ Недопустимый тип')
        return
    await state.update_data(new_step_type=t)
    await state.set_state(FSMOnboardingAdmin.add_order)
    await call.answer()
    await call.message.edit_text('🔢 Введите порядковый номер шага (целое число).\nОтправьте 0, чтобы поставить в конец.')


@router.message(FSMOnboardingAdmin.add_order)
async def onb_add_order(message: types.Message, state: FSMContext):
    try:
        order = int((message.text or '').strip())
    except Exception:
        await message.answer('❌ Нужно целое число. Попробуйте снова:')
        return
    # compute last if 0 or less
    if order <= 0:
        last = OnboardingStep.select().order_by(OnboardingStep.order.desc()).first()
        order = (last.order + 1) if last else 1
    await state.update_data(new_step_order=order)
    await state.set_state(FSMOnboardingAdmin.add_text_key)
    await message.answer('📝 Введите ключ текста для шага (например: <code>onboarding.welcome</code>) или отправьте <code>/skip</code>:', parse_mode='html')


@router.message(FSMOnboardingAdmin.add_text_key)
async def onb_add_text_key(message: types.Message, state: FSMContext):
    text_key_raw = (message.text or '').strip()
    text_key = None if text_key_raw == '/skip' else text_key_raw
    data = await state.get_data()
    key = data.get('new_step_key')
    t = data.get('new_step_type')
    order = data.get('new_step_order')
    # required default: screens not required, others required
    required_default = False if t == 'screen' else True
    try:
        OnboardingStep.create(key=key, type=t, order=order, text_key=text_key, enabled=True, required=required_default)
        await message.answer('✅ Шаг создан')
    except Exception as e:
        await message.answer(f'❌ Ошибка создания: {e}')
    await state.clear()
    # Show list
    steps = (OnboardingStep.select().order_by(OnboardingStep.order.asc()))
    await message.answer(_format_onb_steps_text(list(steps)), parse_mode='html', reply_markup=_build_onb_steps_kb(list(steps)))


@router.callback_query(F.data.startswith('onb_move:'))
async def onb_step_move(call: types.CallbackQuery, state: FSMContext):
    _, sid, direction = call.data.split(':', 2)
    try:
        sid = int(sid)
        step = OnboardingStep.get_by_id(sid)
    except Exception:
        await call.answer('❌ Шаг не найден', show_alert=True)
        return
    steps = list(OnboardingStep.select().order_by(OnboardingStep.order.asc()))
    idx = next((i for i, s in enumerate(steps) if s.id == sid), -1)
    if idx == -1:
        await call.answer('❌ Не найдено')
        return
    if direction == 'up' and idx > 0:
        other = steps[idx - 1]
    elif direction == 'down' and idx < len(steps) - 1:
        other = steps[idx + 1]
    else:
        await call.answer()
        return
    # swap orders
    step_order, other_order = step.order, other.order
    step.order, other.order = other_order, step_order
    step.save()
    other.save()
    await call.answer('✅ Порядок обновлён')
    await onb_steps(call, state)


@router.callback_query(F.data.startswith('onb_step_delete:'))
async def onb_step_delete_confirm(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[1])
    try:
        step = OnboardingStep.get_by_id(sid)
    except Exception:
        await call.answer('❌ Шаг не найден', show_alert=True)
        return
    kb_local = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Удалить', callback_data=f'onb_step_del_yes:{sid}')],
        [InlineKeyboardButton(text='↩️ Отмена', callback_data='onb_steps')]
    ])
    await call.answer()
    await call.message.edit_text(f"❗ Подтвердите удаление шага <code>{step.key}</code>", parse_mode='html', reply_markup=kb_local)


@router.callback_query(F.data.startswith('onb_step_del_yes:'))
async def onb_step_delete(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[1])
    try:
        step = OnboardingStep.get_by_id(sid)
        step.delete_instance(recursive=True)
        await call.answer('✅ Удалено')
    except Exception as e:
        await call.answer(f'❌ Ошибка: {e}', show_alert=True)
    await onb_steps(call, state)


@router.callback_query(F.data.startswith('onb_step_edit:'))
async def onb_step_edit(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[1])
    try:
        step = OnboardingStep.get_by_id(sid)
    except Exception:
        await call.answer('❌ Шаг не найден', show_alert=True)
        return
    # Build edit menu
    text = (
        f"✏️ <b>Редактирование шага</b>\n\n"
        f"key: <code>{step.key}</code>\n"
        f"type: <b>{step.type}</b>\n"
        f"order: <b>{step.order}</b>\n"
        f"text_key: <code>{step.text_key or '—'}</code>\n"
        f"enabled: {'✅' if step.enabled else '🚫'}\n"
        f"required: {'❗' if step.required else '—'}\n"
    )
    rows = [
        [InlineKeyboardButton(text='📝 Ключ', callback_data=f'onb_field:KEY:{sid}'), InlineKeyboardButton(text='🔢 Порядок', callback_data=f'onb_field:ORDER:{sid}')],
        [InlineKeyboardButton(text='🧩 Тип', callback_data=f'onb_field:TYPE:{sid}'), InlineKeyboardButton(text='📝 Текстовый ключ', callback_data=f'onb_field:TEXT_KEY:{sid}')],
        [InlineKeyboardButton(text=('✅ Включить' if not step.enabled else '🚫 Выключить'), callback_data=f'onb_toggle:enabled:{sid}')],
        [InlineKeyboardButton(text=('❗ Обязательный' if not step.required else '— Необязательный'), callback_data=f'onb_toggle:required:{sid}')],
    ]
    if step.type != 'screen':
        rows.append([InlineKeyboardButton(text='🧩 Опции', callback_data=f'onb_opts:{sid}')])
    rows.append([InlineKeyboardButton(text='↪️ Назад', callback_data='onb_steps')])
    await call.answer()
    await call.message.edit_text(text, parse_mode='html', reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith('onb_field:TYPE:'))
async def onb_step_change_type_prompt(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[2])
    kb_types = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='ℹ️ screen', callback_data=f'onb_change_type:{sid}:screen')],
        [InlineKeyboardButton(text='🔘 single_choice', callback_data=f'onb_change_type:{sid}:single_choice')],
        [InlineKeyboardButton(text='☑ multi_choice', callback_data=f'onb_change_type:{sid}:multi_choice')],
        [InlineKeyboardButton(text='✅ consent', callback_data=f'onb_change_type:{sid}:consent')],
        [InlineKeyboardButton(text='↩️ Отмена', callback_data=f'onb_step_edit:{sid}')]
    ])
    await call.answer()
    await call.message.edit_text('🧩 Выберите новый тип:', reply_markup=kb_types)


@router.callback_query(F.data.startswith('onb_change_type:'))
async def onb_step_change_type(call: types.CallbackQuery, state: FSMContext):
    _, sid, t = call.data.split(':', 2)
    sid = int(sid)
    if t not in ALLOWED_ONB_TYPES:
        await call.answer('❌ Недопустимый тип')
        return
    try:
        step = OnboardingStep.get_by_id(sid)
        step.type = t
        step.save()
        await call.answer('✅ Тип обновлён')
    except Exception as e:
        await call.answer(f'❌ Ошибка: {e}', show_alert=True)
    await onb_step_edit(call, state)


@router.callback_query(F.data.startswith('onb_field:KEY:'))
async def onb_step_edit_key(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[2])
    await state.update_data(edit_step_id=sid, edit_field='KEY')
    await state.set_state(FSMOnboardingAdmin.edit_value)
    await call.answer()
    await call.message.edit_text('✏️ Введите новый ключ шага (латиница/цифры/_):')


@router.callback_query(F.data.startswith('onb_field:ORDER:'))
async def onb_step_edit_order(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[2])
    await state.update_data(edit_step_id=sid, edit_field='ORDER')
    await state.set_state(FSMOnboardingAdmin.edit_value)
    await call.answer()
    await call.message.edit_text('🔢 Введите новый порядковый номер (целое число):')


@router.callback_query(F.data.startswith('onb_field:TEXT_KEY:'))
async def onb_step_edit_text_key(call: types.CallbackQuery, state: FSMContext):
    sid = int(call.data.split(':')[2])
    await state.update_data(edit_step_id=sid, edit_field='TEXT_KEY')
    await state.set_state(FSMOnboardingAdmin.edit_value)
    await call.answer()
    await call.message.edit_text('📝 Введите новый текстовый ключ (например: onboarding.welcome) или /skip, чтобы очистить:')


@router.message(FSMOnboardingAdmin.edit_value)
async def onb_step_edit_value_save(message: types.Message, state: FSMContext):
    import re
    data = await state.get_data()
    sid = data.get('edit_step_id')
    field = data.get('edit_field')
    try:
        step = OnboardingStep.get_by_id(sid)
    except Exception:
        await state.clear()
        await message.answer('❌ Шаг не найден')
        return
    text = (message.text or '').strip()
    try:
        if field == 'KEY':
            if not re.match(r'^[a-z0-9_]+$', text.lower()):
                await message.answer('❌ Некорректный ключ. Повторите:')
                return
            if OnboardingStep.select().where((OnboardingStep.key == text) & (OnboardingStep.id != sid)).exists():
                await message.answer('❌ Такой ключ уже используется. Введите другой:')
                return
            step.key = text
        elif field == 'ORDER':
            new_order = int(text)
            if new_order <= 0:
                new_order = 1
            step.order = new_order
        elif field == 'TEXT_KEY':
            if text == '/skip':
                step.text_key = None
            else:
                step.text_key = text
        step.save()
        await message.answer('✅ Сохранено')
    except ValueError:
        await message.answer('❌ Нужно целое число')
        return
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
    await state.clear()
    # Return to edit screen
    # Send a callback-like refresh by rebuilding list view
    steps = (OnboardingStep.select().order_by(OnboardingStep.order.asc()))
    await message.answer(_format_onb_steps_text(list(steps)), parse_mode='html', reply_markup=_build_onb_steps_kb(list(steps)))


@router.callback_query(F.data.startswith('onb_toggle:'))
async def onb_step_toggle(call: types.CallbackQuery, state: FSMContext):
    _, field, sid = call.data.split(':', 2)
    sid = int(sid)
    try:
        step = OnboardingStep.get_by_id(sid)
        if field == 'enabled':
            step.enabled = not step.enabled
        elif field == 'required':
            step.required = not step.required
        step.save()
        await call.answer('✅ Обновлено')
    except Exception as e:
        await call.answer(f'❌ Ошибка: {e}', show_alert=True)
    await onb_step_edit(call, state)


# ===== OPTIONS MANAGEMENT =====

def _build_onb_options_kb(step_id, options):
    rows = []
    for o in options:
        rows.append([
            InlineKeyboardButton(text='✏️', callback_data=f'onb_opt_edit:{o.id}'),
            InlineKeyboardButton(text='🔼', callback_data=f'onb_opt_move:{o.id}:up'),
            InlineKeyboardButton(text='🔽', callback_data=f'onb_opt_move:{o.id}:down'),
            InlineKeyboardButton(text=('✅ Вкл' if not o.enabled else '🚫 Выкл'), callback_data=f'onb_opt_toggle:{o.id}'),
            InlineKeyboardButton(text='🗑️', callback_data=f'onb_opt_delete:{o.id}')
        ])
    rows.append([InlineKeyboardButton(text='➕ Добавить опцию', callback_data=f'onb_opt_add:{step_id}')])
    rows.append([InlineKeyboardButton(text='↪️ Назад к шагу', callback_data=f'onb_step_edit:{step_id}')])
    rows.append([InlineKeyboardButton(text='🏗️ Шаги', callback_data='onb_steps')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_onb_options_text(step, options):
    lines = [f"🧩 <b>Опции шага</b> <code>{step.key}</code> (type: {step.type})\n"]
    if not options:
        lines.append('📭 Опций пока нет')
    for idx, o in enumerate(options, start=1):
        lines.append(f"{idx}. value: <code>{o.value}</code>, text_key: <code>{o.text_key}</code>, order: {o.order}, enabled: {'✅' if o.enabled else '🚫'}")
    return '\n'.join(lines)


@router.callback_query(F.data.startswith('onb_opts:'))
async def onb_opts(call: types.CallbackQuery, state: FSMContext):
    step_id = int(call.data.split(':')[1])
    try:
        step = OnboardingStep.get_by_id(step_id)
    except Exception:
        await call.answer('❌ Шаг не найден', show_alert=True)
        return
    options = list(OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.asc()))
    await call.answer()
    await call.message.edit_text(_format_onb_options_text(step, options), parse_mode='html', reply_markup=_build_onb_options_kb(step_id, options))


@router.callback_query(F.data.startswith('onb_opt_add:'))
async def onb_opt_add(call: types.CallbackQuery, state: FSMContext):
    step_id = int(call.data.split(':')[1])
    await state.update_data(add_opt_step_id=step_id)
    await state.set_state(FSMOnboardingOption.add_value)
    await call.answer()
    await call.message.edit_text('✏️ Введите value опции (латиница/цифры/_):')


@router.message(FSMOnboardingOption.add_value)
async def onb_opt_add_value(message: types.Message, state: FSMContext):
    import re
    val = (message.text or '').strip().lower()
    if not re.match(r'^[a-z0-9_]+$', val):
        await message.answer('❌ Некорректное value. Повторите:')
        return
    data = await state.get_data()
    step_id = data.get('add_opt_step_id')
    step = OnboardingStep.get_by_id(step_id)
    if OnboardingOption.select().where((OnboardingOption.step == step) & (OnboardingOption.value == val)).exists():
        await message.answer('❌ Такая опция уже существует для этого шага. Введите другое значение:')
        return
    await state.update_data(add_opt_value=val)
    await state.set_state(FSMOnboardingOption.add_text_key)
    await message.answer('📝 Введите текстовый ключ для опции (например: onboarding.goal.option.quick_start):')


@router.message(FSMOnboardingOption.add_text_key)
async def onb_opt_add_text_key(message: types.Message, state: FSMContext):
    text_key = (message.text or '').strip()
    if not text_key:
        await message.answer('❌ Текстовый ключ обязателен. Введите:')
        return
    await state.update_data(add_opt_text_key=text_key)
    await state.set_state(FSMOnboardingOption.add_order)
    await message.answer('🔢 Введите порядковый номер опции (целое число, 0 — в конец):')


@router.message(FSMOnboardingOption.add_order)
async def onb_opt_add_order(message: types.Message, state: FSMContext):
    try:
        order = int((message.text or '').strip())
    except Exception:
        await message.answer('❌ Нужно целое число. Повторите:')
        return
    data = await state.get_data()
    step_id = data.get('add_opt_step_id')
    step = OnboardingStep.get_by_id(step_id)
    if order <= 0:
        last = (OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.desc()).first())
        order = (last.order + 1) if last else 1
    try:
        OnboardingOption.create(step=step, value=data.get('add_opt_value'), text_key=data.get('add_opt_text_key'), order=order, enabled=True)
        await message.answer('✅ Опция добавлена')
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
    await state.clear()
    # Show options
    options = list(OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.asc()))
    await message.answer(_format_onb_options_text(step, options), parse_mode='html', reply_markup=_build_onb_options_kb(step_id, options))


@router.callback_query(F.data.startswith('onb_opt_toggle:'))
async def onb_opt_toggle(call: types.CallbackQuery, state: FSMContext):
    oid = int(call.data.split(':')[1])
    try:
        opt = OnboardingOption.get_by_id(oid)
        opt.enabled = not opt.enabled
        opt.save()
        await call.answer('✅ Обновлено')
        await onb_opts(call, state)
    except Exception as e:
        await call.answer(f'❌ Ошибка: {e}', show_alert=True)


@router.callback_query(F.data.startswith('onb_opt_move:'))
async def onb_opt_move(call: types.CallbackQuery, state: FSMContext):
    _, oid, direction = call.data.split(':', 2)
    oid = int(oid)
    try:
        opt = OnboardingOption.get_by_id(oid)
        step = opt.step
    except Exception:
        await call.answer('❌ Опция не найдена', show_alert=True)
        return
    options = list(OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.asc()))
    idx = next((i for i, o in enumerate(options) if o.id == oid), -1)
    if idx == -1:
        await call.answer()
        return
    if direction == 'up' and idx > 0:
        other = options[idx - 1]
    elif direction == 'down' and idx < len(options) - 1:
        other = options[idx + 1]
    else:
        await call.answer()
        return
    opt.order, other.order = other.order, opt.order
    opt.save(); other.save()
    await call.answer('✅ Порядок обновлён')
    await onb_opts(call, state)


@router.callback_query(F.data.startswith('onb_opt_delete:'))
async def onb_opt_delete(call: types.CallbackQuery, state: FSMContext):
    oid = int(call.data.split(':')[1])
    try:
        opt = OnboardingOption.get_by_id(oid)
        step_id = opt.step.id
        opt.delete_instance()
        await call.answer('✅ Удалено')
        # refresh
        step = OnboardingStep.get_by_id(step_id)
        options = list(OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.asc()))
        await call.message.edit_text(_format_onb_options_text(step, options), parse_mode='html', reply_markup=_build_onb_options_kb(step_id, options))
    except Exception as e:
        await call.answer(f'❌ Ошибка: {e}', show_alert=True)


@router.callback_query(F.data.startswith('onb_opt_edit:'))
async def onb_opt_edit(call: types.CallbackQuery, state: FSMContext):
    oid = int(call.data.split(':')[1])
    try:
        opt = OnboardingOption.get_by_id(oid)
    except Exception:
        await call.answer('❌ Опция не найдена', show_alert=True)
        return
    text = (
        f"✏️ <b>Опция</b>\n\n"
        f"value: <code>{opt.value}</code>\n"
        f"text_key: <code>{opt.text_key}</code>\n"
        f"order: <b>{opt.order}</b>\n"
        f"enabled: {'✅' if opt.enabled else '🚫'}\n"
    )
    rows = [
        [InlineKeyboardButton(text='📝 value', callback_data=f'onb_opt_field:VALUE:{oid}'), InlineKeyboardButton(text='📝 text_key', callback_data=f'onb_opt_field:TEXT_KEY:{oid}')],
        [InlineKeyboardButton(text='🔢 Порядок', callback_data=f'onb_opt_field:ORDER:{oid}')],
        [InlineKeyboardButton(text=('✅ Вкл' if not opt.enabled else '🚫 Выкл'), callback_data=f'onb_opt_toggle:{oid}')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data=f'onb_opts:{opt.step.id}')]
    ]
    await call.answer()
    await call.message.edit_text(text, parse_mode='html', reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.callback_query(F.data.startswith('onb_opt_field:'))
async def onb_opt_field_edit(call: types.CallbackQuery, state: FSMContext):
    _, field, oid = call.data.split(':', 2)
    oid = int(oid)
    await state.update_data(edit_opt_id=oid, edit_opt_field=field)
    await state.set_state(FSMOnboardingOption.edit_value)
    await call.answer()
    if field == 'VALUE':
        await call.message.edit_text('✏️ Введите новое value (латиница/цифры/_):')
    elif field == 'TEXT_KEY':
        await call.message.edit_text('📝 Введите новый text_key:')
    else:
        await call.message.edit_text('🔢 Введите новый порядок (целое число):')


@router.message(FSMOnboardingOption.edit_value)
async def onb_opt_edit_value_save(message: types.Message, state: FSMContext):
    import re
    data = await state.get_data()
    oid = int(data.get('edit_opt_id'))
    field = data.get('edit_opt_field')
    try:
        opt = OnboardingOption.get_by_id(oid)
    except Exception:
        await state.clear()
        await message.answer('❌ Опция не найдена')
        return
    text = (message.text or '').strip()
    try:
        if field == 'VALUE':
            if not re.match(r'^[a-z0-9_]+$', text.lower()):
                await message.answer('❌ Некорректное value. Повторите:')
                return
            # uniqueness within step
            if (OnboardingOption.select()
                .where((OnboardingOption.step == opt.step) & (OnboardingOption.value == text) & (OnboardingOption.id != oid))
               ).exists():
                await message.answer('❌ Такое value уже используется в этом шаге. Другое:')
                return
            opt.value = text
        elif field == 'TEXT_KEY':
            if not text:
                await message.answer('❌ text_key обязателен')
                return
            opt.text_key = text
        else:  # ORDER
            new_order = int(text)
            if new_order <= 0:
                new_order = 1
            opt.order = new_order
        opt.save()
        await message.answer('✅ Сохранено')
    except ValueError:
        await message.answer('❌ Нужен целый номер')
        return
    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}')
    step = opt.step
    await state.clear()
    options = list(OnboardingOption.select().where(OnboardingOption.step == step).order_by(OnboardingOption.order.asc()))
    await message.answer(_format_onb_options_text(step, options), parse_mode='html', reply_markup=_build_onb_options_kb(step.id, options))


# End of file
