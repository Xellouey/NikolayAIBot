#!/usr/bin/env python3
"""
Тест исправления ошибки дублирования сообщений в системе поддержки.

Проверяет, что функции show_tickets_by_status и admin_support_dashboard
корректно обрабатывают попытки редактирования сообщений с идентичным содержимым.
"""

import sys
import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from aiogram import types
from aiogram.fsm.context import FSMContext

# Патчим модули перед импортом
sys.modules['config'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['keyboards'] = MagicMock()
sys.modules['database.support'] = MagicMock()
sys.modules['database.user'] = MagicMock()
sys.modules['states'] = MagicMock()
sys.modules['aiogram.fsm.context'] = MagicMock()
sys.modules['aiogram'] = MagicMock()

# Настраиваем патчи
import config
config.ADMINS = [123456789]
config.TOKEN = "123456789:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRRSSTTuuvvwwxxyyzz"  # Valid token format

import utils
utils.get_admins = MagicMock(return_value=[])
utils.get_text = MagicMock(return_value="Test text")

import keyboards as kb
kb.markup_admin_support_dashboard = MagicMock(return_value=MagicMock())
kb.markup_admin_tickets_list = MagicMock(return_value=MagicMock())

from database.support import SupportTicket
from database.user import User

# Патчим Bot класс
with patch('aiogram.Bot'):
    with patch('handlers.support.Bot'):
        # Теперь можно безопасно импортировать


def create_mock_callback_query(data, user_id=123456789):
    """Создает мок callback query"""
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.full_name = "Test User"
    
    mock_message = MagicMock()
    mock_message.edit_text = AsyncMock()
    
    mock_call = MagicMock()
    mock_call.data = data
    mock_call.from_user = mock_user
    mock_call.message = mock_message
    mock_call.answer = AsyncMock()
    
    return mock_call


def create_mock_state():
    """Создает мок FSMContext"""
    mock_state = MagicMock()
    mock_state.get_state = AsyncMock(return_value=None)
    mock_state.set_state = AsyncMock()
    mock_state.update_data = AsyncMock()
    mock_state.clear = AsyncMock()
    mock_state.get_data = AsyncMock(return_value={})
    return mock_state


class TestSupportMessageFix(unittest.TestCase):
    """Тесты исправления ошибки дублирования сообщений"""
    
    def setUp(self):
        """Настройка тестов"""
        # Создаем моки
        self.support_ticket_mock = MagicMock()
        self.user_model_mock = MagicMock()
        
        # Патчим модули
        self.patcher_support = patch('handlers.support.support_ticket', self.support_ticket_mock)
        self.patcher_user = patch('handlers.support.user_model', self.user_model_mock)
        
        self.patcher_support.start()
        self.patcher_user.start()
    
    def tearDown(self):
        """Очистка после тестов"""
        self.patcher_support.stop()
        self.patcher_user.stop()
    
    async def test_show_tickets_by_status_no_tickets_open(self):
        """Тест отображения пустого списка открытых тикетов"""
        print("🧪 Тестирование show_tickets_by_status с пустым списком открытых тикетов...")
        
        try:
            # Настраиваем моки
            self.support_ticket_mock.get_all_tickets = AsyncMock(return_value=[])
            
            from handlers.support import show_tickets_by_status
            
            call = create_mock_callback_query("tickets_open")
            state = create_mock_state()
            
            # Вызываем функцию
            await show_tickets_by_status(call, state)
            
            # Проверяем, что функция была вызвана без ошибок
            call.answer.assert_called_once()
            call.message.edit_text.assert_called_once()
            
            # Проверяем, что текст содержит информацию о статусе
            args = call.message.edit_text.call_args[0]
            self.assertIn("🟢 Открытые", args[0])
            self.assertIn("не найдено", args[0])
            
            print("✅ Тест show_tickets_by_status с пустым списком открытых тикетов прошел успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте show_tickets_by_status: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_show_tickets_by_status_message_not_modified_error(self):
        """Тест обработки ошибки 'message is not modified'"""
        print("🧪 Тестирование обработки ошибки 'message is not modified'...")
        
        try:
            # Настраиваем моки
            self.support_ticket_mock.get_all_tickets = AsyncMock(return_value=[])
            
            from handlers.support import show_tickets_by_status
            
            call = create_mock_callback_query("tickets_open")
            state = create_mock_state()
            
            # Настраиваем мок для генерации ошибки "message is not modified"
            call.message.edit_text.side_effect = Exception("message is not modified: specified new message content and reply markup are exactly the same")
            
            # Вызываем функцию
            await show_tickets_by_status(call, state)
            
            # Проверяем, что call.answer был вызван дважды (один раз в начале, один раз при ошибке)
            self.assertEqual(call.answer.call_count, 2)
            
            # Проверяем, что второй вызов содержит сообщение об уже показанных тикетах
            second_call_args = call.answer.call_args_list[1][0]
            self.assertIn("Уже показаны тикеты", second_call_args[0])
            
            print("✅ Тест обработки ошибки 'message is not modified' прошел успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте обработки ошибки: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_admin_support_dashboard(self):
        """Тест панели администратора поддержки"""
        print("🧪 Тестирование admin_support_dashboard...")
        
        try:
            # Настраиваем моки
            mock_counts = {
                'total': 10,
                'open': 3,
                'in_progress': 2,
                'closed': 5
            }
            self.support_ticket_mock.get_tickets_count_by_status = AsyncMock(return_value=mock_counts)
            
            from handlers.support import admin_support_dashboard
            
            call = create_mock_callback_query("admin_support")
            state = create_mock_state()
            
            # Вызываем функцию
            await admin_support_dashboard(call, state)
            
            # Проверяем, что функция была вызвана без ошибок
            call.answer.assert_called_once()
            call.message.edit_text.assert_called_once()
            
            print("✅ Тест admin_support_dashboard прошел успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в тесте admin_support_dashboard: {e}")
            import traceback
            traceback.print_exc()
            return False


async def run_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск тестов исправления системы поддержки...")
    
    test_instance = TestSupportMessageFix()
    test_instance.setUp()
    
    tests = [
        test_instance.test_show_tickets_by_status_no_tickets_open,
        test_instance.test_show_tickets_by_status_message_not_modified_error,
        test_instance.test_admin_support_dashboard
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Ошибка в тесте {test.__name__}: {e}")
            failed += 1
    
    test_instance.tearDown()
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Прошли: {passed}")
    print(f"❌ Не прошли: {failed}")
    print(f"📈 Всего: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 Все тесты прошли успешно! Исправление работает корректно.")
        return True
    else:
        print(f"\n⚠️ {failed} тестов не прошли. Требуется дополнительная проверка.")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_tests())
        if result:
            print("\n✅ Система поддержки исправлена и готова к использованию!")
        else:
            print("\n❌ Обнаружены проблемы в системе поддержки.")
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()