"""
Database Resilience - система резилиентных операций с базой данных
Обеспечивает retry логику, обработку сбоев подключения и graceful degradation
"""

import asyncio
import logging
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import peewee
from peewee import OperationalError, InterfaceError, DatabaseError

from errors import global_error_handler, ErrorContext, ErrorType, ErrorSeverity


class DatabaseConnectionError(Exception):
    """Исключение для ошибок подключения к базе данных"""
    pass


class DatabaseOperationError(Exception):
    """Исключение для ошибок операций с базой данных"""
    pass


class DatabaseHealthChecker:
    """Проверка состояния базы данных"""
    
    def __init__(self, database_connection):
        self.db = database_connection
        self.last_check = None
        self.is_healthy = True
        self.check_interval = timedelta(minutes=5)
        self.logger = logging.getLogger(__name__)
    
    async def check_health(self) -> bool:
        """Проверить состояние подключения к БД"""
        try:
            # Простой запрос для проверки соединения
            self.db.execute_sql("SELECT 1")
            self.is_healthy = True
            self.last_check = datetime.now()
            self.logger.debug("✅ База данных доступна")
            return True
            
        except Exception as e:
            self.is_healthy = False
            self.last_check = datetime.now()
            self.logger.error(f"❌ База данных недоступна: {e}")
            return False
    
    def should_check_health(self) -> bool:
        """Нужно ли проверять состояние БД"""
        if self.last_check is None:
            return True
        return datetime.now() - self.last_check > self.check_interval
    
    async def ensure_healthy(self) -> bool:
        """Убедиться что БД доступна"""
        if self.should_check_health():
            return await self.check_health()
        return self.is_healthy


class ConnectionPool:
    """Простой пул подключений к базе данных"""
    
    def __init__(self, database_connection, pool_size: int = 5):
        self.db = database_connection
        self.pool_size = pool_size
        self.active_connections = 0
        self.max_retries = 3
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def get_connection(self):
        """Получить подключение из пула"""
        if self.active_connections >= self.pool_size:
            # Ждем освобождения подключения
            await asyncio.sleep(0.1)
        
        self.active_connections += 1
        try:
            # Проверяем подключение
            if self.db.is_closed():
                self.db.connect()
            yield self.db
        finally:
            self.active_connections -= 1


