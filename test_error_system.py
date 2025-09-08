"""
Простая проверка системы обработки ошибок
"""

def test_imports():
    """Тест импорта всех модулей системы обработки ошибок"""
    try:
        from errors import ErrorHandler, ErrorType, ErrorSeverity, global_error_handler
        print("✅ errors.py импортирован успешно")
        
        from message_manager import MessageManager, global_message_manager
        print("✅ message_manager.py импортирован успешно")
        
        from state_manager import SafeStateManager, safe_state_manager
        print("✅ state_manager.py импортирован успешно")
        
        from database_resilience import ResilientDatabaseManager
        print("✅ database_resilience.py импортирован успешно")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False


def test_error_classification():
    """Тест классификации ошибок"""
    try:
        from errors import ErrorHandler, ErrorType, ErrorSeverity
        from aiogram.exceptions import TelegramBadRequest
        
        handler = ErrorHandler()
        
        # Тест классификации ошибки "message is not modified"
        error = TelegramBadRequest(method="edit_message_text", message="message is not modified")
        error_type, severity = handler.classify_error(error)
        
        assert error_type == ErrorType.TELEGRAM_API
        assert severity == ErrorSeverity.LOW
        
        print("✅ Классификация ошибок работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования классификации: {e}")
        return False


def test_content_comparison():
    """Тест сравнения содержимого"""
    try:
        from errors import ContentComparator
        
        comparator = ContentComparator()
        
        # Тест сравнения текста
        assert comparator.compare_text("Hello", "Hello") is True
        assert comparator.compare_text("Hello", "World") is False
        assert comparator.compare_text(None, None) is True
        
        print("✅ Сравнение содержимого работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования сравнения: {e}")
        return False


def test_state_manager():
    """Тест менеджера состояний"""
    try:
        from state_manager import SafeStateManager
        
        manager = SafeStateManager()
        
        # Проверяем что объект создался
        assert manager is not None
        assert hasattr(manager, 'operation_counters')
        
        stats = manager.get_statistics()
        assert 'total_operations' in stats
        assert 'error_rate' in stats
        
        print("✅ Менеджер состояний работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования менеджера состояний: {e}")
        return False


def test_database_resilience():
    """Тест резилиентности базы данных"""
    try:
        from database_resilience import ResilientDatabaseManager
        from unittest.mock import Mock
        
        mock_db = Mock()
        manager = ResilientDatabaseManager(mock_db)
        
        # Проверяем что объект создался
        assert manager is not None
        assert hasattr(manager, 'health_checker')
        assert hasattr(manager, 'connection_pool')
        
        # Тест кэширования
        manager.save_to_cache("test_key", {"test": "data"})
        cached = manager.get_from_cache("test_key")
        assert cached == {"test": "data"}
        
        print("✅ Система резилиентности БД работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования резилиентности БД: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🧪 Запуск проверки системы обработки ошибок...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_error_classification,
        test_content_comparison,
        test_state_manager,
        test_database_resilience
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Тест {test.__name__} не прошел")
        except Exception as e:
            print(f"❌ Исключение в тесте {test.__name__}: {e}")
    
    print("=" * 50)
    print(f"📊 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все тесты прошли! Система обработки ошибок готова к использованию.")
        return True
    else:
        print("⚠️ Некоторые тесты не прошли. Требуется дополнительная проверка.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)