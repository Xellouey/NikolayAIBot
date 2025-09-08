"""
MessageManager - система безопасного управления сообщениями
Предотвращает ошибки "message is not modified" и обеспечивает fallback механизмы
"""

import logging
from typing import Optional, Union, Any
from aiogram import types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from errors import ContentComparator, MarkupValidator, global_error_handler, ErrorContext, ErrorType


class MessageManager:
    """Менеджер безопасных операций с сообщениями"""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.content_comparator = ContentComparator()
        self.markup_validator = MarkupValidator()
        self.logger = logging.getLogger(__name__)
    
    async def edit_message_safe(self, 
                              message: types.Message, 
                              new_text: str, 
                              new_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
                              parse_mode: str = 'HTML') -> bool:
        """
        Безопасно редактировать сообщение с проверкой содержимого
        
        Args:
            message: Сообщение для редактирования
            new_text: Новый текст
            new_markup: Новая разметка клавиатуры
            parse_mode: Режим парсинга
            
        Returns:
            bool: True если операция успешна, False иначе
        """
        try:
            # Валидируем разметку
            if new_markup is not None:
                new_markup = self.markup_validator.convert_markup_type(new_markup, "inline")
            
            # Сравниваем содержимое
            if self.content_comparator.is_content_identical(
                message.text, new_text, message.reply_markup, new_markup
            ):
                self.logger.debug(f"Содержимое сообщения {message.message_id} идентично, пропускаем редактирование")
                return True
            
            # Пытаемся отредактировать
            await message.edit_text(
                text=new_text,
                reply_markup=new_markup,
                parse_mode=parse_mode
            )
            
            self.logger.debug(f"Сообщение {message.message_id} успешно отредактировано")
            return True
            
        except TelegramBadRequest as e:
            return await self._handle_edit_error(e, message, new_text, new_markup, parse_mode)
        
        except Exception as e:
            # Неожиданная ошибка
            context = ErrorContext(
                user_id=message.from_user.id if message.from_user else None,
                handler="edit_message_safe",
                message_id=message.message_id,
                chat_id=message.chat.id,
                additional_data={"new_text_length": len(new_text)}
            )
            
            error_type, severity = global_error_handler.classify_error(e)
            global_error_handler.logger.log_error(e, context, error_type, severity)
            return False
    
    async def _handle_edit_error(self, 
                               error: TelegramBadRequest, 
                               message: types.Message,
                               new_text: str,
                               new_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]],
                               parse_mode: str) -> bool:
        """Обработать ошибки редактирования"""
        error_str = str(error)
        
        if "message is not modified" in error_str:
            # Содержимое идентично, но наша проверка это пропустила
            self.logger.debug(f"Telegram API: сообщение {message.message_id} не изменилось")
            return True
        
        elif "message to edit not found" in error_str:
            # Сообщение было удалено, отправляем новое
            self.logger.warning(f"Сообщение {message.message_id} не найдено, отправляем новое")
            try:
                await self.send_message_safe(
                    chat_id=message.chat.id,
                    text=new_text,
                    reply_markup=new_markup,
                    parse_mode=parse_mode
                )
                return True
            except Exception as send_error:
                self.logger.error(f"Ошибка при отправке нового сообщения: {send_error}")
                return False
        
        elif "can't parse entities" in error_str or "bad format" in error_str.lower():
            # Ошибка парсинга HTML/Markdown, пробуем без разметки
            self.logger.warning(f"Ошибка парсинга в сообщении {message.message_id}, отправляем без форматирования")
            try:
                await message.edit_text(
                    text=new_text,
                    reply_markup=new_markup,
                    parse_mode=None
                )
                return True
            except Exception:
                return False
        
        else:
            # Другая ошибка Telegram API
            self.logger.error(f"Неизвестная ошибка редактирования сообщения {message.message_id}: {error}")
            return False
    
    async def send_message_safe(self,
                              chat_id: int,
                              text: str,
                              reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
                              parse_mode: str = 'HTML',
                              disable_web_page_preview: bool = True) -> Optional[types.Message]:
        """
        Безопасно отправить сообщение
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
            reply_markup: Разметка клавиатуры
            parse_mode: Режим парсинга
            disable_web_page_preview: Отключить предпросмотр ссылок
            
        Returns:
            types.Message или None если отправка не удалась
        """
        try:
            if not self.bot:
                self.logger.error("Bot instance не настроен для MessageManager")
                return None
            
            # Валидируем разметку
            if reply_markup is not None:
                if isinstance(reply_markup, InlineKeyboardMarkup):
                    reply_markup = self.markup_validator.convert_markup_type(reply_markup, "inline")
                else:
                    reply_markup = self.markup_validator.convert_markup_type(reply_markup, "reply")
            
            # Отправляем сообщение
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            
            self.logger.debug(f"Сообщение успешно отправлено в чат {chat_id}")
            return message
            
        except TelegramBadRequest as e:
            return await self._handle_send_error(e, chat_id, text, reply_markup, parse_mode, disable_web_page_preview)
        
        except Exception as e:
            context = ErrorContext(
                chat_id=chat_id,
                handler="send_message_safe",
                additional_data={"text_length": len(text)}
            )
            
            error_type, severity = global_error_handler.classify_error(e)
            global_error_handler.logger.log_error(e, context, error_type, severity)
            return None
    
    async def _handle_send_error(self,
                               error: TelegramBadRequest,
                               chat_id: int,
                               text: str,
                               reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]],
                               parse_mode: str,
                               disable_web_page_preview: bool) -> Optional[types.Message]:
        """Обработать ошибки отправки сообщения"""
        error_str = str(error)
        
        if "can't parse entities" in error_str or "bad format" in error_str.lower():
            # Ошибка парсинга, пробуем без форматирования
            self.logger.warning(f"Ошибка парсинга при отправке в чат {chat_id}, отправляем без форматирования")
            try:
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=None,
                    disable_web_page_preview=disable_web_page_preview
                )
            except Exception:
                return None
        
        elif "message is too long" in error_str:
            # Сообщение слишком длинное, обрезаем
            self.logger.warning(f"Сообщение слишком длинное для чата {chat_id}, обрезаем")
            truncated_text = text[:4000] + "..." if len(text) > 4000 else text
            try:
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=truncated_text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview
                )
            except Exception:
                return None
        
        elif "chat not found" in error_str:
            self.logger.error(f"Чат {chat_id} не найден")
            return None
        
        else:
            self.logger.error(f"Неизвестная ошибка отправки сообщения в чат {chat_id}: {error}")
            return None
    
    async def send_media_safe(self,
                            chat_id: int,
                            media_type: str,
                            file_id: str,
                            caption: Optional[str] = None,
                            reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
                            parse_mode: str = 'HTML') -> Optional[types.Message]:
        """
        Безопасно отправить медиа с fallback на текст
        
        Args:
            chat_id: ID чата
            media_type: Тип медиа (photo, video, document, etc.)
            file_id: Telegram file_id
            caption: Подпись к медиа
            reply_markup: Разметка клавиатуры
            parse_mode: Режим парсинга
            
        Returns:
            types.Message или None если отправка не удалась
        """
        if not self.bot:
            self.logger.error("Bot instance не настроен для MessageManager")
            return None
        
        try:
            # Валидируем разметку
            if reply_markup is not None:
                reply_markup = self.markup_validator.convert_markup_type(reply_markup, "inline")
            
            # Выбираем метод отправки в зависимости от типа медиа
            if media_type.lower() == 'photo':
                return await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            elif media_type.lower() == 'video':
                return await self.bot.send_video(
                    chat_id=chat_id,
                    video=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            elif media_type.lower() == 'document':
                return await self.bot.send_document(
                    chat_id=chat_id,
                    document=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            elif media_type.lower() == 'audio':
                return await self.bot.send_audio(
                    chat_id=chat_id,
                    audio=file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                self.logger.error(f"Неподдерживаемый тип медиа: {media_type}")
                return None
                
        except TelegramBadRequest as e:
            # Медиа не удалось отправить, fallback на текст
            self.logger.warning(f"Ошибка отправки медиа {media_type} в чат {chat_id}: {e}")
            
            fallback_text = caption or f"❌ Не удалось загрузить {media_type}. Обратитесь в поддержку."
            
            return await self.send_message_safe(
                chat_id=chat_id,
                text=fallback_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
        except Exception as e:
            context = ErrorContext(
                chat_id=chat_id,
                handler="send_media_safe",
                additional_data={
                    "media_type": media_type,
                    "file_id": file_id[:50] + "..." if len(file_id) > 50 else file_id
                }
            )
            
            error_type, severity = global_error_handler.classify_error(e)
            global_error_handler.logger.log_error(e, context, error_type, severity)
            
            # Fallback на текст
            fallback_text = caption or f"❌ Не удалось загрузить {media_type}. Обратитесь в поддержку."
            return await self.send_message_safe(
                chat_id=chat_id,
                text=fallback_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    
    async def delete_message_safe(self, chat_id: int, message_id: int) -> bool:
        """
        Безопасно удалить сообщение
        
        Args:
            chat_id: ID чата
            message_id: ID сообщения
            
        Returns:
            bool: True если удалено успешно или сообщения уже нет
        """
        if not self.bot:
            self.logger.error("Bot instance не настроен для MessageManager")
            return False
        
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            self.logger.debug(f"Сообщение {message_id} удалено из чата {chat_id}")
            return True
            
        except TelegramBadRequest as e:
            error_str = str(e)
            if "message to delete not found" in error_str:
                # Сообщение уже удалено
                self.logger.debug(f"Сообщение {message_id} уже удалено из чата {chat_id}")
                return True
            elif "message can't be deleted" in error_str:
                self.logger.warning(f"Сообщение {message_id} нельзя удалить из чата {chat_id}")
                return False
            else:
                self.logger.error(f"Ошибка удаления сообщения {message_id} из чата {chat_id}: {e}")
                return False
        
        except Exception as e:
            context = ErrorContext(
                chat_id=chat_id,
                message_id=message_id,
                handler="delete_message_safe"
            )
            
            error_type, severity = global_error_handler.classify_error(e)
            global_error_handler.logger.log_error(e, context, error_type, severity)
            return False
    
    def set_bot(self, bot: Bot):
        """Установить Bot instance"""
        self.bot = bot


# Глобальный экземпляр менеджера сообщений  
global_message_manager = MessageManager()