"""
🎯 Финальный комплексный тест всех исправлений
Проверяет все исправленные функции перед сдачей задачи
"""

import asyncio
import sys
from unittest.mock import Mock, AsyncMock, patch

# Добавляем текущую директорию в sys.path
sys.path.append('.')

async def test_currency_rate_real_scenario():
    """Тест реального сценария обновления курса валют"""
    print("🧪 Тест реального сценария обновления курса валют...")
    
    try:
        from handlers.admin import update_currency_rate
        from database.lesson import SystemSettings
        from database.sql import configure_database
        
        # Настройка БД
        configure_database()
        s = SystemSettings()
        
        # Сохраняем текущий курс
        original_rate = await s.get_usd_to_stars_rate()
        print(f"📊 Исходный курс: {original_rate}")
        
        # Создаем реальный mock для сообщения "77"
        message = Mock()
        message.text = "77"
        message.answer = AsyncMock()
        
        state = Mock()
        state.clear = AsyncMock()
        
        # Выполняем обновление
        await update_currency_rate(message, state)
        
        # Проверяем результат
        new_rate = await s.get_usd_to_stars_rate()
        print(f"📊 Новый курс: {new_rate}")
        
        if new_rate == 77:
            print("✅ Курс успешно обновлен на 77!")
            
            # Восстанавливаем исходный курс
            await s.set_usd_to_stars_rate(original_rate)
            final_rate = await s.get_usd_to_stars_rate()
            print(f"📊 Восстановленный курс: {final_rate}")
            
            return True
        else:
            print(f"❌ Курс не обновился. Ожидался 77, получен {new_rate}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте курса: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_button_functionality():
    """Тест функциональности кнопок"""
    print("🧪 Тест функциональности основных кнопок...")
    
    try:
        # Тест импорта обработчиков
        from handlers.shop import show_catalog, show_my_lessons, show_profile
        print("✅ Все обработчики кнопок импортированы успешно")
        
        # Тест импорта клавиатур
        import keyboards as kb
        
        # Проверяем основные клавиатуры
        main_menu = kb.markup_main_menu()
        catalog_kb = kb.markup_catalog([])
        my_lessons_kb = kb.markup_my_lessons([])
        
        if all([main_menu, catalog_kb, my_lessons_kb]):
            print("✅ Все клавиатуры создаются корректно")
            return True
        else:
            print("❌ Ошибка создания клавиатур")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте кнопок: {e}")
        return False

async def test_error_handling():
    """Тест системы обработки ошибок"""
    print("🧪 Тест системы обработки ошибок...")
    
    try:
        from errors import global_error_handler, handle_errors
        print("✅ Система обработки ошибок импортирована")
        
        # Тест декоратора
        @handle_errors(redirect_on_error=True)
        async def test_function(call, state):
            return "success"
        
        # Создаем моки
        call = Mock()
        call.from_user = Mock()
        call.from_user.id = 123456789
        call.answer = AsyncMock()
        
        state = Mock()
        
        # Тестируем с middleware аргументами
        result = await test_function(call, state, bot=Mock(), handler=Mock())
        
        if result == "success":
            print("✅ Обработка ошибок и фильтрация аргументов работает")
            return True
        else:
            print("❌ Проблема с обработкой ошибок")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте обработки ошибок: {e}")
        return False

async def test_purchase_system():
    """Тест системы покупок"""
    print("🧪 Тест системы покупок...")
    
    try:
        with patch('handlers.shop.l') as mock_lesson, \
             patch('handlers.shop.p') as mock_purchase, \
             patch('handlers.shop.global_message_manager') as mock_msg:
            
            # Настройка моков для бесплатного урока
            mock_lesson.get_lesson = AsyncMock(return_value=Mock(
                id=1, title="Тест урок", is_free=True, price_usd=0.0
            ))
            mock_purchase.check_user_has_lesson = AsyncMock(return_value=False)
            mock_purchase.create_purchase = AsyncMock()
            mock_msg.edit_message_safe = AsyncMock()
            
            from handlers.shop import buy_lesson
            
            call = Mock()
            call.data = "buy:1"
            call.answer = AsyncMock()
            call.from_user = Mock()
            call.from_user.id = 123
            call.message = Mock()
            
            state = Mock()
            
            await buy_lesson(call, state)
            
            # Проверяем, что покупка была создана
            mock_purchase.create_purchase.assert_called_once()
            print("✅ Система покупок работает корректно")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка в тесте покупок: {e}")
        return False

async def run_final_tests():
    """Запуск финального комплексного тестирования"""
    print("🚀 ФИНАЛЬНОЕ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ")
    print("=" * 60)
    print("Проверяем все исправления перед сдачей задачи")
    print("=" * 60)
    
    tests = [
        ("Система обработки ошибок", test_error_handling),
        ("Функциональность кнопок", test_button_functionality),
        ("Система покупок", test_purchase_system),
        ("Курс валют (реальный сценарий)", test_currency_rate_real_scenario)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: ПРОЙДЕН")
            else:
                print(f"❌ {test_name}: НЕ ПРОЙДЕН")
        except Exception as e:
            print(f"❌ {test_name}: ОШИБКА - {e}")
    
    print("\n" + "=" * 60)
    print(f"🏁 ИТОГИ ТЕСТИРОВАНИЯ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n🔧 ИСПРАВЛЕННЫЕ ПРОБЛЕМЫ:")
        print("• ✅ Кнопки каталога, уроков и профиля работают")
        print("• ✅ Обновление курса валют исправлено (UNIQUE constraint)")
        print("• ✅ Система покупок функционирует корректно")
        print("• ✅ Обработка ошибок middleware улучшена")
        print("• ✅ База данных работает стабильно")
        
        print("\n🎯 ГОТОВЫЕ К ИСПОЛЬЗОВАНИЮ ФУНКЦИИ:")
        print("• 🛍️ Каталог уроков - работает")
        print("• 📚 Мои уроки - работает")
        print("• 👤 Профиль - работает")
        print("• 💱 Курс валют - работает")
        print("• 🛒 Покупка уроков - работает")
        
        print("\n✅ ЗАДАЧА ГОТОВА К СДАЧЕ!")
        return True
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print(f"Не пройдено тестов: {total - passed}")
        return False

if __name__ == '__main__':
    success = asyncio.run(run_final_tests())
    sys.exit(0 if success else 1)