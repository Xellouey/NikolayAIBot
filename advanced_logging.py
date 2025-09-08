"""
Улучшенная система логирования ошибок для NikolayAI Telegram бота
Обеспечивает структурированное логирование с контекстом и метриками
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from collections import defaultdict, deque

from errors import ErrorType, ErrorSeverity, ErrorContext


@dataclass
class LogMetrics:
    """Метрики логирования"""
    total_logs: int = 0
    error_logs: int = 0
    warning_logs: int = 0
    info_logs: int = 0
    critical_logs: int = 0
    
    # Метрики по типам ошибок
    telegram_api_errors: int = 0
    database_errors: int = 0
    network_errors: int = 0
    validation_errors: int = 0
    state_errors: int = 0
    
    # Метрики производительности
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    slow_operations: int = 0  # операции > 5 сек
    
    # Метрики пользователей
    affected_users: set = None
    error_prone_users: Dict[int, int] = None  # user_id -> error_count
    
    def __post_init__(self):
        if self.affected_users is None:
            self.affected_users = set()
        if self.error_prone_users is None:
            self.error_prone_users = defaultdict(int)


class RotatingFileHandler(logging.Handler):
    """Кастомный handler для ротации логов"""
    
    def __init__(self, filename: str, max_bytes: int = 10*1024*1024, backup_count: int = 5):
        super().__init__()
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.current_size = 0
        
        # Создаем директорию если не существует
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
    def emit(self, record):
        """Записать лог запись"""
        try:
            msg = self.format(record)
            
            # Проверяем нужна ли ротация
            if self.current_size + len(msg.encode('utf-8')) > self.max_bytes:
                self._rotate_logs()
            
            # Записываем в файл
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
                self.current_size += len(msg.encode('utf-8'))
                
        except Exception:
            self.handleError(record)
    
    def _rotate_logs(self):
        """Ротация логов"""
        try:
            # Переименовываем существующие файлы
            for i in range(self.backup_count - 1, 0, -1):
                old_name = f"{self.filename}.{i}"
                new_name = f"{self.filename}.{i + 1}"
                if Path(old_name).exists():
                    Path(old_name).rename(new_name)
            
            # Переименовываем текущий файл
            if Path(self.filename).exists():
                Path(self.filename).rename(f"{self.filename}.1")
            
            self.current_size = 0
            
        except Exception as e:
            print(f"Ошибка ротации логов: {e}")


class StructuredLogFormatter(logging.Formatter):
    """Форматтер для структурированных логов"""
    
    def format(self, record):
        """Форматировать запись в структурированный JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем дополнительные поля из record
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'handler_name'):
            log_data['handler_name'] = record.handler_name
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        if hasattr(record, 'error_context'):
            log_data['error_context'] = record.error_context
        if hasattr(record, 'response_time'):
            log_data['response_time'] = record.response_time
        if hasattr(record, 'additional_data'):
            log_data['additional_data'] = record.additional_data
        
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class AdvancedLogger:
    """Улучшенная система логирования"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.metrics = LogMetrics()
        self.recent_errors = deque(maxlen=1000)  # Последние 1000 ошибок
        self.performance_data = deque(maxlen=5000)  # Данные производительности
        
        # Настройка логгеров
        self._setup_loggers()
        
        # Периодическая очистка данных
        self._last_cleanup = datetime.now()
        
    def _setup_loggers(self):
        """Настроить различные логгеры"""
        # Основной логгер ошибок
        self.error_logger = logging.getLogger('nikolayai.errors')
        self.error_logger.setLevel(logging.DEBUG)
        
        error_handler = RotatingFileHandler(
            self.log_dir / "errors.jsonl",
            max_bytes=50*1024*1024,  # 50MB
            backup_count=10
        )
        error_handler.setFormatter(StructuredLogFormatter())
        self.error_logger.addHandler(error_handler)
        
        # Логгер производительности
        self.performance_logger = logging.getLogger('nikolayai.performance')
        self.performance_logger.setLevel(logging.INFO)
        
        perf_handler = RotatingFileHandler(
            self.log_dir / "performance.jsonl",
            max_bytes=30*1024*1024,  # 30MB
            backup_count=5
        )
        perf_handler.setFormatter(StructuredLogFormatter())
        self.performance_logger.addHandler(perf_handler)
        
        # Логгер пользовательских действий
        self.user_logger = logging.getLogger('nikolayai.users')
        self.user_logger.setLevel(logging.INFO)
        
        user_handler = RotatingFileHandler(
            self.log_dir / "user_actions.jsonl",
            max_bytes=20*1024*1024,  # 20MB
            backup_count=3
        )
        user_handler.setFormatter(StructuredLogFormatter())
        self.user_logger.addHandler(user_handler)
        
        # Логгер системных событий
        self.system_logger = logging.getLogger('nikolayai.system')
        self.system_logger.setLevel(logging.INFO)
        
        system_handler = RotatingFileHandler(
            self.log_dir / "system.jsonl",
            max_bytes=10*1024*1024,  # 10MB
            backup_count=3
        )
        system_handler.setFormatter(StructuredLogFormatter())
        self.system_logger.addHandler(system_handler)
    
    def log_error(self, error: Exception, context: ErrorContext, error_type: ErrorType, severity: ErrorSeverity):
        """Логировать ошибку с полным контекстом"""
        # Обновляем метрики
        self.metrics.total_logs += 1
        self.metrics.error_logs += 1
        
        if severity == ErrorSeverity.CRITICAL:
            self.metrics.critical_logs += 1
        
        # Учитываем тип ошибки
        if error_type == ErrorType.TELEGRAM_API:
            self.metrics.telegram_api_errors += 1
        elif error_type == ErrorType.DATABASE:
            self.metrics.database_errors += 1
        elif error_type == ErrorType.NETWORK:
            self.metrics.network_errors += 1
        elif error_type == ErrorType.VALIDATION:
            self.metrics.validation_errors += 1
        elif error_type == ErrorType.STATE_CORRUPTION:
            self.metrics.state_errors += 1
        
        # Учитываем пользователя
        if context.user_id:
            self.metrics.affected_users.add(context.user_id)
            self.metrics.error_prone_users[context.user_id] += 1
        
        # Сохраняем в recent_errors
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type.value,
            'severity': severity.value,
            'message': str(error),
            'user_id': context.user_id,
            'handler': context.handler,
            'context': asdict(context)
        }
        self.recent_errors.append(error_record)
        
        # Логируем в файл
        self.error_logger.error(
            f"{error_type.value.upper()}: {str(error)}",
            extra={
                'user_id': context.user_id,
                'handler_name': context.handler,
                'error_type': error_type.value,
                'error_severity': severity.value,
                'error_context': asdict(context),
                'additional_data': context.additional_data
            },
            exc_info=True
        )
    
    def log_performance(self, operation: str, duration: float, user_id: Optional[int] = None, 
                       success: bool = True, additional_data: Optional[Dict] = None):
        """Логировать данные производительности"""
        self.metrics.total_logs += 1
        
        # Обновляем метрики производительности
        if duration > self.metrics.max_response_time:
            self.metrics.max_response_time = duration
        
        if duration > 5.0:  # Медленная операция
            self.metrics.slow_operations += 1
        
        # Пересчитываем среднее время ответа
        if len(self.performance_data) > 0:
            total_time = sum(d['duration'] for d in self.performance_data) + duration
            self.metrics.avg_response_time = total_time / (len(self.performance_data) + 1)
        else:
            self.metrics.avg_response_time = duration
        
        # Сохраняем данные
        perf_record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration': duration,
            'user_id': user_id,
            'success': success,
            'additional_data': additional_data or {}
        }
        self.performance_data.append(perf_record)
        
        # Логируем в файл
        self.performance_logger.info(
            f"Operation {operation} took {duration:.3f}s",
            extra={
                'operation': operation,
                'response_time': duration,
                'user_id': user_id,
                'success': success,
                'additional_data': additional_data
            }
        )
    
    def log_user_action(self, user_id: int, action: str, additional_data: Optional[Dict] = None):
        """Логировать действие пользователя"""
        self.metrics.total_logs += 1
        
        self.user_logger.info(
            f"User {user_id} performed action: {action}",
            extra={
                'user_id': user_id,
                'action': action,
                'additional_data': additional_data or {}
            }
        )
    
    def log_system_event(self, event: str, level: str = "INFO", additional_data: Optional[Dict] = None):
        """Логировать системное событие"""
        self.metrics.total_logs += 1
        
        log_method = getattr(self.system_logger, level.lower(), self.system_logger.info)
        log_method(
            f"System event: {event}",
            extra={
                'event': event,
                'additional_data': additional_data or {}
            }
        )
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получить сводку метрик"""
        return {
            'total_logs': self.metrics.total_logs,
            'error_distribution': {
                'errors': self.metrics.error_logs,
                'warnings': self.metrics.warning_logs,
                'info': self.metrics.info_logs,
                'critical': self.metrics.critical_logs
            },
            'error_types': {
                'telegram_api': self.metrics.telegram_api_errors,
                'database': self.metrics.database_errors,
                'network': self.metrics.network_errors,
                'validation': self.metrics.validation_errors,
                'state_corruption': self.metrics.state_errors
            },
            'performance': {
                'avg_response_time': round(self.metrics.avg_response_time, 3),
                'max_response_time': round(self.metrics.max_response_time, 3),
                'slow_operations': self.metrics.slow_operations
            },
            'users': {
                'affected_users_count': len(self.metrics.affected_users),
                'top_error_users': dict(sorted(
                    self.metrics.error_prone_users.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10])
            }
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """Получить последние ошибки"""
        return list(self.recent_errors)[-limit:]
    
    def get_performance_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Получить статистику производительности за последние N часов"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_data = [
            d for d in self.performance_data
            if datetime.fromisoformat(d['timestamp']) > cutoff_time
        ]
        
        if not recent_data:
            return {}
        
        durations = [d['duration'] for d in recent_data]
        operations = defaultdict(list)
        
        for d in recent_data:
            operations[d['operation']].append(d['duration'])
        
        return {
            'total_operations': len(recent_data),
            'avg_duration': sum(durations) / len(durations),
            'max_duration': max(durations),
            'min_duration': min(durations),
            'slow_operations': len([d for d in durations if d > 5.0]),
            'operations_breakdown': {
                op: {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times)
                }
                for op, times in operations.items()
            }
        }
    
    def cleanup_old_data(self, days: int = 7):
        """Очистить старые данные из памяти"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Очищаем recent_errors
        self.recent_errors = deque([
            error for error in self.recent_errors
            if datetime.fromisoformat(error['timestamp']) > cutoff_time
        ], maxlen=1000)
        
        # Очищаем performance_data
        self.performance_data = deque([
            perf for perf in self.performance_data
            if datetime.fromisoformat(perf['timestamp']) > cutoff_time
        ], maxlen=5000)
        
        self._last_cleanup = datetime.now()
    
    def should_cleanup(self) -> bool:
        """Нужна ли очистка данных"""
        return datetime.now() - self._last_cleanup > timedelta(hours=6)


# Глобальный экземпляр улучшенного логгера
advanced_logger = AdvancedLogger()


# Декоратор для логирования производительности
def log_performance(operation_name: str = None):
    """Декоратор для автоматического логирования производительности"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Пытаемся извлечь user_id из аргументов
                user_id = None
                for arg in args:
                    if hasattr(arg, 'from_user') and arg.from_user:
                        user_id = arg.from_user.id
                        break
                
                advanced_logger.log_performance(operation, duration, user_id, True)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Пытаемся извлечь user_id из аргументов
                user_id = None
                for arg in args:
                    if hasattr(arg, 'from_user') and arg.from_user:
                        user_id = arg.from_user.id
                        break
                
                advanced_logger.log_performance(operation, duration, user_id, False)
                raise
        
        def sync_wrapper(*args, **kwargs):
            operation = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                advanced_logger.log_performance(operation, duration, None, True)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                advanced_logger.log_performance(operation, duration, None, False)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Интеграция с существующей системой
def integrate_with_error_handler():
    """Интегрировать с существующим ErrorHandler"""
    from errors import global_error_handler
    
    # Заменяем метод логирования в ErrorHandler
    original_log_error = global_error_handler.logger.log_error
    
    def enhanced_log_error(error: Exception, context: ErrorContext, error_type: ErrorType, severity: ErrorSeverity):
        # Сначала используем оригинальное логирование
        original_log_error(error, context, error_type, severity)
        
        # Затем используем улучшенное логирование
        advanced_logger.log_error(error, context, error_type, severity)
    
    global_error_handler.logger.log_error = enhanced_log_error


# Автоматическая интеграция при импорте
integrate_with_error_handler()