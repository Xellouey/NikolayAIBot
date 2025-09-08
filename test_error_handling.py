"""
Тесты для системы обработки ошибок NikolayAI Telegram бота
Покрывает основные сценарии ошибок и восстановления
"""

import asyncio
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

# Импортируем компоненты для тестирования
from errors import (
    ErrorHandler, ErrorType, ErrorSeverity, ErrorContext,
    ContentComparator, MarkupValidator, global_error_handler,
    StateCorruptionError
)
from message_manager import MessageManager, global_message_manager
from state_manager import SafeStateManager, safe_state_manager
from database_resilience import ResilientDatabaseManager


class TestErrorClassification:
    """Тесты классификации ошибок"""
    
    def setup_method(self):
        self.error_handler = ErrorHandler()
    
    def test_telegram_api_error_classification(self):
        """Тест классификации ошибок Telegram API"""
        # Тест "message is not modified"
        error = TelegramBadRequest(method="edit_message_text", message="message is not modified")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.TELEGRAM_API
        assert severity == ErrorSeverity.LOW
        
        # Тест "message to edit not found"
        error = TelegramBadRequest(method="edit_message_text", message="message to edit not found")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.TELEGRAM_API
        assert severity == ErrorSeverity.MEDIUM
        
        # Тест общей Bad Request ошибки
        error = TelegramBadRequest(method="send_message", message="Bad Request: chat not found")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.VALIDATION
        assert severity == ErrorSeverity.MEDIUM
    
    def test_network_error_classification(self):
        """Тест классификации сетевых ошибок"""
        error = TelegramNetworkError(message="Network timeout")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.NETWORK
        assert severity == ErrorSeverity.HIGH
    
    def test_state_corruption_error_classification(self):
        """Тест классификации ошибок состояния"""
        error = StateCorruptionError("FSM state corrupted")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.STATE_CORRUPTION
        assert severity == ErrorSeverity.HIGH
    
    def test_database_error_classification(self):
        """Тест классификации ошибок базы данных"""
        error = ConnectionError("Database connection failed")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.DATABASE
        assert severity == ErrorSeverity.CRITICAL
    
    def test_unknown_error_classification(self):
        """Тест классификации неизвестных ошибок"""
        error = RuntimeError("Unknown error")
        error_type, severity = self.error_handler.classify_error(error)
        assert error_type == ErrorType.UNKNOWN
        assert severity == ErrorSeverity.HIGH


class TestContentComparator:
    """Тесты сравнения содержимого сообщений"""
    
    def setup_method(self):
        self.comparator = ContentComparator()
    
    def test_text_comparison(self):
        """Тест сравнения текста"""
        # Идентичный текст
        assert self.comparator.compare_text("Hello", "Hello") is True
        
        # Текст с пробелами
        assert self.comparator.compare_text("Hello ", " Hello") is True
        
        # Разный текст
        assert self.comparator.compare_text("Hello", "World") is False
        
        # None значения
        assert self.comparator.compare_text(None, None) is True
        assert self.comparator.compare_text("Hello", None) is False
        assert self.comparator.compare_text(None, "Hello") is False
    
    def test_markup_comparison(self):
        """Тест сравнения разметки клавиатур"""
        # Создаем mock объекты для тестирования
        markup1 = Mock()
        markup1.model_dump.return_value = {"inline_keyboard": []}
        
        markup2 = Mock()
        markup2.model_dump.return_value = {"inline_keyboard": []}
        
        # Идентичная разметка
        assert self.comparator.compare_markup(markup1, markup2) is True
        
        # None значения
        assert self.comparator.compare_markup(None, None) is True
        assert self.comparator.compare_markup(markup1, None) is False
        assert self.comparator.compare_markup(None, markup1) is False
    
    def test_content_identity_check(self):
        """Тест проверки идентичности всего содержимого"""
        markup = Mock()
        markup.model_dump.return_value = {"inline_keyboard": []}
        
        # Полностью идентичное содержимое
        assert self.comparator.is_content_identical(
            "Hello", "Hello", markup, markup
        ) is True
        
        # Разный текст
        assert self.comparator.is_content_identical(
            "Hello", "World", markup, markup
        ) is False


