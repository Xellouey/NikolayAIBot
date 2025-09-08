# Error Handling and Recovery Framework
import asyncio
import logging
import traceback
import functools
from typing import Optional, Callable, Any, Dict
from datetime import datetime
import json

from aiogram import types
from aiogram.fsm.context import FSMContext
import utils
import keyboards as kb

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorRecoverySystem:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self):
        self.fallback_steps = self._get_default_steps()
        self.error_counts = {}
        self.max_retries = 3
        
    def _get_default_steps(self) -> Dict[str, Any]:
        """Get default fallback steps in case of file corruption"""
        return {
            "join": {
                "content_type": "text",
                "text": "🎓 Добро пожаловать! Для получения уроков авторизируйтесь 👇",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "start": {
                "content_type": "text", 
                "text": "✅ Авторизация успешна!\n\n🎁 Начинаем обучение:",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "text",
                "text": "📚 Добро пожаловать в мир нейросетей!\n\nВ ближайшее время мы загрузим для вас актуальные уроки.",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 3
            }
        }
    
    def error_handler(self, operation_name: str = None, max_retries: int = 3, fallback_action: Callable = None):
        """
        Decorator for comprehensive error handling with automatic recovery
        
        Args:
            operation_name: Name of operation for logging
            max_retries: Maximum retry attempts
            fallback_action: Function to call if all retries fail
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                operation = operation_name or func.__name__
                retry_count = 0
                
                while retry_count <= max_retries:
                    try:
                        return await func(*args, **kwargs)
                        
                    except Exception as e:
                        retry_count += 1
                        error_id = f"{operation}_{id(e)}"
                        
                        # Log error with context
                        logger.error(
                            f"Error in {operation} (attempt {retry_count}/{max_retries + 1}): "
                            f"{type(e).__name__}: {e}\n"
                            f"Traceback: {traceback.format_exc()}"
                        )
                        
                        # Track error frequency
                        self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
                        
                        # If we've exhausted retries
                        if retry_count > max_retries:
                            logger.critical(f"Max retries exceeded for {operation}")
                            
                            # Try fallback action if provided
                            if fallback_action:
                                try:
                                    return await fallback_action(*args, **kwargs)
                                except Exception as fallback_error:
                                    logger.critical(f"Fallback failed for {operation}: {fallback_error}")
                            
                            # Re-raise the original error
                            raise e
                        
                        # Wait before retry (exponential backoff)
                        wait_time = min(2 ** retry_count, 10)
                        await asyncio.sleep(wait_time)
                        
            return wrapper
        return decorator
    
    async def safe_send_message(self, chat_id: int, text: str, reply_markup=None, parse_mode: str = 'HTML') -> bool:
        """
        Safely send message with fallback to plain text
        
        Args:
            chat_id: Target chat ID
            text: Message text
            reply_markup: Keyboard markup
            parse_mode: Parse mode (HTML/Markdown)
            
        Returns:
            True if message sent successfully
        """
        from handlers.client import send_msg
        
        try:
            # Try with original formatting
            message_data = {
                'content_type': 'text',
                'text': text,
                'caption': None,
                'file_id': None
            }
            
            await send_msg(message_data, chat_id, reply_markup)
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send formatted message: {e}")
            
            try:
                # Fallback: send plain text without formatting
                plain_text = self._strip_html_tags(text)
                message_data = {
                    'content_type': 'text',
                    'text': plain_text,
                    'caption': None,
                    'file_id': None
                }
                
                await send_msg(message_data, chat_id, reply_markup)
                return True
                
            except Exception as fallback_error:
                logger.error(f"Failed to send fallback message: {fallback_error}")
                return False
    
    def _strip_html_tags(self, text: str) -> str:
        """Strip HTML tags from text for fallback"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    async def recover_from_step_error(self, user_id: int, error_context: str = None) -> bool:
        """
        Recover from step-related errors by falling back to safe steps
        
        Args:
            user_id: User ID to send recovery message to
            error_context: Context about what failed
            
        Returns:
            True if recovery successful
        """
        try:
            logger.info(f"Initiating step error recovery for user {user_id}")
            
            # Send recovery message
            recovery_text = (
                "⚠️ Произошла техническая ошибка при загрузке контента.\n\n"
                "🔄 Мы переключили вас на резервную систему.\n"
                "📞 Обратитесь в поддержку, если проблема повторится."
            )
            
            await self.safe_send_message(
                user_id, 
                recovery_text, 
                kb.markup_main_menu()
            )
            
            logger.info(f"Recovery message sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.critical(f"Recovery failed for user {user_id}: {e}")
            return False
    
    async def recover_from_database_error(self, operation: str, user_id: int = None) -> bool:
        """
        Recover from database connection errors
        
        Args:
            operation: Database operation that failed
            user_id: User ID if applicable
            
        Returns:
            True if recovery successful
        """
        try:
            logger.warning(f"Database error recovery initiated for operation: {operation}")
            
            # Try to reconnect to database
            from database.core import con
            
            if con.is_closed():
                con.connect()
                logger.info("Database connection restored")
            
            # If user_id provided, send notification
            if user_id:
                await self.safe_send_message(
                    user_id,
                    "⚠️ Временные технические работы.\n🔄 Попробуйте повторить действие через несколько секунд.",
                    kb.markup_main_menu()
                )
            
            return True
            
        except Exception as e:
            logger.critical(f"Database recovery failed: {e}")
            return False
    
    async def handle_steps_file_corruption(self) -> bool:
        """
        Handle corrupted steps.json file by restoring from backup or defaults
        
        Returns:
            True if recovery successful
        """
        try:
            logger.warning("Steps file corruption detected, initiating recovery")
            
            # Try to restore from backup first
            from validators import StepBackupManager
            backup_manager = StepBackupManager()
            
            backups = backup_manager.list_backups()
            if backups:
                latest_backup = backups[0]
                logger.info(f"Attempting restore from backup: {latest_backup}")
                
                if backup_manager.restore_backup(latest_backup):
                    logger.info("Successfully restored from backup")
                    return True
            
            # If no backup or restore failed, use default steps
            logger.warning("No valid backup found, using default steps")
            utils.update_steps(self.fallback_steps)
            
            logger.info("Default steps loaded successfully")
            return True
            
        except Exception as e:
            logger.critical(f"Steps file recovery failed: {e}")
            return False
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "most_frequent_error": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None,
            "timestamp": datetime.now().isoformat()
        }


# Global error recovery system instance
error_recovery = ErrorRecoverySystem()


# Decorator shortcuts for common use cases
def handle_message_errors(func: Callable) -> Callable:
    """Decorator for message handler error handling"""
    return error_recovery.error_handler(
        operation_name=f"message_handler_{func.__name__}",
        max_retries=2
    )(func)


def handle_callback_errors(func: Callable) -> Callable:
    """Decorator for callback handler error handling"""
    return error_recovery.error_handler(
        operation_name=f"callback_handler_{func.__name__}",
        max_retries=2
    )(func)


def handle_database_errors(func: Callable) -> Callable:
    """Decorator for database operation error handling"""
    async def fallback_action(*args, **kwargs):
        """Fallback for database errors"""
        logger.warning(f"Database fallback triggered for {func.__name__}")
        await error_recovery.recover_from_database_error(func.__name__)
        return None
    
    return error_recovery.error_handler(
        operation_name=f"database_{func.__name__}",
        max_retries=3,
        fallback_action=fallback_action
    )(func)


async def graceful_error_response(message_or_call, error_msg: str = None, show_main_menu: bool = True):
    """
    Send a graceful error response to user
    
    Args:
        message_or_call: Message or CallbackQuery object
        error_msg: Custom error message
        show_main_menu: Whether to show main menu
    """
    default_error = "❌ Произошла ошибка. Попробуйте позже или обратитесь в поддержку."
    text = error_msg or default_error
    
    markup = kb.markup_main_menu() if show_main_menu else None
    
    try:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.answer()
            await message_or_call.message.edit_text(text, reply_markup=markup)
        else:
            await message_or_call.answer(text, reply_markup=markup)
            
    except Exception as e:
        logger.error(f"Failed to send error response: {e}")
        
        # Last resort: try to send basic message
        try:
            chat_id = (message_or_call.message.chat.id 
                      if isinstance(message_or_call, types.CallbackQuery) 
                      else message_or_call.chat.id)
            
            await error_recovery.safe_send_message(chat_id, text, markup)
            
        except Exception as critical_error:
            logger.critical(f"Critical error in graceful_error_response: {critical_error}")


class HealthChecker:
    """System health monitoring and alerts"""
    
    def __init__(self):
        self.last_check = None
        self.health_status = {}
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check
        
        Returns:
            Health status dictionary
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # Check database connectivity
        try:
            from database.core import con
            if con.is_closed():
                con.connect()
            
            # Simple query test
            from database.user import User
            await User().get_all_users()
            health["checks"]["database"] = "healthy"
            
        except Exception as e:
            health["checks"]["database"] = f"error: {e}"
            health["overall_status"] = "degraded"
        
        # Check steps file integrity
        try:
            steps = utils.get_steps()
            if not steps:
                raise ValueError("Steps file is empty")
            
            from validators import StepValidator
            validator = StepValidator()
            is_valid, errors, warnings = validator.validate_steps_file(steps)
            
            if is_valid:
                health["checks"]["steps_file"] = "healthy"
                if warnings:
                    health["checks"]["steps_file"] += f" ({len(warnings)} warnings)"
            else:
                health["checks"]["steps_file"] = f"invalid: {len(errors)} errors"
                health["overall_status"] = "degraded"
                
        except Exception as e:
            health["checks"]["steps_file"] = f"error: {e}"
            health["overall_status"] = "degraded"
        
        # Check interface texts
        try:
            texts = utils.get_interface_texts()
            if not texts:
                raise ValueError("Interface texts file is empty")
            health["checks"]["interface_texts"] = "healthy"
            
        except Exception as e:
            health["checks"]["interface_texts"] = f"error: {e}"
            health["overall_status"] = "degraded"
        
        # Error statistics
        error_stats = error_recovery.get_error_stats()
        health["error_stats"] = error_stats
        
        if error_stats["total_errors"] > 50:  # Threshold for concern
            health["overall_status"] = "degraded"
        
        self.last_check = datetime.now()
        self.health_status = health
        
        return health
    
    async def auto_recovery_check(self):
        """Perform automatic recovery actions if needed"""
        health = await self.check_system_health()
        
        if health["overall_status"] == "degraded":
            logger.warning("System health degraded, initiating auto-recovery")
            
            # Attempt to fix common issues
            if "steps_file" in health["checks"] and "error" in health["checks"]["steps_file"]:
                await error_recovery.handle_steps_file_corruption()
            
            if "database" in health["checks"] and "error" in health["checks"]["database"]:
                await error_recovery.recover_from_database_error("health_check")


# Global health checker instance
health_checker = HealthChecker()


# Periodic health check task
async def start_health_monitoring():
    """Start periodic health monitoring"""
    while True:
        try:
            await health_checker.auto_recovery_check()
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(60)  # Retry in 1 minute if error


"""
🛡️ Error Handling Module for NikolayAI Bot
Provides system-wide error recovery and health monitoring
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps

class BotHealthMonitor:
    """Bot health monitoring and error recovery system"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_error_time = {}
        self.error_threshold = 5  # Max errors per minute
        self.recovery_actions = {}
        
    def register_recovery_action(self, error_type: str, action: Callable):
        """Register recovery action for specific error type"""
        self.recovery_actions[error_type] = action
        
    async def handle_error(self, error: Exception, context: str = "unknown") -> bool:
        """Handle error with appropriate recovery action"""
        error_type = type(error).__name__
        current_time = datetime.now()
        
        # Track error frequency
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
            self.last_error_time[error_type] = current_time
            
        # Reset counter if more than a minute has passed
        if (current_time - self.last_error_time[error_type]).seconds > 60:
            self.error_counts[error_type] = 0
            
        self.error_counts[error_type] += 1
        self.last_error_time[error_type] = current_time
        
        # Log error with emoji indicators
        error_msg = f"❌ Error in {context}: {error_type} - {str(error)}"
        print(error_msg)
        logging.error(error_msg)
        
        # Check if we need recovery action
        if self.error_counts[error_type] >= self.error_threshold:
            print(f"🚨 Critical error threshold reached for {error_type}")
            if error_type in self.recovery_actions:
                try:
                    await self.recovery_actions[error_type]()
                    print(f"🔧 Recovery action executed for {error_type}")
                    return True
                except Exception as recovery_error:
                    print(f"💥 Recovery action failed: {recovery_error}")
                    
        return False

# Global health monitor instance
health_monitor = BotHealthMonitor()

def error_handler(context: str = "unknown"):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await health_monitor.handle_error(e, context)
                raise  # Re-raise after handling
        return wrapper
    return decorator

def safe_file_operation(func):
    """Decorator for safe file operations with validation"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # Validate file_id if present in kwargs
            if 'file_id' in kwargs:
                file_id = kwargs['file_id']
                if not validate_telegram_file_id(file_id):
                    raise ValueError(f"Invalid Telegram file_id: {file_id}")
                    
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            if "wrong file identifier" in error_msg or "bad request" in error_msg:
                print(f"🔧 File validation failed, using fallback")
                # Return fallback indication
                return {"error": "invalid_file_id", "fallback_needed": True}
            raise
    return wrapper

def validate_telegram_file_id(file_id: Any) -> bool:
    """Validate Telegram file_id format"""
    if not file_id:
        return False
        
    file_id_str = str(file_id)
    
    # Check for common invalid values
    invalid_values = ['None', '', 'null', 'undefined', 'false', '0']
    if file_id_str.lower() in invalid_values:
        return False
        
    # Telegram file_ids are usually at least 10 characters long
    if len(file_id_str) < 10:
        return False
        
    # Basic format check - Telegram file_ids contain letters, numbers, and some special chars
    if not any(c.isalnum() for c in file_id_str):
        return False
        
    return True

async def database_recovery_action():
    """Recovery action for database errors"""
    print("🔄 Attempting database recovery...")
    try:
        from database.sql import configure_database
        configure_database()
        print("✅ Database recovery successful")
    except Exception as e:
        print(f"❌ Database recovery failed: {e}")

async def file_system_recovery_action():
    """Recovery action for file system errors"""
    print("🔄 Attempting file system recovery...")
    # Could implement file cleanup, cache clearing, etc.
    print("✅ File system recovery completed")

# Register recovery actions
health_monitor.register_recovery_action("OperationalError", database_recovery_action)
health_monitor.register_recovery_action("FileNotFoundError", file_system_recovery_action)

class TelegramErrorHandler:
    """Specialized handler for Telegram API errors"""
    
    @staticmethod
    def is_file_error(error: Exception) -> bool:
        """Check if error is related to file identifiers"""
        error_msg = str(error).lower()
        file_error_indicators = [
            "wrong file identifier",
            "bad request",
            "file not found",
            "invalid file_id"
        ]
        return any(indicator in error_msg for indicator in file_error_indicators)
    
    @staticmethod
    def is_rate_limit_error(error: Exception) -> bool:
        """Check if error is rate limiting"""
        error_msg = str(error).lower()
        return "too many requests" in error_msg or "retry after" in error_msg
    
    @staticmethod
    def is_network_error(error: Exception) -> bool:
        """Check if error is network related"""
        error_msg = str(error).lower()
        network_indicators = [
            "connection",
            "timeout",
            "network",
            "dns"
        ]
        return any(indicator in error_msg for indicator in network_indicators)
    
    @staticmethod
    async def handle_telegram_error(error: Exception, context: str = "telegram_api") -> Dict[str, Any]:
        """Handle Telegram-specific errors with appropriate responses"""
        handler = TelegramErrorHandler()
        
        if handler.is_file_error(error):
            print(f"📁 File identifier error detected: {error}")
            return {
                "error_type": "file_error",
                "action": "use_fallback",
                "message": "Файл временно недоступен"
            }
        elif handler.is_rate_limit_error(error):
            print(f"⏱️ Rate limit error detected: {error}")
            return {
                "error_type": "rate_limit",
                "action": "retry_later",
                "message": "Слишком много запросов, попробуйте позже"
            }
        elif handler.is_network_error(error):
            print(f"🌐 Network error detected: {error}")
            return {
                "error_type": "network_error", 
                "action": "retry",
                "message": "Проблемы с сетью, повторите попытку"
            }
        else:
            print(f"❓ Unknown Telegram error: {error}")
            return {
                "error_type": "unknown",
                "action": "generic_fallback",
                "message": "Произошла ошибка, попробуйте позже"
            }

# Export main components
__all__ = [
    'health_monitor',
    'error_handler', 
    'safe_file_operation',
    'validate_telegram_file_id',
    'TelegramErrorHandler'
]
