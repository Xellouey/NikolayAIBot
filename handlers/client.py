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
l = lesson.Lesson()
p = lesson.Purchase()


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)




async def send_lead_lesson(message: types.Message, bot: Bot, lang: str = 'ru'):
    """Send lead magnet lesson content (fixed flow)"""
    try:
        lead_id = await l.ensure_lead_magnet()
        if not lead_id:
            print("❌ Не удалось получить лид-урок")
            return
        
        lesson_data = await l.get_lesson(lead_id)
        if not lesson_data:
            print("❌ Лид-урок не найден")
            return
        
        user_id = message.from_user.id
        
        # Create purchase for lead magnet if not exists
        if not await p.check_user_has_lesson(user_id, lead_id):
            await p.create_purchase(
                user_id=user_id,
                lesson_id=lead_id,
                price_paid_usd=0,
                price_paid_stars=0,
                payment_id="lead_magnet"
            )
            print("✅ Создан purchase для лид-урока")
        
        # Send video with caption from lesson
        caption = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description}\n\n{lesson_data.text_content or ''}"
        if lesson_data.video_file_id:
            await bot.send_video(
                chat_id=user_id,
                video=lesson_data.video_file_id,
                caption=caption,
                parse_mode='HTML'
            )
        
        # Send document if exists
        if lesson_data.document_file_id:
            doc_caption = lesson_data.text_content or get_text('after_video', lang)
            await bot.send_document(
                chat_id=user_id,
                document=lesson_data.document_file_id,
                caption=doc_caption,
                parse_mode='HTML'
            )
        
        # Send instruction message
        await bot.send_message(
            chat_id=user_id,
            text=get_text('after_video', lang),
            reply_markup=kb.markup_main_menu()
        )
        
        print(f"✅ Лид-урок отправлен пользователю {user_id}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки лид-урока: {e}")
        logging.error(f"Ошибка отправки лид-урока: {e}")


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
    # Fixed simple flow: /start -> welcome -> lead video -> main menu
    if message.from_user is None:
        print("❌ No from_user in start")
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

    # Send welcome message
    welcome_text = get_text('welcome', lang)
    await message.answer(
        welcome_text,
        reply_markup=kb.markup_remove()
    )

    # Send intro video (lead lesson) - this will also show the main menu
    await send_lead_lesson(message, bot, lang)

    # Mark onboarding as completed
    await u.mark_onboarding_complete(user_id)
