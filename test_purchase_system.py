"""
Тест покупки уроков
"""
import asyncio
from unittest.mock import Mock, AsyncMock, patch

async def test_buy_lesson_free():
    """Тест покупки бесплатного урока"""
    print("🧪 Тестирование покупки бесплатного урока...")
    
    with patch('handlers.shop.l') as mock_lesson, \
         patch('handlers.shop.p') as mock_purchase, \
         patch('handlers.shop.global_message_manager') as mock_msg:
        
        # Настройка мокков
        mock_lesson.get_lesson = AsyncMock(return_value=Mock(
            id=1, title="Бесплатный урок", is_free=True, price_usd=0.0
        ))
        mock_purchase.check_user_has_lesson = AsyncMock(return_value=False)
        mock_purchase.create_purchase = AsyncMock()
        mock_lesson.increment_purchases = AsyncMock()
        mock_msg.edit_message_safe = AsyncMock()
        
        from handlers.shop import buy_lesson
        
        # Создание мока call
        call = Mock()
        call.data = "buy:1"
        call.answer = AsyncMock()
        call.from_user.id = 123
        call.message = Mock()
        
        state = Mock()
        
        await buy_lesson(call, state)
        
        # Проверки
        mock_purchase.create_purchase.assert_called_once()
        print("✅ Бесплатный урок успешно куплен")
        return True

async def test_buy_lesson_paid():
    """Тест попытки покупки платного урока"""  
    print("🧪 Тестирование попытки покупки платного урока...")
    
    with patch('handlers.shop.l') as mock_lesson, \
         patch('handlers.shop.p') as mock_purchase, \
         patch('handlers.shop.global_message_manager') as mock_msg:
        
        mock_lesson.get_lesson = AsyncMock(return_value=Mock(
            id=2, title="Платный урок", is_free=False, price_usd=25.0
        ))
        mock_purchase.check_user_has_lesson = AsyncMock(return_value=False)
        mock_msg.edit_message_safe = AsyncMock()
        
        from handlers.shop import buy_lesson
        
        call = Mock()
        call.data = "buy:2"
        call.answer = AsyncMock()
        call.from_user.id = 123
        call.message = Mock()
        
        state = Mock()
        
        await buy_lesson(call, state)
        
        # Должно показать сообщение о недоступности оплаты
        mock_msg.edit_message_safe.assert_called_once()
        print("✅ Показано сообщение о недоступности оплаты")
        return True

async def run_purchase_tests():
    """Запуск всех тестов покупки"""
    print("🚀 Тестирование системы покупок...")
    print("=" * 50)
    
    tests = [test_buy_lesson_free, test_buy_lesson_paid]
    passed = 0
    
    for test in tests:
        try:
            if await test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
    
    print("=" * 50)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("✅ Система покупок работает корректно!")
        return True
    else:
        print("❌ Обнаружены проблемы в системе покупок")
        return False

if __name__ == '__main__':
    import sys
    sys.path.append('.')
    success = asyncio.run(run_purchase_tests())