class TestMarkupValidator:
    """Тесты валидации разметки клавиатур"""
    
    def setup_method(self):
        self.validator = MarkupValidator()
    
    def test_inline_keyboard_validation(self):
        """Тест валидации inline клавиатур"""
        inline_markup = Mock(spec=InlineKeyboardMarkup)
        reply_markup = Mock(spec=ReplyKeyboardMarkup)
        
        assert self.validator.validate_inline_keyboard(inline_markup) is True
        assert self.validator.validate_inline_keyboard(reply_markup) is False
        assert self.validator.validate_inline_keyboard(None) is False
    
    def test_reply_keyboard_validation(self):
        """Тест валидации reply клавиатур"""
        inline_markup = Mock(spec=InlineKeyboardMarkup)
        reply_markup = Mock(spec=ReplyKeyboardMarkup)
        
        assert self.validator.validate_reply_keyboard(reply_markup) is True
        assert self.validator.validate_reply_keyboard(inline_markup) is False
        assert self.validator.validate_reply_keyboard(None) is False
    
    def test_markup_type_conversion(self):
        """Тест конвертации типов разметки"""
        inline_markup = Mock(spec=InlineKeyboardMarkup)
        reply_markup = Mock(spec=ReplyKeyboardMarkup)
        
        # Конвертация в inline тип
        result = self.validator.convert_markup_type(inline_markup, "inline")
        assert result is inline_markup
        
        result = self.validator.convert_markup_type(reply_markup, "inline")
        assert isinstance(result, InlineKeyboardMarkup)
        
        # Конвертация в reply тип
        result = self.validator.convert_markup_type(reply_markup, "reply")
        assert result is reply_markup
        
        result = self.validator.convert_markup_type(inline_markup, "reply")
        assert isinstance(result, ReplyKeyboardMarkup)


