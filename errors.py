"""
Система обработки ошибок для Telegram бота NikolayAI
Реализует классификацию ошибок, их обработку и восстановление
"""

import json
import logging
import traceback
import asyncio
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable, Union
from dataclasses import dataclass

from aiogram import types
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup


class ErrorType(Enum):
    """Типы ошибок в системе"""
    TELEGRAM_API = "telegram_api"
    VALIDATION = "validation"
    DATABASE = "database"
    NETWORK = "network"
    BUSINESS_LOGIC = "business_logic"
    STATE_CORRUPTION = "state_corruption"
    FILE_OPERATION = "file_operation"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Уровни критичности ошибок"""
    CRITICAL = "critical"    # Критические ошибки, требующие немедленного вмешательства
    HIGH = "high"           # Высокий приоритет, влияет на функциональность
    MEDIUM = "medium"       # Средний приоритет, частичная потеря функций
    LOW = "low"             # Низкий приоритет, минимальное влияние


@dataclass
class ErrorContext:
    """Контекст ошибки для детального анализа"""
    user_id: Optional[int] = None
    handler: Optional[str] = None
    callback_data: Optional[str] = None
    current_state: Optional[str] = None
    message_id: Optional[int] = None
    chat_id: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None


class StateCorruptionError(Exception):
    """Исключение для повреждения состояния FSM"""
    pass


class ContentComparator:
    """Класс для сравнения содержимого сообщений"""
    
    @staticmethod
    def compare_text(text1: Optional[str], text2: Optional[str]) -> bool:
        """Сравнить текст сообщений"""
        if text1 is None and text2 is None:
            return True
        if text1 is None or text2 is None:
            return False
        return text1.strip() == text2.strip()
    
    @staticmethod
    def compare_markup(markup1: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]], 
                      markup2: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]]) -> bool:
        """Сравнить разметку клавиатур"""
        if markup1 is None and markup2 is None:
            return True
        if markup1 is None or markup2 is None:
            return False
        
        # Простое сравнение через JSON
        try:
            markup1_dict = markup1.model_dump() if hasattr(markup1, 'model_dump') else markup1.dict()
            markup2_dict = markup2.model_dump() if hasattr(markup2, 'model_dump') else markup2.dict()
            return markup1_dict == markup2_dict
        except Exception:
            return False
    
    @classmethod
    def is_content_identical(cls, current_text: Optional[str], new_text: Optional[str],
                           current_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]],
                           new_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]]) -> bool:
        """Проверить идентичность всего содержимого"""
        return (cls.compare_text(current_text, new_text) and 
                cls.compare_markup(current_markup, new_markup))


class MarkupValidator:
    """Валидатор разметки клавиатур"""
    
    @staticmethod
    def validate_inline_keyboard(markup: Any) -> bool:
        """Проверить корректность inline клавиатуры"""
        return isinstance(markup, InlineKeyboardMarkup)
    
    @staticmethod
    def validate_reply_keyboard(markup: Any) -> bool:
        """Проверить корректность reply клавиатуры"""
        return isinstance(markup, ReplyKeyboardMarkup)
    
    @staticmethod
    def convert_markup_type(markup: Any, target_type: str = "inline") -> Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]]:
        """Конвертировать тип разметки с fallback"""
        if markup is None:
            return None
            
        if target_type == "inline":
            if isinstance(markup, InlineKeyboardMarkup):
                return markup
            elif isinstance(markup, ReplyKeyboardMarkup):
                logging.warning("ReplyKeyboardMarkup используется в inline контексте, создается пустая InlineKeyboardMarkup")
                return InlineKeyboardMarkup(inline_keyboard=[[]])
        elif target_type == "reply":
            if isinstance(markup, ReplyKeyboardMarkup):
                return markup
            elif isinstance(markup, InlineKeyboardMarkup):
                logging.warning("InlineKeyboardMarkup используется в reply контексте, создается пустая ReplyKeyboardMarkup")
                return ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)
                
        return markup


class ErrorLogger:
    """Система логирования ошибок"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring_enabled = False  # Можно настроить для внешних систем мониторинга
    
    def log_error(self, error: Exception, context: ErrorContext, error_type: ErrorType, severity: ErrorSeverity):
        """Логировать ошибку со структурированными данными"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'error_severity': severity.value,
            'error_class': type(error).__name__,
            'error_message': str(error),
            'user_id': context.user_id,
            'handler': context.handler,
            'callback_data': context.callback_data,
            'current_state': context.current_state,
            'message_id': context.message_id,
            'chat_id': context.chat_id,
            'additional_data': context.additional_data,
            'stack_trace': traceback.format_exc()
        }
        
        # Выбираем уровень логирования по критичности
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(json.dumps(log_data, ensure_ascii=False, indent=2))
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(json.dumps(log_data, ensure_ascii=False, indent=2))
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(json.dumps(log_data, ensure_ascii=False, indent=2))
        else:
            self.logger.info(json.dumps(log_data, ensure_ascii=False, indent=2))
        
        # Отправляем в систему мониторинга если настроена
        if self.monitoring_enabled:
            self._send_to_monitoring(log_data)
    
    def _send_to_monitoring(self, log_data: Dict[str, Any]):
        """Отправить в систему мониторинга (заглушка)"""
        # Здесь может быть интеграция с внешними системами мониторинга
        pass


class RecoveryAction:
    """Действия восстановления после ошибок"""
    
    @staticmethod
    async def retry_operation(operation: Callable, max_retries: int = 3, delay: float = 1.0, *args, **kwargs):
        """Повторить операцию с экспоненциальной задержкой"""
        for attempt in range(max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (2 ** attempt))
                    continue
                else:
                    raise e
    
    @staticmethod
    async def clear_user_state(state: FSMContext):
        """Очистить состояние пользователя"""
        try:
            await state.clear()
        except Exception as e:
            logging.error(f"Ошибка при очистке состояния: {e}")
    
    @staticmethod
    async def redirect_to_main_menu(message_or_call: Union[types.Message, types.CallbackQuery], 
                                  main_menu_markup, error_text: str = "❌ Произошла ошибка. Возвращаемся в главное меню."):
        """Перенаправить пользователя в главное меню"""
        try:
            if isinstance(message_or_call, types.CallbackQuery):
                await message_or_call.message.edit_text(error_text, reply_markup=main_menu_markup)
            else:
                await message_or_call.answer(error_text, reply_markup=main_menu_markup)
        except Exception as e:
            logging.error(f"Ошибка при перенаправлении в главное меню: {e}")


class ErrorHandler:
    """Основной класс обработки ошибок"""
    
    def __init__(self):
        self.logger = ErrorLogger()
        self.content_comparator = ContentComparator()
        self.markup_validator = MarkupValidator()
        self.recovery_action = RecoveryAction()
    
    def classify_error(self, error: Exception) -> tuple[ErrorType, ErrorSeverity]:
        """Классифицировать ошибку по типу и критичности"""
        if isinstance(error, TelegramBadRequest):
            if "message is not modified" in str(error):
                return ErrorType.TELEGRAM_API, ErrorSeverity.LOW
            elif "message to edit not found" in str(error):
                return ErrorType.TELEGRAM_API, ErrorSeverity.MEDIUM
            elif "Bad Request" in str(error):
                return ErrorType.VALIDATION, ErrorSeverity.MEDIUM
            else:
                return ErrorType.TELEGRAM_API, ErrorSeverity.HIGH
        
        elif isinstance(error, TelegramNetworkError):
            return ErrorType.NETWORK, ErrorSeverity.HIGH
        
        elif isinstance(error, TelegramAPIError):
            return ErrorType.TELEGRAM_API, ErrorSeverity.HIGH
        
        elif isinstance(error, StateCorruptionError):
            return ErrorType.STATE_CORRUPTION, ErrorSeverity.HIGH
        
        elif isinstance(error, (ConnectionError, OSError)):
            return ErrorType.DATABASE, ErrorSeverity.CRITICAL
        
        elif isinstance(error, ValueError):
            return ErrorType.VALIDATION, ErrorSeverity.MEDIUM
        
        elif isinstance(error, FileNotFoundError):
            return ErrorType.FILE_OPERATION, ErrorSeverity.MEDIUM
        
        else:
            return ErrorType.UNKNOWN, ErrorSeverity.HIGH
    
    async def handle_error(self, error: Exception, context: ErrorContext, 
                          message_or_call: Optional[Union[types.Message, types.CallbackQuery]] = None,
                          state: Optional[FSMContext] = None,
                          main_menu_markup=None) -> bool:
        """
        Обработать ошибку с автоматическим восстановлением
        
        Returns:
            bool: True если ошибка была успешно обработана, False иначе
        """
        error_type, severity = self.classify_error(error)
        
        # Логируем ошибку
        self.logger.log_error(error, context, error_type, severity)
        
        try:
            # Специальная обработка для разных типов ошибок
            if error_type == ErrorType.TELEGRAM_API:
                return await self._handle_telegram_api_error(error, message_or_call, main_menu_markup)
            
            elif error_type == ErrorType.STATE_CORRUPTION and state:
                await self.recovery_action.clear_user_state(state)
                if message_or_call and main_menu_markup:
                    await self.recovery_action.redirect_to_main_menu(
                        message_or_call, main_menu_markup,
                        "❌ Состояние пользователя повреждено. Сброс состояния выполнен."
                    )
                return True
            
            elif error_type == ErrorType.DATABASE:
                # Для ошибок БД просто уведомляем пользователя
                if message_or_call and main_menu_markup:
                    await self.recovery_action.redirect_to_main_menu(
                        message_or_call, main_menu_markup,
                        "❌ Проблемы с базой данных. Попробуйте позже."
                    )
                return True
            
            else:
                # Общий fallback
                if message_or_call and main_menu_markup:
                    await self.recovery_action.redirect_to_main_menu(
                        message_or_call, main_menu_markup
                    )
                return True
                
        except Exception as recovery_error:
            # Если восстановление тоже не удалось
            self.logger.log_error(
                recovery_error, 
                ErrorContext(additional_data={"original_error": str(error)}),
                ErrorType.UNKNOWN,
                ErrorSeverity.CRITICAL
            )
            return False
    
    async def _handle_telegram_api_error(self, error: Exception, 
                                       message_or_call: Optional[Union[types.Message, types.CallbackQuery]],
                                       main_menu_markup) -> bool:
        """Специальная обработка ошибок Telegram API"""
        error_str = str(error)
        
        if "message is not modified" in error_str:
            # Сообщение не изменилось - это не критично
            return True
        
        elif "message to edit not found" in error_str:
            # Сообщение не найдено - отправляем новое
            if message_or_call:
                try:
                    if isinstance(message_or_call, types.CallbackQuery):
                        await message_or_call.message.answer(
                            "❌ Сообщение устарело. Возвращаемся в главное меню.",
                            reply_markup=main_menu_markup
                        )
                    else:
                        await message_or_call.answer(
                            "❌ Произошла ошибка. Возвращаемся в главное меню.",
                            reply_markup=main_menu_markup
                        )
                    return True
                except Exception:
                    return False
        
        elif "rate limit" in error_str.lower():
            # Лимит запросов - ждем и повторяем
            await asyncio.sleep(1.0)
            return False  # Сигнализируем что нужен retry
        
        return False


# Глобальный экземпляр обработчика ошибок
global_error_handler = ErrorHandler()


# Декораторы для упрощения использования
def handle_errors(main_menu_markup=None, redirect_on_error: bool = True):
    """
    Декоратор для автоматической обработки ошибок в хендлерах
    
    Args:
        main_menu_markup: Разметка главного меню для возврата при ошибке
        redirect_on_error: Перенаправлять ли в главное меню при ошибке
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Фильтруем неожиданные аргументы от aiogram миддлвар
            # Используем более общий подход для фильтрации всех middleware аргументов
            aiogram_middleware_args = {
                'dispatcher', 'bots', 'bot', 'fsm_storage', 'event_context', 
                'event_from_user', 'event_chat', 'event_update_type', 'raw_updates', 'handler'
            }
            # Также фильтруем аргументы с известными префиксами
            filtered_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in aiogram_middleware_args and not k.startswith(('event_', 'fsm_', 'raw_'))
            }
            
            try:
                return await func(*args, **filtered_kwargs)
            except Exception as e:
                # Извлекаем контекст из аргументов
                context = ErrorContext()
                message_or_call = None
                state = None
                
                for arg in args:
                    if isinstance(arg, (types.Message, types.CallbackQuery)):
                        message_or_call = arg
                        context.user_id = arg.from_user.id if arg.from_user else None
                        context.handler = func.__name__
                        
                        if isinstance(arg, types.CallbackQuery):
                            context.callback_data = arg.data
                            context.message_id = arg.message.message_id if arg.message else None
                            context.chat_id = arg.message.chat.id if arg.message else None
                        else:
                            context.message_id = arg.message_id
                            context.chat_id = arg.chat.id
                    
                    elif isinstance(arg, FSMContext):
                        state = arg
                        try:
                            state_data = await arg.get_state()
                            context.current_state = str(state_data) if state_data else None
                        except Exception:
                            context.current_state = "unknown"
                
                # Обрабатываем ошибку
                if redirect_on_error:
                    await global_error_handler.handle_error(
                        e, context, message_or_call, state, main_menu_markup
                    )
                else:
                    # Только логируем без redirect
                    error_type, severity = global_error_handler.classify_error(e)
                    global_error_handler.logger.log_error(e, context, error_type, severity)
                    raise
        
        return wrapper
    return decorator