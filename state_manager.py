"""
State Manager - система безопасного управления состояниями FSM
Предотвращает повреждение состояний и обеспечивает восстановление
"""

import logging
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from errors import (
    global_error_handler, ErrorContext, ErrorType, ErrorSeverity, 
    StateCorruptionError
)


class StateBackup:
    """Класс для резервного копирования состояний"""
    
    def __init__(self):
        self.backups: Dict[int, Dict[str, Any]] = {}
        self.backup_ttl = timedelta(hours=24)
        self.logger = logging.getLogger(__name__)
    
    def save_backup(self, user_id: int, state_name: Optional[str], state_data: Dict[str, Any]):
        """Сохранить резервную копию состояния"""
        try:
            self.backups[user_id] = {
                'state_name': state_name,
                'state_data': state_data.copy(),
                'timestamp': datetime.now(),
                'backup_id': f"backup_{user_id}_{int(datetime.now().timestamp())}"
            }
            
            self.logger.debug(f"💾 Резервная копия состояния сохранена для пользователя {user_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения резервной копии для пользователя {user_id}: {e}")
    
    def get_backup(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить резервную копию состояния"""
        if user_id not in self.backups:
            return None
        
        backup = self.backups[user_id]
        
        # Проверяем срок жизни backup
        if datetime.now() - backup['timestamp'] > self.backup_ttl:
            del self.backups[user_id]
            self.logger.debug(f"🗑️ Устаревшая резервная копия удалена для пользователя {user_id}")
            return None
        
        return backup
    
    def clear_backup(self, user_id: int):
        """Очистить резервную копию"""
        if user_id in self.backups:
            del self.backups[user_id]
            self.logger.debug(f"🗑️ Резервная копия очищена для пользователя {user_id}")
    
    def cleanup_expired_backups(self):
        """Очистить устаревшие резервные копии"""
        current_time = datetime.now()
        expired_users = []
        
        for user_id, backup in self.backups.items():
            if current_time - backup['timestamp'] > self.backup_ttl:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.backups[user_id]
        
        if expired_users:
            self.logger.info(f"🗑️ Очищено {len(expired_users)} устаревших резервных копий")


class StateValidator:
    """Валидатор состояний FSM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Определяем допустимые типы данных для состояний
        self.allowed_types = (str, int, float, bool, list, dict, type(None))
        
        # Максимальные размеры для данных состояния
        self.max_string_length = 10000
        self.max_list_length = 1000
        self.max_dict_size = 1000
        self.max_total_size = 50000  # байт
    
    def validate_state_data(self, state_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Валидировать данные состояния
        
        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Проверяем общий размер данных
            serialized = json.dumps(state_data, ensure_ascii=False)
            if len(serialized.encode('utf-8')) > self.max_total_size:
                return False, f"Размер данных состояния превышает {self.max_total_size} байт"
            
            # Проверяем каждое поле
            for key, value in state_data.items():
                if not isinstance(key, str):
                    return False, f"Ключ '{key}' не является строкой"
                
                if not isinstance(value, self.allowed_types):
                    return False, f"Значение для ключа '{key}' имеет недопустимый тип: {type(value)}"
                
                # Проверяем строки
                if isinstance(value, str) and len(value) > self.max_string_length:
                    return False, f"Строка для ключа '{key}' слишком длинная"
                
                # Проверяем списки
                if isinstance(value, list) and len(value) > self.max_list_length:
                    return False, f"Список для ключа '{key}' слишком длинный"
                
                # Проверяем словари
                if isinstance(value, dict) and len(value) > self.max_dict_size:
                    return False, f"Словарь для ключа '{key}' слишком большой"
            
            return True, None
            
        except Exception as e:
            return False, f"Ошибка валидации: {e}"
    
    def sanitize_state_data(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Очистить и исправить данные состояния"""
        sanitized = {}
        
        for key, value in state_data.items():
            # Приводим ключ к строке
            clean_key = str(key)[:100]  # Ограничиваем длину ключа
            
            # Очищаем значение
            if isinstance(value, str):
                sanitized[clean_key] = value[:self.max_string_length]
            elif isinstance(value, list):
                sanitized[clean_key] = value[:self.max_list_length]
            elif isinstance(value, dict):
                # Берем только первые N элементов словаря
                items = list(value.items())[:self.max_dict_size]
                sanitized[clean_key] = dict(items)
            elif isinstance(value, self.allowed_types):
                sanitized[clean_key] = value
            else:
                # Неподдерживаемый тип - конвертируем в строку
                sanitized[clean_key] = str(value)[:self.max_string_length]
        
        return sanitized


class SafeStateManager:
    """Менеджер безопасных операций с состояниями FSM"""
    
    def __init__(self):
        self.backup_manager = StateBackup()
        self.validator = StateValidator()
        self.logger = logging.getLogger(__name__)
        
        # Счетчики для мониторинга
        self.operation_counters = {
            'get_success': 0,
            'get_error': 0,
            'set_success': 0,
            'set_error': 0,
            'update_success': 0,
            'update_error': 0,
            'clear_success': 0,
            'clear_error': 0,
            'corruption_detected': 0,
            'recoveries_performed': 0
        }
    
    async def safe_get_state_data(self, state: FSMContext, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Безопасно получить данные состояния
        
        Args:
            state: FSM контекст
            user_id: ID пользователя для логирования
            
        Returns:
            Dict с данными состояния или пустой dict при ошибке
        """
        try:
            state_data = await state.get_data()
            
            # Валидируем полученные данные
            is_valid, error_msg = self.validator.validate_state_data(state_data)
            
            if not is_valid:
                self.logger.warning(f"⚠️ Некорректные данные состояния для пользователя {user_id}: {error_msg}")
                
                # Пытаемся очистить данные
                sanitized_data = self.validator.sanitize_state_data(state_data)
                
                # Сохраняем очищенные данные
                await state.set_data(sanitized_data)
                
                self.operation_counters['get_success'] += 1
                return sanitized_data
            
            self.operation_counters['get_success'] += 1
            return state_data
            
        except Exception as e:
            self.operation_counters['get_error'] += 1
            
            # Логируем ошибку
            context = ErrorContext(
                user_id=user_id,
                handler="safe_get_state_data",
                additional_data={"error_details": str(e)}
            )
            
            global_error_handler.logger.log_error(
                e, context, ErrorType.STATE_CORRUPTION, ErrorSeverity.MEDIUM
            )
            
            # Пытаемся восстановить из backup
            if user_id:
                backup = self.backup_manager.get_backup(user_id)
                if backup:
                    self.logger.info(f"🔄 Восстановление состояния из backup для пользователя {user_id}")
                    try:
                        await state.set_data(backup['state_data'])
                        self.operation_counters['recoveries_performed'] += 1
                        return backup['state_data']
                    except Exception as restore_error:
                        self.logger.error(f"❌ Ошибка восстановления из backup: {restore_error}")
            
            # Возвращаем пустое состояние
            return {}
    
    async def safe_set_state(self, state: FSMContext, new_state: Union[State, str, None], 
                           user_id: Optional[int] = None) -> bool:
        """
        Безопасно установить состояние
        
        Args:
            state: FSM контекст
            new_state: Новое состояние
            user_id: ID пользователя для логирования
            
        Returns:
            bool: True если операция успешна
        """
        try:
            # Сохраняем backup текущего состояния
            if user_id:
                try:
                    current_state_name = await state.get_state()
                    current_data = await state.get_data()
                    self.backup_manager.save_backup(
                        user_id, 
                        str(current_state_name) if current_state_name else None,
                        current_data
                    )
                except Exception as backup_error:
                    self.logger.warning(f"⚠️ Не удалось создать backup для пользователя {user_id}: {backup_error}")
            
            # Устанавливаем новое состояние
            await state.set_state(new_state)
            
            self.operation_counters['set_success'] += 1
            self.logger.debug(f"✅ Состояние установлено для пользователя {user_id}: {new_state}")
            return True
            
        except Exception as e:
            self.operation_counters['set_error'] += 1
            
            context = ErrorContext(
                user_id=user_id,
                handler="safe_set_state",
                additional_data={
                    "new_state": str(new_state),
                    "error_details": str(e)
                }
            )
            
            global_error_handler.logger.log_error(
                e, context, ErrorType.STATE_CORRUPTION, ErrorSeverity.HIGH
            )
            
            return False
    
    async def safe_update_data(self, state: FSMContext, data: Dict[str, Any], 
                             user_id: Optional[int] = None) -> bool:
        """
        Безопасно обновить данные состояния
        
        Args:
            state: FSM контекст
            data: Данные для обновления
            user_id: ID пользователя для логирования
            
        Returns:
            bool: True если операция успешна
        """
        try:
            # Валидируем новые данные
            is_valid, error_msg = self.validator.validate_state_data(data)
            
            if not is_valid:
                self.logger.warning(f"⚠️ Некорректные данные для обновления пользователя {user_id}: {error_msg}")
                # Очищаем данные
                data = self.validator.sanitize_state_data(data)
            
            # Сохраняем backup
            if user_id:
                try:
                    current_state_name = await state.get_state()
                    current_data = await state.get_data()
                    self.backup_manager.save_backup(
                        user_id,
                        str(current_state_name) if current_state_name else None,
                        current_data
                    )
                except Exception as backup_error:
                    self.logger.warning(f"⚠️ Не удалось создать backup для пользователя {user_id}: {backup_error}")
            
            # Обновляем данные
            await state.update_data(**data)
            
            self.operation_counters['update_success'] += 1
            self.logger.debug(f"✅ Данные состояния обновлены для пользователя {user_id}")
            return True
            
        except Exception as e:
            self.operation_counters['update_error'] += 1
            
            context = ErrorContext(
                user_id=user_id,
                handler="safe_update_data",
                additional_data={
                    "update_keys": list(data.keys()) if isinstance(data, dict) else str(data),
                    "error_details": str(e)
                }
            )
            
            global_error_handler.logger.log_error(
                e, context, ErrorType.STATE_CORRUPTION, ErrorSeverity.MEDIUM
            )
            
            return False
    
    async def safe_clear_state(self, state: FSMContext, user_id: Optional[int] = None) -> bool:
        """
        Безопасно очистить состояние
        
        Args:
            state: FSM контекст
            user_id: ID пользователя для логирования
            
        Returns:
            bool: True если операция успешна
        """
        try:
            # Очищаем backup при успешной очистке состояния
            if user_id:
                self.backup_manager.clear_backup(user_id)
            
            await state.clear()
            
            self.operation_counters['clear_success'] += 1
            self.logger.debug(f"✅ Состояние очищено для пользователя {user_id}")
            return True
            
        except Exception as e:
            self.operation_counters['clear_error'] += 1
            
            context = ErrorContext(
                user_id=user_id,
                handler="safe_clear_state",
                additional_data={"error_details": str(e)}
            )
            
            global_error_handler.logger.log_error(
                e, context, ErrorType.STATE_CORRUPTION, ErrorSeverity.MEDIUM
            )
            
            return False
    
    async def handle_corrupted_state(self, state: FSMContext, user_id: int, 
                                   corruption_details: str = "") -> bool:
        """
        Обработать поврежденное состояние
        
        Args:
            state: FSM контекст
            user_id: ID пользователя
            corruption_details: Детали повреждения
            
        Returns:
            bool: True если восстановление прошло успешно
        """
        self.operation_counters['corruption_detected'] += 1
        
        self.logger.error(f"🚨 Обнаружено повреждение состояния для пользователя {user_id}: {corruption_details}")
        
        # Пытаемся восстановить из backup
        backup = self.backup_manager.get_backup(user_id)
        
        if backup:
            try:
                self.logger.info(f"🔄 Попытка восстановления состояния из backup для пользователя {user_id}")
                
                # Очищаем текущее состояние
                await state.clear()
                
                # Восстанавливаем из backup
                if backup['state_name']:
                    await state.set_state(backup['state_name'])
                
                if backup['state_data']:
                    await state.set_data(backup['state_data'])
                
                self.operation_counters['recoveries_performed'] += 1
                self.logger.info(f"✅ Состояние восстановлено из backup для пользователя {user_id}")
                return True
                
            except Exception as restore_error:
                self.logger.error(f"❌ Ошибка восстановления из backup для пользователя {user_id}: {restore_error}")
        
        # Если восстановление не удалось, полностью очищаем состояние
        try:
            await state.clear()
            self.backup_manager.clear_backup(user_id)
            
            self.logger.warning(f"⚠️ Состояние полностью сброшено для пользователя {user_id}")
            return True
            
        except Exception as clear_error:
            self.logger.critical(f"🔥 Критическая ошибка очистки состояния для пользователя {user_id}: {clear_error}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику операций"""
        total_operations = sum(self.operation_counters.values())
        
        return {
            "total_operations": total_operations,
            "counters": self.operation_counters.copy(),
            "error_rate": (
                (self.operation_counters['get_error'] + 
                 self.operation_counters['set_error'] + 
                 self.operation_counters['update_error'] + 
                 self.operation_counters['clear_error']) / max(total_operations, 1)
            ) * 100,
            "corruption_rate": (
                self.operation_counters['corruption_detected'] / max(total_operations, 1)
            ) * 100,
            "recovery_success_rate": (
                self.operation_counters['recoveries_performed'] / 
                max(self.operation_counters['corruption_detected'], 1)
            ) * 100,
            "active_backups": len(self.backup_manager.backups)
        }
    
    def cleanup_expired_data(self):
        """Очистить устаревшие данные"""
        self.backup_manager.cleanup_expired_backups()


# Глобальный экземпляр менеджера состояний
safe_state_manager = SafeStateManager()


# Декораторы для упрощения использования
def safe_state_operation(operation_type: str = "get"):
    """
    Декоратор для безопасных операций с состоянием
    
    Args:
        operation_type: Тип операции ("get", "set", "update", "clear")
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Извлекаем FSMContext и user_id из аргументов
            state_context = None
            user_id = None
            
            for arg in args:
                if isinstance(arg, FSMContext):
                    state_context = arg
                elif hasattr(arg, 'from_user') and arg.from_user:
                    user_id = arg.from_user.id
            
            if not state_context:
                # Нет FSMContext, выполняем функцию как есть
                return await func(*args, **kwargs)
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Обрабатываем ошибку состояния
                if user_id:
                    await safe_state_manager.handle_corrupted_state(
                        state_context, user_id, f"Ошибка в {func.__name__}: {e}"
                    )
                raise StateCorruptionError(f"Состояние повреждено в {func.__name__}: {e}")
        
        return wrapper
    return decorator