class TestMessageManager:
    """Тесты менеджера сообщений"""
    
    def setup_method(self):
        self.bot_mock = AsyncMock()
        self.message_manager = MessageManager(self.bot_mock)
    
    @pytest.mark.asyncio
    async def test_safe_message_edit_identical_content(self):
        """Тест безопасного редактирования с идентичным содержимым"""
        message_mock = Mock()
        message_mock.text = "Hello"
        message_mock.reply_markup = None
        
        # Пытаемся отредактировать на идентичное содержимое
        result = await self.message_manager.edit_message_safe(
            message_mock, "Hello", None
        )
        
        assert result is True
        message_mock.edit_text.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_safe_message_edit_different_content(self):
        """Тест безопасного редактирования с разным содержимым"""
        message_mock = AsyncMock()
        message_mock.text = "Hello"
        message_mock.reply_markup = None
        
        # Редактируем на другое содержимое
        result = await self.message_manager.edit_message_safe(
            message_mock, "World", None
        )
        
        assert result is True
        message_mock.edit_text.assert_called_once_with(
            text="World", reply_markup=None, parse_mode='HTML'
        )
    
    @pytest.mark.asyncio
    async def test_safe_message_edit_telegram_error(self):
        """Тест обработки ошибок при редактировании"""
        message_mock = AsyncMock()
        message_mock.text = "Hello"
        message_mock.reply_markup = None
        message_mock.edit_text.side_effect = TelegramBadRequest(
            method="edit_message_text", 
            message="message is not modified"
        )
        
        result = await self.message_manager.edit_message_safe(
            message_mock, "World", None
        )
        
        assert result is True  # Должен обработать ошибку как успех
    
    @pytest.mark.asyncio
    async def test_safe_message_send(self):
        """Тест безопасной отправки сообщения"""
        chat_id = 12345
        text = "Test message"
        
        result = await self.message_manager.send_message_safe(
            chat_id, text
        )
        
        self.bot_mock.send_message.assert_called_once_with(
            chat_id=chat_id,
            text=text,
            reply_markup=None,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    
    @pytest.mark.asyncio
    async def test_safe_media_send_with_fallback(self):
        """Тест отправки медиа с fallback на текст"""
        chat_id = 12345
        file_id = "test_file_id"
        caption = "Test caption"
        
        # Симулируем ошибку при отправке видео
        self.bot_mock.send_video.side_effect = TelegramBadRequest(
            method="send_video", message="Invalid file_id"
        )
        
        result = await self.message_manager.send_media_safe(
            chat_id, "video", file_id, caption
        )
        
        # Должен попытаться отправить видео, затем fallback на текст
        self.bot_mock.send_video.assert_called_once()
        self.bot_mock.send_message.assert_called_once()


class TestSafeStateManager:
    """Тесты менеджера состояний"""
    
    def setup_method(self):
        self.state_manager = SafeStateManager()
        self.mock_state = AsyncMock(spec=FSMContext)
    
    @pytest.mark.asyncio
    async def test_safe_get_state_data_success(self):
        """Тест успешного получения данных состояния"""
        test_data = {"key": "value", "number": 123}
        self.mock_state.get_data.return_value = test_data
        
        result = await self.state_manager.safe_get_state_data(
            self.mock_state, user_id=12345
        )
        
        assert result == test_data
        assert self.state_manager.operation_counters['get_success'] == 1
    
    @pytest.mark.asyncio
    async def test_safe_get_state_data_error(self):
        """Тест обработки ошибки при получении данных состояния"""
        self.mock_state.get_data.side_effect = Exception("State error")
        
        result = await self.state_manager.safe_get_state_data(
            self.mock_state, user_id=12345
        )
        
        assert result == {}  # Должен вернуть пустой словарь при ошибке
        assert self.state_manager.operation_counters['get_error'] == 1
    
    @pytest.mark.asyncio
    async def test_safe_set_state_success(self):
        """Тест успешной установки состояния"""
        from states import FSMPurchase
        
        result = await self.state_manager.safe_set_state(
            self.mock_state, FSMPurchase.promocode, user_id=12345
        )
        
        assert result is True
        self.mock_state.set_state.assert_called_once_with(FSMPurchase.promocode)
        assert self.state_manager.operation_counters['set_success'] == 1
    
    @pytest.mark.asyncio
    async def test_safe_update_data_with_validation(self):
        """Тест обновления данных с валидацией"""
        valid_data = {"lesson_id": 1, "price": 10.0}
        
        result = await self.state_manager.safe_update_data(
            self.mock_state, valid_data, user_id=12345
        )
        
        assert result is True
        self.mock_state.update_data.assert_called_once_with(**valid_data)
        assert self.state_manager.operation_counters['update_success'] == 1
    
    @pytest.mark.asyncio
    async def test_safe_clear_state(self):
        """Тест очистки состояния"""
        result = await self.state_manager.safe_clear_state(
            self.mock_state, user_id=12345
        )
        
        assert result is True
        self.mock_state.clear.assert_called_once()
        assert self.state_manager.operation_counters['clear_success'] == 1
    
    @pytest.mark.asyncio
    async def test_handle_corrupted_state_with_backup(self):
        """Тест восстановления поврежденного состояния из backup"""
        user_id = 12345
        backup_data = {"lesson_id": 1}
        
        # Создаем backup
        self.state_manager.backup_manager.save_backup(
            user_id, "FSMPurchase:promocode", backup_data
        )
        
        result = await self.state_manager.handle_corrupted_state(
            self.mock_state, user_id, "Test corruption"
        )
        
        assert result is True
        self.mock_state.clear.assert_called()
        self.mock_state.set_data.assert_called_with(backup_data)
    
    def test_statistics_collection(self):
        """Тест сбора статистики операций"""
        # Симулируем несколько операций
        self.state_manager.operation_counters['get_success'] = 10
        self.state_manager.operation_counters['get_error'] = 2
        self.state_manager.operation_counters['corruption_detected'] = 1
        self.state_manager.operation_counters['recoveries_performed'] = 1
        
        stats = self.state_manager.get_statistics()
        
        assert stats['total_operations'] == 14
        assert stats['error_rate'] > 0
        assert stats['corruption_rate'] > 0
        assert stats['recovery_success_rate'] == 100.0


class TestDatabaseResilience:
    """Тесты резилиентности базы данных"""
    
    def setup_method(self):
        self.mock_db = Mock()
        self.db_manager = ResilientDatabaseManager(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_successful_database_operation(self):
        """Тест успешной операции с базой данных"""
        async def mock_operation():
            return "success"
        
        result = await self.db_manager.execute_with_retry(
            mock_operation, "test_operation"
        )
        
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_database_operation_with_retry(self):
        """Тест операции с базой данных с retry"""
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Database unavailable")
            return "success"
        
        result = await self.db_manager.execute_with_retry(
            mock_operation, "test_operation"
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_database_operation_max_retries_exceeded(self):
        """Тест превышения максимального количества retry"""
        async def mock_operation():
            raise ConnectionError("Persistent error")
        
        with pytest.raises(Exception):
            await self.db_manager.execute_with_retry(
                mock_operation, "test_operation"
            )
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Тест функциональности кэширования"""
        cache_key = "test_key"
        test_data = {"key": "value"}
        
        # Сохраняем в кэш
        self.db_manager.save_to_cache(cache_key, test_data)
        
        # Получаем из кэша
        cached_data = self.db_manager.get_from_cache(cache_key)
        assert cached_data == test_data
        
        # Тест устаревшего кэша
        self.db_manager.emergency_cache[cache_key]['timestamp'] = (
            datetime.now() - timedelta(hours=25)
        )
        expired_data = self.db_manager.get_from_cache(cache_key)
        assert expired_data is None
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Тест проверки состояния базы данных"""
        # Мокаем успешное подключение
        self.mock_db.execute_sql.return_value = None
        
        result = await self.db_manager.test_connection()
        
        assert result['status'] == 'healthy'
        assert 'response_time_ms' in result
        assert result['response_time_ms'] >= 0


class TestIntegrationScenarios:
    """Интеграционные тесты различных сценариев ошибок"""
    
    @pytest.mark.asyncio
    async def test_message_edit_conflict_scenario(self):
        """Тест сценария конфликта редактирования сообщения"""
        message_mock = AsyncMock()
        message_mock.text = "Original text"
        message_mock.reply_markup = None
        
        # Первое редактирование успешно
        message_mock.edit_text.return_value = None
        
        message_manager = MessageManager()
        
        # Первое редактирование
        result1 = await message_manager.edit_message_safe(
            message_mock, "New text", None
        )
        assert result1 is True
        
        # Второе редактирование с той же информацией (должно быть пропущено)
        message_mock.text = "New text"  # Обновляем text как если бы сообщение было отредактировано
        result2 = await message_manager.edit_message_safe(
            message_mock, "New text", None
        )
        assert result2 is True
        
        # edit_text должен быть вызван только один раз
        assert message_mock.edit_text.call_count == 1
    
    @pytest.mark.asyncio
    async def test_state_corruption_recovery_scenario(self):
        """Тест сценария восстановления после повреждения состояния"""
        mock_state = AsyncMock()
        user_id = 12345
        
        state_manager = SafeStateManager()
        
        # Создаем backup
        backup_data = {"lesson_id": 1, "step": "payment"}
        state_manager.backup_manager.save_backup(
            user_id, "FSMPurchase:payment", backup_data
        )
        
        # Симулируем повреждение состояния
        mock_state.get_data.side_effect = Exception("Corrupted state")
        
        # Пытаемся получить данные состояния
        result = await state_manager.safe_get_state_data(mock_state, user_id)
        
        # Должен вернуть пустой словарь из-за ошибки
        assert result == {}
        
        # Восстанавливаем состояние
        recovery_result = await state_manager.handle_corrupted_state(
            mock_state, user_id, "Test corruption"
        )
        
        assert recovery_result is True
        mock_state.clear.assert_called()
        mock_state.set_data.assert_called_with(backup_data)
    
    @pytest.mark.asyncio
    async def test_database_failure_with_cache_fallback(self):
        """Тест fallback на кэш при сбое базы данных"""
        mock_db = Mock()
        db_manager = ResilientDatabaseManager(mock_db)
        
        cache_key = "test_operation"
        cached_data = {"result": "cached_value"}
        
        # Сохраняем данные в кэш
        db_manager.save_to_cache(cache_key, cached_data)
        
        # Симулируем сбой базы данных
        async def failing_operation():
            raise ConnectionError("Database down")
        
        # Пытаемся получить данные из БД или кэша
        result = await db_manager.get_from_cache_or_db(
            cache_key, failing_operation, "test_operation"
        )
        
        assert result == cached_data


# Помощные функции для запуска тестов
def run_tests():
    """Запустить все тесты системы обработки ошибок"""
    import pytest
    import sys
    
    # Настройка pytest для асинхронных тестов
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ]
    
    # Запускаем тесты
    exit_code = pytest.main(pytest_args)
    return exit_code == 0


if __name__ == "__main__":
    print("🧪 Запуск тестов системы обработки ошибок...")
    
    success = run_tests()
    
    if success:
        print("✅ Все тесты прошли успешно!")
    else:
        print("❌ Некоторые тесты не прошли!")
        exit(1)