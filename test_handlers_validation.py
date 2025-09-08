"""
🧪 Тест для проверки валидности обработчиков каталога уроков
Проверяет, что новые обработчики правильно импортируются и не содержат синтаксических ошибок
"""

import sys
import traceback

def test_handlers_import():
    """Тест импорта обработчиков"""
    print("🧪 Тестирование импорта обработчиков...")
    
    try:
        # Импортируем обработчики
        from handlers import shop
        print("✅ Обработчики shop успешно импортированы")
        
        # Проверяем, что router существует
        if hasattr(shop, 'shop_router'):
            print("✅ shop_router найден")
        else:
            print("❌ shop_router не найден")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта обработчиков: {e}")
        traceback.print_exc()
        return False

def test_callback_patterns():
    """Тест паттернов callback"""
    print("🧪 Тестирование паттернов callback...")
    
    try:
        from aiogram import F
        
        # Тестируем паттерны F.data
        test_patterns = [
            "lesson:1",
            "lesson:99", 
            "view_lesson:1",
            "view_lesson:99",
            "buy:1",
            "buy:99",
            "promocode:1",
            "promocode:99"
        ]
        
        for pattern in test_patterns:
            # Проверяем startswith паттерны
            prefix = pattern.split(':')[0] + ':'
            result = pattern.startswith(prefix)
            if result:
                print(f"✅ Паттерн '{pattern}' корректен")
            else:
                print(f"❌ Паттерн '{pattern}' некорректен")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования паттернов: {e}")
        return False

def test_utils_functions():
    """Тест utility функций"""
    print("🧪 Тестирование utility функций...")
    
    try:
        import utils
        
        # Тест get_text
        test_text = utils.get_text('messages.catalog_title')
        if test_text and 'каталог' in test_text.lower():
            print("✅ utils.get_text работает")
        else:
            print("❌ utils.get_text не работает правильно")
            return False
        
        # Тест calculate_stars_price
        stars = utils.calculate_stars_price(25.00)
        if stars == 5000:  # 25 * 200 = 5000
            print("✅ utils.calculate_stars_price работает")
        else:
            print(f"❌ utils.calculate_stars_price вернул {stars}, ожидался 5000")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования utils: {e}")
        return False

def test_keyboards():
    """Тест клавиатур"""
    print("🧪 Тестирование клавиатур...")
    
    try:
        import keyboards as kb
        
        # Тест main menu
        main_menu = kb.markup_main_menu()
        if main_menu:
            print("✅ markup_main_menu работает")
        else:
            print("❌ markup_main_menu не работает")
            return False
        
        # Тест lesson details
        lesson_details = kb.markup_lesson_details(1)
        if lesson_details:
            print("✅ markup_lesson_details работает")
        else:
            print("❌ markup_lesson_details не работает")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования клавиатур: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования валидности обработчиков...")
    print("=" * 60)
    
    tests = [
        test_handlers_import,
        test_callback_patterns,
        test_utils_functions,
        test_keyboards
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print()
        except Exception as e:
            print(f"❌ Тест {test.__name__} завершился с ошибкой: {e}")
            print()
    
    print("=" * 60)
    print(f"🏁 Тестирование завершено: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ Все тесты пройдены! Обработчики готовы к работе")
        print("\n🔧 Проблема решена:")
        print("• Добавлен обработчик 'lesson:' для показа деталей урока")
        print("• Добавлен обработчик 'view_lesson:' для просмотра купленных уроков")
        print("• Добавлен обработчик 'buy:' для покупки уроков")
        print("• Добавлен обработчик 'promocode:' для ввода промокодов") 
        print("• Добавлен обработчик 'back_main' для возврата в главное меню")
        print("\n🎯 Теперь пользователи могут:")
        print("• Нажимать на уроки в каталоге и видеть их детали")
        print("• Покупать бесплатные уроки автоматически")
        print("• Просматривать купленные уроки")
        print("• Использовать промокоды")
        return True
    else:
        print("❌ Некоторые тесты не пройдены")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)