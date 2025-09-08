import asyncio
import utils
import logging
import keyboards as kb
from aiogram import types, Router, F, Bot
from database import user
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

# Import error handling systems
from error_handling import TelegramErrorHandler, validate_telegram_file_id, health_monitor


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
    # filename='file.log'
)

u = user.User()
router = Router()


def validate_file_id(file_id, content_type):
    """Validate Telegram file_id before sending"""
    if not file_id or file_id in ['None', '', 'null', 'undefined']:
        return False
    
    file_id_str = str(file_id)
    if len(file_id_str) < 10:  # Telegram file_id usually longer
        return False
        
    return validate_telegram_file_id(file_id)


async def send_msg(data, message, keyboard=None, bot: Bot = None):
    """Отправка сообщения с валидацией file_id и обработкой ошибок"""
    content_type = data['content_type']
    text = data['text']
    caption = data['caption']
    file_id = data['file_id']
    
    chat_id = message if type(message) == int else message.chat.id
    
    # Получаем bot instance если не передан
    if bot is None:
        try:
            bot = Bot.get_current()
        except Exception:
            print(f"❌ Не удалось получить bot instance")
            return None
    
    message_sent = None  # Initialize to avoid unbound error
    
    try:
        if content_type == 'text':
            message_sent = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            print(f"✅ Текстовое сообщение отправлено в чат {chat_id}")
            return message_sent
        
        elif content_type in ['document', 'video', 'photo', 'audio', 'voice', 'video_note']:
            # Validate file_id
            if not validate_file_id(file_id, content_type):
                print(f"❌ Недействительный file_id для {content_type}: {file_id}")
                fallback_text = caption or text or f"📁 {content_type.title()} временно недоступно"
                message_sent = await bot.send_message(
                    chat_id=chat_id,
                    text=fallback_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return message_sent
            
            try:
                if content_type == 'photo':
                    message_sent = await bot.send_photo(
                        chat_id=chat_id,
                        photo=file_id,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif content_type == 'video':
                    message_sent = await bot.send_video(
                        chat_id=chat_id,
                        video=file_id,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif content_type == 'document':
                    message_sent = await bot.send_document(
                        chat_id=chat_id,
                        document=file_id,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif content_type == 'audio':
                    message_sent = await bot.send_audio(
                        chat_id=chat_id,
                        audio=file_id,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif content_type == 'voice':
                    message_sent = await bot.send_voice(
                        chat_id=chat_id,
                        voice=file_id,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                elif content_type == 'video_note':
                    message_sent = await bot.send_video_note(
                        chat_id=chat_id,
                        video_note=file_id,
                        reply_markup=keyboard
                    )
                
                print(f"✅ {content_type.title()} отправлено в чат {chat_id}")
                return message_sent
                
            except Exception as media_error:
                error_info = await TelegramErrorHandler.handle_telegram_error(media_error, f"send_{content_type}")
                
                if error_info['error_type'] == 'file_error':
                    print(f"📁 Ошибка file_id для {content_type}: {file_id}")
                    fallback_text = caption or text or error_info['message']
                    message_sent = await bot.send_message(
                        chat_id=chat_id,
                        text=fallback_text,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    return message_sent
                else:
                    raise media_error
        
        else:
            fallback_text = text or caption or "⚠️ Неизвестный тип сообщения"
            message_sent = await bot.send_message(
                chat_id=chat_id,
                text=fallback_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return message_sent
            
    except Exception as e:
        await health_monitor.handle_error(e, f"send_msg_{content_type}")
        
        fallback_text = caption or text or "❌ Ошибка отправки сообщения. Обратитесь в поддержку."
        try:
            message_sent = await bot.send_message(
                chat_id=chat_id,
                text=fallback_text,
                reply_markup=keyboard
            )
            return message_sent
        except Exception as critical_error:
            print(f"💥 Критическая ошибка в send_msg: {critical_error}")
            logging.error(f"Критическая ошибка в send_msg: {critical_error}")
            return None

async def start_steps(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user is None:
        print("❌ No from_user in start_steps")
        return
    
    steps = utils.get_steps()
    steps_list = list(steps.values())
    
    try:
        step_bot = steps_list[2:]  # Skip 'join' and 'start' steps
    except:
        step_bot = []
        
    removed = False    
    
    i = 1
    for step in step_bot:
        keyboard = step['keyboard']
        delay = step['delay']
        markup = kb.markup_custom(keyboard)
        
        if markup == None and removed == False:
            markup = kb.markup_remove()
            removed = True
        
        await send_msg(step, message, markup, bot=bot)
        
        if i != len(step_bot):
            await asyncio.sleep(delay)
            
        i += 1
    
    # Mark onboarding as completed after all steps are sent
    await u.mark_onboarding_complete(message.from_user.id)
    
    # Send main menu after onboarding completion
    await asyncio.sleep(2)  # Small delay before showing menu
    welcome_text = utils.get_text('messages.welcome')
    if not isinstance(welcome_text, str):
        welcome_text = str(welcome_text)
    await message.answer(
        welcome_text,
        reply_markup=kb.markup_main_menu()
    )


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

@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext, bot: Bot):    
    if message.from_user is None:
        print("❌ No from_user in start")
        return
        
    if await state.get_state() != None:
        await state.clear()

    user_data = await u.get_user(message.from_user.id)
    
    # Create user if doesn't exist
    if user_data == None:
        await u.create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        user_data = await u.get_user(message.from_user.id)  # Get fresh user data
        
    # Check if user has completed onboarding
    onboarding_completed = await u.check_onboarding_status(message.from_user.id)
    
    if onboarding_completed:
        # User has completed onboarding - show main menu
        welcome_text = utils.get_text('messages.welcome')
        if not isinstance(welcome_text, str):
            welcome_text = str(welcome_text)
        await message.answer(
            welcome_text,
            reply_markup=kb.markup_main_menu()
        )
        return
        
    # User needs onboarding - start the flow
    steps = utils.get_steps()
    start = steps['start']
            
    markup = kb.markup_remove()
        
    await send_msg(start, message, markup, bot=bot)
    
    # Always continue with steps immediately
    await asyncio.sleep(1)
    await start_steps(message, state, bot=bot)
