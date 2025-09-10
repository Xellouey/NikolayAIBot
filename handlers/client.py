import asyncio
import asyncio
import utils
import logging
import keyboards as kb
from aiogram import types, Router, F, Bot
from database import user
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from message_utils import send_msg, validate_file_id
from database import user as user_module
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




async def send_lead_lesson(message: types.Message, bot: Bot):
    """Send lead magnet lesson content"""
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
        
        # Check if user already has this lesson
        if await p.check_user_has_lesson(user_id, lead_id):
            print("✅ Пользователь уже имеет лид-урок")
            return
        
        # Create purchase for lead magnet
        await p.create_purchase(
            user_id=user_id,
            lesson_id=lead_id,
            price_paid_usd=0,
            price_paid_stars=0,
            payment_id="lead_magnet"
        )
        print("✅ Создан purchase для лид-урока")
        
        # Send video with caption
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
            doc_caption = lesson_data.text_content or "📝 Конспект урока"
            await bot.send_document(
                chat_id=user_id,
                document=lesson_data.document_file_id,
                caption=doc_caption,
                parse_mode='HTML'
            )
        
        # Send instruction message
        await bot.send_message(
            chat_id=user_id,
            text="👆 Ваш лид-урок выше. Теперь вы можете перейти в каталог уроков!",
            reply_markup=kb.markup_main_menu()
        )
        
        print(f"✅ Лид-урок отправлен пользователю {user_id}")
        
    except Exception as e:
        print(f"❌ Ошибка отправки лид-урока: {e}")
        logging.error(f"Ошибка отправки лид-урока: {e}")


async def join_request(message: types.ChatJoinRequest, state: FSMContext):
    steps = utils.get_steps()
    join = steps['join']
    
    await message.approve() 
    user_id = message.from_user.id if message.from_user else None
    if user_id:
        await send_msg(join, user_id, kb.markup_phone())
    
    user_data = await u.get_user(user_id) if user_id else None
    
    if user_data == None and user_id:
        await u.create_user(user_id, message.from_user.username if message.from_user else None, message.from_user.full_name if message.from_user else None)


router = Router()


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext, bot: Bot):    
    if message.from_user is None:
        print("❌ No from_user in start")
        return
        
    if await state.get_state() != None:
        await state.clear()

    user_id = message.from_user.id
    lang = message.from_user.language_code or 'ru'
    await u.update_user_lang(user_id, lang)
    
    # Create user if doesn't exist
    user_data = await u.get_user(user_id)
    if user_data == None:
        await u.create_user(user_id, message.from_user.username, message.from_user.full_name)
        user_data = await u.get_user(user_id)  # Get fresh user data
        
    # Check if user has completed onboarding
    onboarding_completed = await u.check_onboarding_status(user_id)
    
    welcome_text = await utils.get_text('messages.welcome', lang=lang)
    
    if onboarding_completed:
        # User has completed onboarding - show main menu
        await message.answer(
            welcome_text,
            reply_markup=kb.markup_main_menu()
        )
        return
        
    # Onboarding - send welcome
    await message.answer(
        welcome_text,
        reply_markup=kb.markup_remove()
    )
    
    # Send intro video (lead lesson)
    await send_lead_lesson(message, bot)
    
    # Mark onboarding as completed
    await u.mark_onboarding_complete(user_id)
    
    # Show catalog (import here to avoid circular import)
    from .shop import show_catalog
    await show_catalog(types.CallbackQuery.from_message(message, data='catalog'), state)  # Simulate callback for show_catalog
    
    # Send main menu after
    await asyncio.sleep(2)
    await message.answer(
        welcome_text + "\n\nТеперь вы можете перейти в каталог уроков!",
        reply_markup=kb.markup_main_menu()
    )
