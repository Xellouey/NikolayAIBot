import asyncio
import logging
import keyboards as kb
from aiogram import types, Router, F, Bot
from database import user
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from database import user as user_module
from localization import get_text  # New localization system

u = user_module.User()

# Import error handling systems
from error_handling import TelegramErrorHandler, validate_telegram_file_id, health_monitor

# Import lesson and purchase
from database import lesson
from database.lead_magnet import LeadMagnet
l = lesson.Lesson()
p = lesson.Purchase()


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)




async def send_lead_magnet(message: types.Message, bot: Bot, lang: str = 'ru'):
    """Send lead magnet content if enabled (supports video, photo, document)"""
    try:
        # Check if lead magnet is ready
        if not await LeadMagnet.is_ready():
            print("ℹ️ Lead magnet not ready (disabled or no content)")
            return False
        
        # Get lead magnet configuration
        lead_magnet = await LeadMagnet.get_lead_magnet()
        if not lead_magnet:
            return False
        
        user_id = message.from_user.id if message.from_user else 0
        
        # Get greeting text for user's locale
        greeting_text = await LeadMagnet.get_text_for_locale('greeting_text', lang)
        
        # Get content bundle
        media_type, media_id, doc_id = await LeadMagnet.get_content_bundle()
        if not (media_id or doc_id):
            return False
        
        from handlers.shop import add_user_preview_message
        lead_message = None
        # Send media first if present
        if media_type == 'video' and media_id:
            lead_message = await bot.send_video(
                chat_id=user_id,
                video=media_id,
                caption=f"🎬 {greeting_text}",
                parse_mode='HTML'
            )
        elif media_type == 'photo' and media_id:
            lead_message = await bot.send_photo(
                chat_id=user_id,
                photo=media_id,
                caption=f"🖼️ {greeting_text}",
                parse_mode='HTML'
            )
        # Track media message
        if lead_message:
            await add_user_preview_message(user_id, lead_message.message_id)
        
        # Send document second if present
        if doc_id:
            doc_msg = await bot.send_document(
                chat_id=user_id,
                document=doc_id,
                caption=f"📁 Материалы урока",
                parse_mode='HTML'
            )
            if doc_msg:
                await add_user_preview_message(user_id, doc_msg.message_id)

        return True
        
    except Exception as e:
        logging.error(f"Error sending lead magnet: {e}")
        return False


async def join_request(message: types.ChatJoinRequest, state: FSMContext):
    # Fixed, simple join handling without steps
    await message.approve()
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        user_data = await u.get_user(user_id)
        if user_data is None:
            await u.create_user(user_id, message.from_user.username if message.from_user else None, message.from_user.full_name if message.from_user else None)
        # No automatic messaging on join in simplified flow


router = Router()


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext, bot: Bot):
    # Fixed simple flow: /start -> welcome -> lead video (if enabled) -> main menu
    if message.from_user is None:
        return

    # Reset state if any
    if await state.get_state() is not None:
        await state.clear()

    user_id = message.from_user.id
    lang = (message.from_user.language_code or 'ru')[:2]
    await u.update_user_lang(user_id, lang)

    # Ensure user exists
    user_data = await u.get_user(user_id)
    if user_data is None:
        await u.create_user(user_id, message.from_user.username, message.from_user.full_name)

    # 1. Send lead magnet video if enabled
    lead_sent = await send_lead_magnet(message, bot, lang)

    # 2. Send main menu with welcome message from localization
    await message.answer(
        get_text('welcome', lang),
        reply_markup=kb.markup_main_menu(lang)
    )

    # Mark onboarding as completed
    await u.mark_onboarding_complete(user_id)
