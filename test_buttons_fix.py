"""
Тест для проверки исправления кнопок каталога, моих уроков и профиля
"""

import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext

# Добавляем текущую директорию в sys.path
sys.path.append('.')

def create_mock_callback_query(data: str, user_id: int = 123456789):
    """Создать mock объект CallbackQuery"""
    call = Mock(spec=types.CallbackQuery)
    call.data = data
    call.answer = AsyncMock()
    
    # Mock пользователя
    call.from_user = Mock()
    call.from_user.id = user_id
    call.from_user.full_name = "Тест Пользователь"
    
    # Mock сообщения
    call.message = Mock()
    call.message.message_id = 123
    call.message.chat = Mock()
    call.message.chat.id = user_id
    
    return call

def create_mock_state():
    """Создать mock объект FSMContext"""
    state = Mock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.clear = AsyncMock()
    return state

async def test_error_decorator_filtering():
    """Тест фильтрации аргументов в декораторе handle_errors"""
    print("🧪 Тестирование фильтрации аргументов в декораторе...")
    
    try:
        from errors import handle_errors
        import keyboards as kb
        
        # Создаем тестовую функцию с декоратором
        @handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
        async def test_handler(call: types.CallbackQuery, state: FSMContext):
            return "success"
        
        # Создаем mock объекты
        call = create_mock_callback_query("test")
        state = create_mock_state()
        
        # Тестируем с различными middleware аргументами
        middleware_args = {
            'dispatcher': Mock(),
            'bot': Mock(),
            'bots': Mock(),
            'fsm_storage': Mock(),
            'event_context': Mock(),
            'event_from_user': Mock(),
            'event_chat': Mock(),
            'raw_updates': Mock(),
            'handler': Mock()  # Добавлен новый аргумент
        }
        
        # Вызываем функцию с middleware аргументами
        result = await test_handler(call, state, **middleware_args)
        
        if result == "success":
            print("✅ Фильтрация middleware аргументов работает корректно")
            return True
        else:
            print("❌ Фильтрация middleware аргументов не работает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании фильтрации: {e}")
        return False

