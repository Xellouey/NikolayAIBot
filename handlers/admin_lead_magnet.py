"""Admin handlers for lead magnet management"""
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


def markup_lead_magnet_menu(is_enabled: bool, has_video: bool):
    """Lead magnet management menu keyboard - ALWAYS IN RUSSIAN"""
    toggle_text = "🔴 Выключить" if is_enabled else "🟢 Включить"
    
    items = [
        [InlineKeyboardButton(text=toggle_text, callback_data='lead_toggle')],
        [InlineKeyboardButton(text='✏️ Изменить приветственный текст', callback_data='lead_edit_text')],
        [InlineKeyboardButton(text='🎬 Изменить видео', callback_data='lead_edit_video')],
        [InlineKeyboardButton(text='🏷️ Изменить название в «Моих уроках»', callback_data='lead_edit_label')],
    ]
    
    if has_video:
        items.append([InlineKeyboardButton(text='👁️ Предпросмотр', callback_data='lead_preview')])
    
    items.append([InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')])
    
    return InlineKeyboardMarkup(inline_keyboard=items)


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
    
    text = f"""
🎬 <b>Управление лид-магнитом</b>

Лид-магнит — это вводное видео, которое показывается новым пользователям при первом входе в бота.

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
🎬 Видео: {'✅ Загружено' if lead_magnet.video_file_id else '❌ Не загружено'}

Выберите действие:
"""
    
    await call.message.edit_text(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled, 
            bool(lead_magnet.video_file_id)
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
    
    # Check if video exists before enabling
    if not lead_magnet.enabled and not lead_magnet.video_file_id:
        await call.answer("❌ Сначала загрузите видео!", show_alert=True)
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
    lead_magnet = await LeadMagnet.get_lead_magnet()
    text = f"""
🎬 <b>Управление лид-магнитом</b>

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
🎬 Видео: {'✅ Загружено' if lead_magnet.video_file_id else '❌ Не загружено'}
"""
    
    await message.answer(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled,
            bool(lead_magnet.video_file_id)
        ),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'lead_edit_video')
async def lead_edit_video_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing video"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    await state.set_state(FSMLeadMagnet.editing_video)
    
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lead_edit")]
    ])
    
    await call.message.edit_text(
        """🎬 <b>Загрузка видео для лид-магнита</b>

Отправьте видео, которое будет показываться новым пользователям.

⚠️ Требования:
• Формат: MP4
• Максимальный размер: 50 МБ
• Рекомендуемая длительность: до 2 минут""",
        reply_markup=cancel_keyboard,
        parse_mode='HTML'
    )


@router.message(FSMLeadMagnet.editing_video)
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
    
    # Save video file_id
    success = await LeadMagnet.set_video(video.file_id)
    
    if success:
        await message.answer("✅ Видео успешно загружено!")
    else:
        await message.answer("❌ Ошибка сохранения видео")
    
    await state.clear()
    
    # Возврат в меню
    lead_magnet = await LeadMagnet.get_lead_magnet()
    text = f"""
🎬 <b>Управление лид-магнитом</b>

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
🎬 Видео: ✅ Загружено
"""
    
    await message.answer(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled,
            True
        ),
        parse_mode='HTML'
    )


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
    lead_magnet = await LeadMagnet.get_lead_magnet()
    text = f"""
🎬 <b>Управление лид-магнитом</b>

📊 Текущий статус: {'✅ Включен' if lead_magnet.enabled else '❌ Выключен'}
🎬 Видео: {'✅ Загружено' if lead_magnet.video_file_id else '❌ Не загружено'}
"""
    
    await message.answer(
        text,
        reply_markup=markup_lead_magnet_menu(
            lead_magnet.enabled,
            bool(lead_magnet.video_file_id)
        ),
        parse_mode='HTML'
    )




@router.callback_query(F.data == 'lead_preview')
async def lead_preview(call: types.CallbackQuery, state: FSMContext):
    """Preview lead magnet"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    lead_magnet = await LeadMagnet.get_lead_magnet()
    if not lead_magnet or not lead_magnet.video_file_id:
        await call.answer("❌ Видео не загружено", show_alert=True)
        return
    
    # Текст приветствия
    greeting_text = await LeadMagnet.get_text_for_locale('greeting_text', 'ru')
    
    # Отправляем предпросмотр
    await bot.send_video(
        chat_id=call.from_user.id,
        video=lead_magnet.video_file_id,
        caption=f"🎬 <b>Предпросмотр лид-магнита</b>\n\n{greeting_text}",
        parse_mode='HTML'
    )
    
    await call.answer("✅ Предпросмотр отправлен")


@router.callback_query(F.data == 'cancel_lead_edit')
async def cancel_lead_edit(call: types.CallbackQuery, state: FSMContext):
    """Cancel current edit operation"""
    await state.clear()
    await call.answer("❌ Отменено")
    
    # Return to menu
    await lead_magnet_menu(call, state)
