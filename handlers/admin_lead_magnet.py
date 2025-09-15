"""Admin handlers for lead magnet management with multi-content support"""
import logging
import config
import utils
import keyboards as kb
from aiogram import Bot, types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states import FSMLeadMagnet
from database.lead_magnet import LeadMagnet
from bot_instance import bot

router = Router()

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
)


def markup_content_type_selection():
    """Content type selection menu"""
    items = [
        [InlineKeyboardButton(text='🎬 Видео', callback_data='lead_select_video')],
        [InlineKeyboardButton(text='🖼️ Фото', callback_data='lead_select_photo')],
        [InlineKeyboardButton(text='📁 Файл/Документ', callback_data='lead_select_document')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_lead_edit')]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lead_magnet_menu(is_enabled: bool, content_type: str = None, has_content: bool = False):
    """Lead magnet management menu keyboard - ALWAYS IN RUSSIAN"""
    toggle_text = "🔴 Выключить" if is_enabled else "🟢 Включить"
    
    items = [
        [InlineKeyboardButton(text=toggle_text, callback_data='lead_toggle')],
        [InlineKeyboardButton(text='✏️ Изменить приветственный текст', callback_data='lead_edit_text')],
    ]
    
    # Динамическая кнопка для контента
    if not has_content:
        items.append([InlineKeyboardButton(text='📎 Добавить контент', callback_data='lead_add_content')])
    else:
        items.append([InlineKeyboardButton(text='📎 Изменить загружаемый контент', callback_data='lead_edit_content')])
    
    items.append([InlineKeyboardButton(text='🏷️ Изменить название в «Моих уроках»', callback_data='lead_edit_label')])
    
    if has_content:
        items.append([InlineKeyboardButton(text='👁️ Предпросмотр', callback_data='lead_preview')])
    
    items.append([InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')])
    
    return InlineKeyboardMarkup(inline_keyboard=items)


# =============================================================================
# ОСНОВНОЕ МЕНЮ И НАВИГАЦИЯ
# =============================================================================

@router.callback_query(F.data == 'lead_magnet')
async def lead_magnet_menu(call: types.CallbackQuery, state: FSMContext):
    """Lead magnet management menu"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')
        return
    
    await call.answer()
    
    # Get current lead magnet configuration
    lead_magnet = await LeadMagnet.get_lead_magnet()
    if not lead_magnet:
        await call.message.edit_text(
            '❌ Ошибка загрузки конфигурации лид-магнита',
            reply_markup=kb.markup_admin_shop(call.from_user.id)
        )
        return
    
    # Определяем наличие контента (медиа и документ отдельно)
    media_type, media_id, doc_id = await LeadMagnet.get_content_bundle()
    has_media = media_id is not None
    has_doc = doc_id is not None
    
    if has_media:
        media_status = '🎬 Видео загружено' if media_type == 'video' else '🖼️ Фото загружено'
    else:
        media_status = '❌ Медиа не загружено'
    doc_status = '📁 Файл загружен' if has_doc else '❌ Файл не загружен'
    
    text = f"""
🎬 <b>Управление лид-магнитом</b>

Лид-магнит — это вводной контент, который показывается новым пользователям при первом входе в бота.
Теперь можно загрузить медиа (видео или фото) и дополнительно документ.

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
{media_status}
{doc_status}

Выберите действие:
"""
    
    await call.message.edit_text(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled, 
            content_type,
            has_content
        ),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'lead_toggle')
async def lead_toggle(call: types.CallbackQuery, state: FSMContext):
    """Toggle lead magnet on/off"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer("⚠️ Нет доступа")
        return
    
    lead_magnet = await LeadMagnet.get_lead_magnet()
    if not lead_magnet:
        await call.answer("❌ Ошибка")
        return
    
    # Check if content exists before enabling
    content_type, file_id = await LeadMagnet.get_current_content()
    if not lead_magnet.enabled and not file_id:
        await call.answer("❌ Сначала загрузите контент!", show_alert=True)
        return
    
    # Toggle status
    new_status = not lead_magnet.enabled
    success = await LeadMagnet.set_enabled(new_status)
    
    if success:
        await call.answer(f"✅ Лид-магнит {'включен' if new_status else 'выключен'}")
        # Refresh menu
        await lead_magnet_menu(call, state)
    else:
        await call.answer("❌ Ошибка изменения статуса")


# =============================================================================
# НОВЫЕ ОБРАБОТЧИКИ ДЛЯ ВЫБОРА ТИПА КОНТЕНТА
# =============================================================================

@router.callback_query(F.data == 'lead_add_content')
@router.callback_query(F.data == 'lead_edit_content')
async def lead_content_menu(call: types.CallbackQuery, state: FSMContext):
    """Show content type selection menu"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    await state.set_state(FSMLeadMagnet.selecting_content_type)
    
    await call.message.edit_text(
        """📎 <b>Выбор типа контента</b>

Выберите, какой тип контента вы хотите загрузить:

🎬 <b>Видео</b> - обучающие видеоролики
🖼️ <b>Фото</b> - инфографика, схемы, иллюстрации
📁 <b>Файл</b> - PDF, документы, презентации

📝 <b>Ссылки</b> можно указать в приветственном тексте.""",
        reply_markup=markup_content_type_selection(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'lead_select_video')
async def lead_select_video(call: types.CallbackQuery, state: FSMContext):
    """Start video upload"""
    await call.answer()
    await state.set_state(FSMLeadMagnet.uploading_video)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        """🎬 <b>Загрузка видео</b>

Отправьте видео, которое будет показываться новым пользователям.

⚠️ Требования:
• Формат: MP4
• Максимальный размер: 50 МБ
• Рекомендуемая длительность: до 2 минут""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'lead_select_photo')
async def lead_select_photo(call: types.CallbackQuery, state: FSMContext):
    """Start photo upload"""
    await call.answer()
    await state.set_state(FSMLeadMagnet.uploading_photo)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        """🖼️ <b>Загрузка фото</b>

Отправьте фото, которое будет показываться новым пользователям.

⚠️ Требования:
• Формат: JPG, PNG
• Максимальный размер: 10 МБ
• Рекомендуемое разрешение: 1080x1920 или меньше""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'lead_select_document')
async def lead_select_document(call: types.CallbackQuery, state: FSMContext):
    """Start document upload"""
    await call.answer()
    await state.set_state(FSMLeadMagnet.uploading_document)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        """📁 <b>Загрузка файла/документа</b>

Отправьте файл, который будет показываться новым пользователям.

⚠️ Требования:
• Формат: PDF, DOC, DOCX, TXT, и др.
• Максимальный размер: 20 МБ
• Рекомендация: добавьте описание в приветственный текст""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


# =============================================================================
# ОБРАБОТЧИКИ ЗАГРУЗКИ КОНТЕНТА
# =============================================================================

@router.message(FSMLeadMagnet.uploading_video)
async def process_video(message: types.Message, state: FSMContext):
    """Process uploaded video"""
    if message.content_type != 'video':
        await message.answer("❌ Отправьте видео файл")
        return
    
    video = message.video
    
    # Check video size (50 MB limit)
    if video.file_size > 50 * 1024 * 1024:
        await message.answer("❌ Видео слишком большое. Максимум 50 МБ.")
        return
    
    # Save video preserving document
    success = await LeadMagnet.set_media('video', video.file_id)
    
    if success:
        await message.answer("✅ Видео успешно загружено!")
    else:
        await message.answer("❌ Ошибка сохранения видео")
    
    await state.clear()
    
    # Возврат в меню
    await _return_to_main_menu(message)


@router.message(FSMLeadMagnet.uploading_photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Process uploaded photo"""
    if message.content_type != 'photo':
        await message.answer("❌ Отправьте фото")
        return
    
    photo = message.photo[-1]  # Получаем фото максимального размера
    
    # Check photo size (10 MB limit)
    if photo.file_size and photo.file_size > 10 * 1024 * 1024:
        await message.answer("❌ Фото слишком большое. Максимум 10 МБ.")
        return
    
    # Save photo preserving document
    success = await LeadMagnet.set_media('photo', photo.file_id)
    
    if success:
        await message.answer("✅ Фото успешно загружено!")
    else:
        await message.answer("❌ Ошибка сохранения фото")
    
    await state.clear()
    
    # Возврат в меню
    await _return_to_main_menu(message)


@router.message(FSMLeadMagnet.uploading_document)
async def process_document(message: types.Message, state: FSMContext):
    """Process uploaded document"""
    if message.content_type != 'document':
        await message.answer("❌ Отправьте документ или файл")
        return
    
    document = message.document
    
    # Check document size (20 MB limit)
    if document.file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой. Максимум 20 МБ.")
        return
    
    # Save document preserving media
    success = await LeadMagnet.set_document(document.file_id)
    
    if success:
        await message.answer("✅ Файл успешно загружен!")
    else:
        await message.answer("❌ Ошибка сохранения файла")
    
    await state.clear()
    
    # Возврат в меню
    await _return_to_main_menu(message)


# =============================================================================
# ОБРАБОТЧИКИ РЕДАКТИРОВАНИЯ ТЕКСТОВ
# =============================================================================

@router.callback_query(F.data == 'lead_edit_text')
async def lead_edit_text_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing greeting text"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    # Текущий текст (без языков)
    current_text = await LeadMagnet.get_text_for_locale('greeting_text', 'ru')
    
    await state.set_state(FSMLeadMagnet.editing_text)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        f"""✏️ <b>Редактирование приветственного текста</b>

Текущий текст:
<i>{current_text}</i>

Отправьте новый текст для приветствия:""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


@router.message(FSMLeadMagnet.editing_text)
async def process_greeting_text(message: types.Message, state: FSMContext):
    """Process new greeting text"""
    if not message.text:
        await message.answer("❌ Отправьте текстовое сообщение")
        return
    
    # Сохраняем текст (без языков)
    success = await LeadMagnet.set_greeting_text('ru', message.text)
    
    if success:
        await message.answer("✅ Приветственный текст обновлён")
    else:
        await message.answer("❌ Ошибка сохранения текста")
    
    await state.clear()
    
    # Возврат в меню
    await _return_to_main_menu(message)


@router.callback_query(F.data == 'lead_edit_label')
async def lead_edit_label_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing lessons label"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    # Текущее название (без языков)
    current_label = await LeadMagnet.get_text_for_locale('lessons_label', 'ru')
    
    await state.set_state(FSMLeadMagnet.editing_label)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        f"""🏷️ <b>Редактирование названия в «Моих уроках»</b>

Текущее название:
<i>{current_label}</i>

Отправьте новое название для отображения в разделе «Мои уроки»:""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


@router.message(FSMLeadMagnet.editing_label)
async def process_label(message: types.Message, state: FSMContext):
    """Process new label"""
    if not message.text:
        await message.answer("❌ Отправьте текстовое сообщение")
        return
    
    # Сохраняем новое название (без языков)
    success = await LeadMagnet.set_lessons_label('ru', message.text)
    
    if success:
        await message.answer("✅ Название обновлено")
    else:
        await message.answer("❌ Ошибка сохранения названия")
    
    await state.clear()
    
    # Возврат в меню
    await _return_to_main_menu(message)


# =============================================================================
# ПРЕДПРОСМОТР КОНТЕНТА
# =============================================================================

@router.callback_query(F.data == 'lead_preview')
async def lead_preview(call: types.CallbackQuery, state: FSMContext):
    """Preview lead magnet"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    lead_magnet = await LeadMagnet.get_lead_magnet()
    media_type, media_id, doc_id = await LeadMagnet.get_content_bundle()
    
    if not lead_magnet or not (media_id or doc_id):
        await call.answer("❌ Контент не загружен", show_alert=True)
        return
    
    # Текст приветствия
    greeting_text = await LeadMagnet.get_text_for_locale('greeting_text', 'ru')
    
    # Отправляем предпросмотр: медиа (если есть) + документ (если есть)
    try:
        if media_type == 'video' and media_id:
            await bot.send_video(
                chat_id=call.from_user.id,
                video=media_id,
                caption=f"🎬 <b>Предпросмотр лид-магнита</b>\n\n{greeting_text}",
                parse_mode='HTML'
            )
        elif media_type == 'photo' and media_id:
            await bot.send_photo(
                chat_id=call.from_user.id,
                photo=media_id,
                caption=f"🖼️ <b>Предпросмотр лид-магнита</b>\n\n{greeting_text}",
                parse_mode='HTML'
            )
        if doc_id:
            await bot.send_document(
                chat_id=call.from_user.id,
                document=doc_id,
                caption=f"📁 <b>Материалы лид-магнита</b>",
                parse_mode='HTML'
            )
        
        await call.answer("✅ Предпросмотр отправлен")
        
    except Exception as e:
        logging.error(f"Error sending preview: {e}")
        await call.answer("❌ Ошибка отправки предпросмотра", show_alert=True)


# =============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =============================================================================

async def _return_to_main_menu(message: types.Message):
    """Helper function to return to main lead magnet menu"""
    lead_magnet = await LeadMagnet.get_lead_magnet()
    content_type, file_id = await LeadMagnet.get_current_content()
    has_content = file_id is not None
    
    # Текст статуса контента
    if has_content:
        if content_type == 'video':
            content_status = '🎬 Видео загружено'
        elif content_type == 'photo':
            content_status = '🖼️ Фото загружено'
        elif content_type == 'document':
            content_status = '📁 Файл загружен'
        else:
            content_status = '✅ Контент загружен'
    else:
        content_status = '❌ Контент не загружен'
    
    text = f"""
🎬 <b>Управление лид-магнитом</b>

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
{content_status}
"""
    
    await message.answer(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled,
            content_type,
            has_content
        ),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'cancel_lead_edit')
async def cancel_lead_edit(call: types.CallbackQuery, state: FSMContext):
    """Cancel current edit operation"""
    await state.clear()
    await call.answer("❌ Отменено")
    
    # Return to menu
    await lead_magnet_menu(call, state)