async def test_catalog_function():
    """Тест функции показа каталога"""
    print("🧪 Тестирование функции show_catalog...")
    
    try:
        # Патчим все зависимости
        with patch('handlers.shop.safe_state_manager') as mock_state_manager, \
             patch('handlers.shop.resilient_db_operation') as mock_db_op, \
             patch('handlers.shop.global_message_manager') as mock_msg_manager, \
             patch('handlers.shop.l') as mock_lesson, \
             patch('handlers.shop.utils') as mock_utils, \
             patch('handlers.shop.kb') as mock_kb:
            
            # Настраиваем моки
            mock_state_manager.safe_clear_state = AsyncMock()
            mock_msg_manager.edit_message_safe = AsyncMock()
            mock_utils.get_text = Mock(return_value="🛍️ Каталог уроков")
            mock_kb.markup_catalog = Mock(return_value=Mock())
            mock_kb.markup_main_menu = Mock(return_value=Mock())
            
            # Мокаем получение уроков
            mock_lessons = [
                {'id': 1, 'title': 'Урок 1', 'price_usd': 25.0, 'is_free': False},
                {'id': 2, 'title': 'Урок 2', 'price_usd': 0.0, 'is_free': True}
            ]
            
            def mock_decorator(operation_name=None, use_cache=False, cache_key=None):
                def decorator(func):
                    async def wrapper():
                        return mock_lessons
                    return wrapper
                return decorator
            
            mock_db_op.side_effect = mock_decorator
            
            # Импортируем и тестируем функцию
            from handlers.shop import show_catalog
            
            call = create_mock_callback_query("catalog")
            state = create_mock_state()
            
            # Вызываем функцию
            await show_catalog(call, state)
            
            # Проверяем вызовы
            call.answer.assert_called_once()
            mock_state_manager.safe_clear_state.assert_called_once()
            mock_msg_manager.edit_message_safe.assert_called_once()
            
            print("✅ Функция show_catalog работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании show_catalog: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_my_lessons_function():
    """Тест функции показа моих уроков"""
    print("🧪 Тестирование функции show_my_lessons...")
    
    try:
        with patch('handlers.shop.safe_state_manager') as mock_state_manager, \
             patch('handlers.shop.resilient_db_operation') as mock_db_op, \
             patch('handlers.shop.global_message_manager') as mock_msg_manager, \
             patch('handlers.shop.p') as mock_purchase, \
             patch('handlers.shop.utils') as mock_utils, \
             patch('handlers.shop.kb') as mock_kb:
            
            # Настраиваем моки
            mock_state_manager.safe_clear_state = AsyncMock()
            mock_msg_manager.edit_message_safe = AsyncMock()
            mock_utils.get_text = Mock(return_value="📚 Ваши уроки")
            mock_kb.markup_my_lessons = Mock(return_value=Mock())
            mock_kb.markup_main_menu = Mock(return_value=Mock())
            
            # Мокаем покупки пользователя
            mock_purchases = [
                {'lesson_id': 1, 'title': 'Купленный урок 1'},
                {'lesson_id': 2, 'title': 'Купленный урок 2'}
            ]
            
            def mock_decorator(operation_name=None, use_cache=False, cache_key=None):
                def decorator(func):
                    async def wrapper():
                        return mock_purchases
                    return wrapper
                return decorator
            
            mock_db_op.side_effect = mock_decorator
            
            from handlers.shop import show_my_lessons
            
            call = create_mock_callback_query("my_lessons")
            state = create_mock_state()
            
            await show_my_lessons(call, state)
            
            # Проверяем вызовы
            call.answer.assert_called_once()
            mock_state_manager.safe_clear_state.assert_called_once()
            mock_msg_manager.edit_message_safe.assert_called_once()
            
            print("✅ Функция show_my_lessons работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании show_my_lessons: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_profile_function():
    """Тест функции показа профиля"""
    print("🧪 Тестирование функции show_profile...")
    
    try:
        with patch('handlers.shop.safe_state_manager') as mock_state_manager, \
             patch('handlers.shop.resilient_db_operation') as mock_db_op, \
             patch('handlers.shop.global_message_manager') as mock_msg_manager, \
             patch('handlers.shop.p') as mock_purchase, \
             patch('handlers.shop.utils') as mock_utils, \
             patch('handlers.shop.kb') as mock_kb:
            
            # Настраиваем моки
            mock_state_manager.safe_clear_state = AsyncMock()
            mock_msg_manager.edit_message_safe = AsyncMock()
            mock_utils.get_text = Mock(return_value="👤 Ваш профиль")
            mock_kb.markup_main_menu = Mock(return_value=Mock())
            
            # Мокаем количество уроков пользователя
            def mock_decorator(operation_name=None, use_cache=False, cache_key=None):
                def decorator(func):
                    async def wrapper():
                        return 3  # 3 урока
                    return wrapper
                return decorator
            
            mock_db_op.side_effect = mock_decorator
            
            from handlers.shop import show_profile
            
            call = create_mock_callback_query("profile")
            state = create_mock_state()
            
            await show_profile(call, state)
            
            # Проверяем вызовы
            call.answer.assert_called_once()
            mock_state_manager.safe_clear_state.assert_called_once()
            mock_msg_manager.edit_message_safe.assert_called_once()
            
            print("✅ Функция show_profile работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании show_profile: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_keyboard_functions():
    """Тест функций клавиатур"""
    print("🧪 Тестирование функций клавиатур...")
    
    try:
        import keyboards as kb
        
        # Тест главного меню
        main_menu = kb.markup_main_menu()
        if main_menu and hasattr(main_menu, 'inline_keyboard'):
            print("✅ markup_main_menu() работает")
        else:
            print("❌ markup_main_menu() не работает")
            return False
        
        # Тест каталога
        mock_lessons = [
            {'id': 1, 'title': 'Урок 1', 'price_usd': 25.0, 'is_free': False}
        ]
        catalog_keyboard = kb.markup_catalog(mock_lessons)
        if catalog_keyboard and hasattr(catalog_keyboard, 'inline_keyboard'):
            print("✅ markup_catalog() работает")
        else:
            print("❌ markup_catalog() не работает")
            return False
        
        # Тест моих уроков
        mock_my_lessons = [
            {'id': 1, 'title': 'Мой урок 1'}
        ]
        my_lessons_keyboard = kb.markup_my_lessons(mock_my_lessons)
        if my_lessons_keyboard and hasattr(my_lessons_keyboard, 'inline_keyboard'):
            print("✅ markup_my_lessons() работает")
        else:
            print("❌ markup_my_lessons() не работает")
            return False
        
        print("✅ Все функции клавиатур работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании клавиатур: {e}")
        return False

async def run_all_tests():
    """Запустить все тесты"""
    print("🚀 Запуск тестов исправления кнопок...")
    print("=" * 60)
    
    tests = [
        test_error_decorator_filtering,
        test_keyboard_functions,
        test_catalog_function,
        test_my_lessons_function,
        test_profile_function
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с ошибкой: {e}")
            print()
    
    print("=" * 60)
    print(f"🏁 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Все тесты пройдены! Кнопки должны работать корректно")
        print("\n🔧 Исправления:")
        print("• Улучшена фильтрация middleware аргументов")
        print("• Добавлена поддержка fsm_storage и других аргументов")
        print("• Проверены все основные функции кнопок")
        print("\n🎯 Кнопки готовы к использованию:")
        print("• 🛍️ Каталог уроков")
        print("• 📚 Мои уроки")
        print("• 👤 Профиль")
        print("• 🔙 Назад")
        return True
    else:
        print("❌ Некоторые тесты не пройдены")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)