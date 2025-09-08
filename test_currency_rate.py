import sys
sys.stdout.reconfigure(encoding='utf-8')
"""
Тест для проверки обновления курса валют
"""
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch

# Добавляем текущую директорию в sys.path
sys.path.append('.')

async def test_currency_rate_update():
    """Тест обновления курса валют"""
    print("🧪 Тестирование обновления курса валют...")
    
    try:
        with patch('handlers.admin.s') as mock_system_settings, \
             patch('handlers.admin.utils') as mock_utils, \
             patch('handlers.admin.kb') as mock_kb:
            
            # Настройка моков
            mock_system_settings.set_usd_to_stars_rate = AsyncMock()
            mock_utils.get_text = Mock(return_value="✅ Курс валют обновлен!")
            mock_kb.markup_remove = Mock(return_value=Mock())
            mock_kb.markup_admin_settings = Mock(return_value=Mock())
            mock_kb.markup_cancel = Mock(return_value=Mock())
            
            from handlers.admin import update_currency_rate
            from states import FSMSettings
            
            # Создание мока message
            message = Mock()
            message.text = "77"
            message.answer = AsyncMock()
            
            # Создание мока state
            state = Mock()
            state.clear = AsyncMock()
            
            # Тестируем успешное обновление
            await update_currency_rate(message, state)
            
            # Проверки
            mock_system_settings.set_usd_to_stars_rate.assert_called_once_with(77)
            assert message.answer.call_count == 2  # 2 сообщения должны быть отправлены
            state.clear.assert_called_once()
            
            print("✅ Курс валют успешно обновлен")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании обновления курса: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_currency_rate_validation():
    """Тест валидации курса валют"""
    print("🧪 Тестирование валидации курса валют...")
    
    try:
        with patch('handlers.admin.s') as mock_system_settings, \
             patch('handlers.admin.kb') as mock_kb:
            
            mock_kb.markup_cancel = Mock(return_value=Mock())
            
            from handlers.admin import update_currency_rate
            
            # Тестируем неверное значение
            message = Mock()
            message.text = "abc"  # Неверное значение
            message.answer = AsyncMock()
            
            state = Mock()
            state.clear = AsyncMock()
            
            await update_currency_rate(message, state)
            
            # Должно быть отправлено сообщение об ошибке
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "корректное число" in call_args
            
            print("✅ Валидация курса валют работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании валидации: {e}")
        return False

async def test_currency_rate_zero_validation():
    """Тест валидации нулевого и отрицательного курса"""
    print("🧪 Тестирование валидации нулевого курса...")
    
    try:
        with patch('handlers.admin.kb') as mock_kb:
            
            mock_kb.markup_cancel = Mock(return_value=Mock())
            
            from handlers.admin import update_currency_rate
            
            # Тестируем нулевое значение
            message = Mock()
            message.text = "0"  # Неверное значение (должно быть > 0)
            message.answer = AsyncMock()
            
            state = Mock()
            state.clear = AsyncMock()
            
            await update_currency_rate(message, state)
            
            # Должно быть отправлено сообщение об ошибке
            message.answer.assert_called_once()
            call_args = message.answer.call_args[0][0]
            assert "больше 0" in call_args
            
            print("✅ Валидация нулевого курса работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании валидации нуля: {e}")
        return False

async def test_stars_calculation():
    """Тест расчёта цены в звёздах"""
    print("🧪 Тестирование расчёта цены в звёздах...")
    
    try:
        from utils import calculate_stars_price
        from database.lesson import SystemSettings
        import unittest.mock as mock
        
        # Mock SystemSettings для возврата курса 77
        with mock.patch.object(SystemSettings, 'get_usd_to_stars_rate', return_value=77):
            s = SystemSettings()
            
            # Тестируем для $25
            stars = await calculate_stars_price(25)
            assert stars == 1925, f"Ожидалось 1925, получено {stars}"
            
            # Тестируем для $0 (минимум 1)
            stars_min = await calculate_stars_price(0)
            assert stars_min == 1
            
            print("✅ Расчёт цены в звёздах работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка в тесте расчёта: {e}")
        return False

# Добавляем тест в список
tests = [
    test_currency_rate_update,
    test_currency_rate_validation,
    test_currency_rate_zero_validation,
    test_stars_calculation
]
async def run_currency_tests():
    """Запуск всех тестов курса валют"""
    print("🚀 Тестирование системы курса валют...")
    print("=" * 50)
    
    tests = [
        test_currency_rate_update,
        test_currency_rate_validation,
        test_currency_rate_zero_validation,
        test_stars_calculation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
            print()
    
    print("=" * 50)
    print(f"Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Система курса валют работает корректно!")
        print("\n🔧 Исправления:")
        print("• Исправлена аннотация типа состояния (FSMSettings -> FSMContext)")
        print("• Добавлена корректная валидация входных данных")
        print("• Улучшена обработка ошибок")
        print("\n🎯 Теперь администраторы могут:")
        print("• Изменять курс USD к Stars")
        print("• Получать корректные сообщения об ошибках")
        print("• Видеть подтверждение изменений")
        return True
    else:
        print("❌ Обнаружены проблемы в системе курса валют")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_currency_tests())
    sys.exit(0 if success else 1)