class ResilientDatabaseManager:
    """Менеджер резилиентных операций с базой данных"""
    
    def __init__(self, database_connection):
        self.db = database_connection
        self.health_checker = DatabaseHealthChecker(database_connection)
        self.connection_pool = ConnectionPool(database_connection)
        self.logger = logging.getLogger(__name__)
        
        # Настройки retry
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 30.0
        self.backoff_factor = 2.0
        
        # Cache для аварийного режима
        self.emergency_cache = {}
        self.cache_ttl = timedelta(minutes=10)
        
    async def execute_with_retry(self, 
                               operation: Callable,
                               operation_name: str = "database_operation",
                               context: Optional[Dict[str, Any]] = None,
                               *args, **kwargs) -> Any:
        """
        Выполнить операцию с базой данных с retry логикой
        
        Args:
            operation: Функция операции с БД
            operation_name: Название операции для логирования
            context: Дополнительный контекст для логирования
            *args, **kwargs: Аргументы для операции
            
        Returns:
            Результат операции
            
        Raises:
            DatabaseOperationError: Если операция не удалась после всех попыток
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Проверяем состояние БД
                if not await self.health_checker.ensure_healthy():
                    if attempt == 0:
                        self.logger.warning(f"🔄 БД недоступна, попытка выполнения {operation_name}")
                
                # Выполняем операцию через пул подключений
                async with self.connection_pool.get_connection() as conn:
                    result = await operation(*args, **kwargs)
                    
                    self.logger.debug(f"✅ {operation_name} выполнена успешно (попытка {attempt + 1})")
                    return result
                    
            except (OperationalError, InterfaceError, DatabaseError) as e:
                last_error = e
                error_str = str(e)
                
                # Классифицируем ошибку
                if any(keyword in error_str.lower() for keyword in ['connection', 'connect', 'network']):
                    error_type = ErrorType.DATABASE
                    severity = ErrorSeverity.HIGH
                    is_retryable = True
                elif any(keyword in error_str.lower() for keyword in ['timeout', 'deadlock']):
                    error_type = ErrorType.DATABASE
                    severity = ErrorSeverity.MEDIUM
                    is_retryable = True
                elif any(keyword in error_str.lower() for keyword in ['constraint', 'duplicate']):
                    error_type = ErrorType.DATABASE
                    severity = ErrorSeverity.MEDIUM
                    is_retryable = False
                else:
                    error_type = ErrorType.DATABASE
                    severity = ErrorSeverity.HIGH
                    is_retryable = True
                
                # Логируем ошибку
                error_context = ErrorContext(
                    handler=operation_name,
                    additional_data={
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "context": context or {},
                        "error_details": error_str
                    }
                )
                
                global_error_handler.logger.log_error(e, error_context, error_type, severity)
                
                # Если ошибка не подлежит retry или это последняя попытка
                if not is_retryable or attempt == self.max_retries - 1:
                    break
                
                # Вычисляем задержку для retry
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                self.logger.warning(
                    f"🔄 {operation_name} не удалась (попытка {attempt + 1}/{self.max_retries}), "
                    f"повтор через {delay:.1f} сек: {error_str}"
                )
                
                await asyncio.sleep(delay)
                
                # Пробуем переподключиться
                try:
                    if self.db.is_closed():
                        self.db.connect()
                except Exception as reconnect_error:
                    self.logger.error(f"❌ Ошибка переподключения: {reconnect_error}")
            
            except Exception as e:
                # Неожиданная ошибка
                last_error = e
                error_context = ErrorContext(
                    handler=operation_name,
                    additional_data={
                        "attempt": attempt + 1,
                        "unexpected_error": True,
                        "context": context or {}
                    }
                )
                
                global_error_handler.logger.log_error(
                    e, error_context, ErrorType.UNKNOWN, ErrorSeverity.CRITICAL
                )
                break
        
        # Все попытки исчерпаны
        raise DatabaseOperationError(
            f"Операция {operation_name} не удалась после {self.max_retries} попыток. "
            f"Последняя ошибка: {last_error}"
        )
    
    async def get_from_cache_or_db(self,
                                 cache_key: str,
                                 db_operation: Callable,
                                 operation_name: str = "cached_operation",
                                 *args, **kwargs) -> Any:
        """
        Получить данные из кэша или БД с fallback механизмом
        
        Args:
            cache_key: Ключ для кэширования
            db_operation: Операция с БД
            operation_name: Название операции
            *args, **kwargs: Аргументы для операции
            
        Returns:
            Данные из БД или кэша
        """
        # Проверяем кэш
        cached_data = self.get_from_cache(cache_key)
        if cached_data is not None:
            self.logger.debug(f"📦 Данные получены из кэша: {cache_key}")
            return cached_data
        
        try:
            # Пытаемся получить из БД
            result = await self.execute_with_retry(
                db_operation, 
                operation_name,
                {"cache_key": cache_key},
                *args, **kwargs
            )
            
            # Сохраняем в кэш
            self.save_to_cache(cache_key, result)
            return result
            
        except DatabaseOperationError:
            # БД недоступна, проверяем есть ли устаревшие данные в кэше
            expired_data = self.get_from_cache(cache_key, ignore_ttl=True)
            if expired_data is not None:
                self.logger.warning(f"⚠️ Используем устаревшие данные из кэша: {cache_key}")
                return expired_data
            
            # Нет данных вообще
            self.logger.error(f"❌ Нет данных для ключа {cache_key} ни в БД, ни в кэше")
            raise
    
    def get_from_cache(self, key: str, ignore_ttl: bool = False) -> Optional[Any]:
        """Получить данные из кэша"""
        if key not in self.emergency_cache:
            return None
        
        cached_item = self.emergency_cache[key]
        
        if not ignore_ttl:
            if datetime.now() - cached_item['timestamp'] > self.cache_ttl:
                # Данные устарели
                return None
        
        return cached_item['data']
    
    def save_to_cache(self, key: str, data: Any):
        """Сохранить данные в кэш"""
        self.emergency_cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Ограничиваем размер кэша
        if len(self.emergency_cache) > 1000:
            # Удаляем самые старые записи
            sorted_items = sorted(
                self.emergency_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            
            for old_key, _ in sorted_items[:100]:  # Удаляем 100 самых старых
                del self.emergency_cache[old_key]
    
    def clear_cache(self):
        """Очистить кэш"""
        self.emergency_cache.clear()
        self.logger.info("🗑️ Кэш очищен")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Тестовая проверка подключения"""
        start_time = datetime.now()
        
        try:
            await self.health_checker.check_health()
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy" if self.health_checker.is_healthy else "unhealthy",
                "response_time_ms": round(response_time * 1000, 2),
                "active_connections": self.connection_pool.active_connections,
                "cache_size": len(self.emergency_cache),
                "last_check": self.health_checker.last_check.isoformat() if self.health_checker.last_check else None
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "error",
                "error": str(e),
                "response_time_ms": round(response_time * 1000, 2),
                "active_connections": self.connection_pool.active_connections,
                "cache_size": len(self.emergency_cache)
            }


# Создаем глобальный экземпляр (будет инициализирован в nikolayai.py)
resilient_db_manager: Optional[ResilientDatabaseManager] = None


def init_resilient_db_manager(database_connection):
    """Инициализировать глобальный менеджер БД"""
    global resilient_db_manager
    resilient_db_manager = ResilientDatabaseManager(database_connection)
    logging.info("✅ Резилиентный менеджер БД инициализирован")


# Декораторы для упрощения использования
def resilient_db_operation(operation_name: str = None, use_cache: bool = False, cache_key: str = None):
    """
    Декоратор для автоматического добавления резилиентности к операциям БД
    
    Args:
        operation_name: Название операции для логирования
        use_cache: Использовать ли кэширование
        cache_key: Ключ для кэширования (если не указан, генерируется автоматически)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if resilient_db_manager is None:
                # Fallback если менеджер не инициализирован
                return await func(*args, **kwargs)
            
            op_name = operation_name or func.__name__
            
            if use_cache:
                # Генерируем ключ кэша если не указан
                cache_key_final = cache_key or f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                return await resilient_db_manager.get_from_cache_or_db(
                    cache_key_final, func, op_name, *args, **kwargs
                )
            else:
                return await resilient_db_manager.execute_with_retry(
                    func, op_name, None, *args, **kwargs
                )
        
        return wrapper
    return decorator