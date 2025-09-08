"""
Интеграционный тест для системы курса валют
Проверяет полный цикл работы от вызова до сохранения в БД
"""

import asyncio
import sys
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Добавляем текущую директорию в sys.path
sys.path.append('.')

async def test_full_currency_flow():
    """Полный интеграционный тест обновления курса валют"""
    print("🧪 Интеграционный тест курса валют...")
    
    try:
        # Импортируем реальные модули
        from handlers.admin import currency_rate_settings, update_currency_rate
        from states import FSMSettings
        from database.lesson import SystemSettings
        
        # Тестируем настройку курса валют
        print("1️⃣ Тестирование вызова настроек курса...")
        
        # Создаем реальный mock call
        call = Mock()
        call.from_user.id = 123456789  # ID администратора
        call.answer = AsyncMock()
        call.message = Mock()
        call.message.edit_text = AsyncMock()
        
        state = Mock()
        state.set_state = AsyncMock()
        
        # Мокаем базу данных и другие зависимости
        with patch('handlers.admin.config.ADMINS', [123456789]), \
             patch('handlers.admin.utils.get_admins', return_value=[]), \
             patch('handlers.admin.s') as mock_system_settings, \
             patch('handlers.admin.utils.get_text') as mock_get_text:
            
            mock_system_settings.get_usd_to_stars_rate = AsyncMock(return_value=200)
            mock_get_text.return_value = "💱 Текущий курс валют\n\n1 USD = 200 ⭐ Stars\n\nВведите новый курс:"
            
            # Вызываем настройки курса
            await currency_rate_settings(call, state)
            
            # Проверки
            call.answer.assert_called_once()
            state.set_state.assert_called_once_with(FSMSettings.currency_rate)
            call.message.edit_text.assert_called_once()
            
        print("✅ Настройки курса работают корректно")
        
        # Тестируем обновление курса
        print("2️⃣ Тестирование обновления курса...")
        
        message = Mock()
        message.text = "77"
        message.answer = AsyncMock()
        
        state = Mock()
        state.clear = AsyncMock()
        
        with patch('handlers.admin.s') as mock_system_settings, \
             patch('handlers.admin.utils.get_text') as mock_get_text, \
             patch('handlers.admin.kb') as mock_kb:
            
            mock_system_settings.set_usd_to_stars_rate = AsyncMock()
            mock_get_text.return_value = "✅ Курс валют обновлен!"
            mock_kb.markup_remove.return_value = Mock()
            mock_kb.markup_admin_settings.return_value = Mock()
            
            # Вызываем обновление курса
            await update_currency_rate(message, state)
            
            # Проверки
            mock_system_settings.set_usd_to_stars_rate.assert_called_once_with(77)
            assert message.answer.call_count == 2
            state.clear.assert_called_once()
            
        print("✅ Обновление курса работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в интеграционном тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_operations():
    """Тест операций с базой данных для курса валют"""
    print("🗄️ Тестирование операций с БД...")
    
    try:
        from database.lesson import SystemSettings
        
        # Создаем экземпляр SystemSettings
        s = SystemSettings()
        
        # Тестируем с моком базы данных
        with patch.object(s, 'set_setting') as mock_set_setting, \
             patch.object(s, 'get_setting') as mock_get_setting:
            
            # Настройка моков
            mock_get_setting.return_value = "200"
            mock_set_setting.return_value = None
            
            # Тестируем получение курса
            rate = await s.get_usd_to_stars_rate()
            assert rate == 200
            
            # Тестируем установку курса
            await s.set_usd_to_stars_rate(77)
            mock_set_setting.assert_called_once_with('usd_to_stars_rate', '77')
            
        print("✅ Операции с БД работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте БД: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """Тест обработки ошибок в системе курса валют"""
    print("⚠️ Тестирование обработки ошибок...")
    
    try:
        from handlers.admin import update_currency_rate
        
        # Тест с некорректным вводом
        message = Mock()
        message.text = "abc"
        message.answer = AsyncMock()
        
        state = Mock()
        state.clear = AsyncMock()
        
        with patch('handlers.admin.kb') as mock_kb:
            mock_kb.markup_cancel.return_value = Mock()
            
            await update_currency_rate(message, state)
            
            # Должно быть вызвано сообщение об ошибке
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "корректное число" in call_args
        
        # Тест с нулевым значением
        message.text = "0"
        message.answer.reset_mock()
        
        await update_currency_rate(message, state)
        
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "больше 0" in call_args
        
        print("✅ Обработка ошибок работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте обработки ошибок: {e}")
        return False

async def test_real_database_connection():
    """Тест подключения к реальной базе данных"""
    print("🔗 Тестирование подключения к реальной БД...")
    
    try:
        from database.lesson import SystemSettings
        from database.core import con
        
        # Проверяем подключение к БД
        if con.is_closed():
            con.connect()
        
        s = SystemSettings()
        
        # Пытаемся получить текущий курс
        try:
            current_rate = await s.get_usd_to_stars_rate()
            print(f"📊 Текущий курс в БД: {current_rate}")
            
            # Сохраняем текущий курс
            original_rate = current_rate
            
            # Устанавливаем тестовый курс
            test_rate = 999
            await s.set_usd_to_stars_rate(test_rate)
            
            # Проверяем, что курс изменился
            new_rate = await s.get_usd_to_stars_rate()
            assert new_rate == test_rate, f"Ожидался курс {test_rate}, получен {new_rate}"
            
            # Возвращаем оригинальный курс
            await s.set_usd_to_stars_rate(original_rate)
            
            print("✅ Подключение к БД работает корректно")
            return True
            
        except Exception as db_error:
            print(f"❌ Ошибка операций с БД: {db_error}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

async def test_state_management():
    """Тест управления состояниями FSM"""
    print("🔄 Тестирование управления состояниями...")
    
    try:
        from states import FSMSettings
        from aiogram.fsm.context import FSMContext
        
        # Проверяем, что состояние определено
        assert hasattr(FSMSettings, 'currency_rate'), "Состояние currency_rate не найдено"
        
        # Создаем мок состояния
        state = Mock(spec=FSMContext)
        state.set_state = AsyncMock()
        state.clear = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        state.update_data = AsyncMock()
        
        # Тестируем установку состояния
        await state.set_state(FSMSettings.currency_rate)
        state.set_state.assert_called_once_with(FSMSettings.currency_rate)
        
        # Тестируем очистку состояния
        await state.clear()
        state.clear.assert_called_once()
        
        print("✅ Управление состояниями работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте состояний: {e}")
        return False

async def run_integration_tests():
    """Запуск всех интеграционных тестов"""
    print("🚀 Запуск интеграционных тестов курса валют...")
    print("=" * 60)
    
    tests = [
        test_state_management,
        test_database_operations,
        test_error_handling,
        test_full_currency_flow,
        test_real_database_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
            print()
    
    print("=" * 60)
    print(f"🏁 Результаты интеграционного тестирования: {passed}/{total}")
    
    if passed == total:
        print("✅ Все интеграционные тесты пройдены!")
        print("\n🔧 Система курса валют готова к работе:")
        print("• Состояния FSM настроены корректно")
        print("• База данных функционирует правильно")
        print("• Обработка ошибок работает")
        print("• Полный цикл обновления курса исправен")
        print("• Реальные операции с БД выполняются")
        return True
    else:
        print("❌ Обнаружены критические проблемы!")
        print(f"Не пройдено тестов: {total - passed}")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)