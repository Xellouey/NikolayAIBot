"""
Message utilities for the Telegram bot
Contains functions for sending messages with validation and error handling
"""

import logging
from aiogram import Bot, types
from error_handling import TelegramErrorHandler, validate_telegram_file_id, health_monitor


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