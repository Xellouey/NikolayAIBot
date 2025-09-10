#!/usr/bin/env python
"""
Полный набор юнит-тестов для системы рассылок
"""
import unittest
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from localization import get_text, Localization
from keyboards import markup_custom
from database.mail import Mail
import config


class TestLocalization(unittest.TestCase):
    """Тесты локализации"""
    
    def test_mail_help_text_exists(self):
        """Проверка что текст справки существует и не возвращает ключ"""
        text = get_text('mail.messages.mail_help', 'ru')
        self.assertNotEqual(text, 'mail.messages.mail_help')
        self.assertIn('inline', text.lower())
        self.assertIn('JSON', text)
    
    def test_button_texts_exist(self):
        """Проверка что тексты кнопок существуют"""
        buttons = [
            'mail.buttons.copy_json',
            'mail.buttons.copy_inline', 
            'mail.buttons.copy_callback'
        ]
        for key in buttons:
            text = get_text(key, 'ru')
            self.assertNotEqual(text, key, f"Ключ {key} возвращает сам себя вместо текста")
            self.assertIsInstance(text, str)
            self.assertTrue(len(text) > 0)
    
    def test_json_examples_are_valid(self):
        """Проверка что примеры JSON валидные"""
        examples = [
            'mail.messages.json_example_inline',
            'mail.messages.json_example_callback'
        ]
        for key in examples:
            text = get_text(key, 'ru')
            self.assertNotEqual(text, key)
            # Проверяем что это валидный JSON
            try:
                data = json.loads(text)
                self.assertIn('inline_keyboard', data)
                self.assertIsInstance(data['inline_keyboard'], list)
            except json.JSONDecodeError:
                self.fail(f"Пример {key} содержит невалидный JSON")
    
    def test_no_regular_keyboard_mentions(self):
        """Проверка что обычные клавиатуры не упоминаются"""
        help_text = get_text('mail.messages.mail_help', 'ru')
        self.assertNotIn('keyboard":', help_text)  # Не должно быть обычной клавиатуры
        self.assertNotIn('resize_keyboard', help_text)
        self.assertNotIn('one_time_keyboard', help_text)


class TestMarkupCustom(unittest.TestCase):
    """Тесты функции markup_custom"""
    
    def test_none_input(self):
        """Проверка обработки None"""
        result = markup_custom(None)
        self.assertIsNone(result)
    
    def test_valid_inline_keyboard(self):
        """Проверка валидной inline клавиатуры"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Кнопка 1", "url": "https://example.com"}],
                [{"text": "Кнопка 2", "callback_data": "action"}]
            ]
        }
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        # Проверяем что это InlineKeyboardMarkup
        self.assertTrue(hasattr(result, 'inline_keyboard'))
    
    def test_mixed_buttons(self):
        """Проверка смешанных кнопок (URL и callback)"""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "URL", "url": "https://test.com"},
                    {"text": "Callback", "callback_data": "test"}
                ]
            ]
        }
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        # Проверяем что обе кнопки в одной строке
        self.assertEqual(len(result.inline_keyboard), 1)
        self.assertEqual(len(result.inline_keyboard[0]), 2)
    
    def test_empty_inline_keyboard(self):
        """Проверка пустой клавиатуры"""
        keyboard = {"inline_keyboard": []}
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.inline_keyboard), 0)
    
    def test_invalid_format(self):
        """Проверка невалидного формата"""
        # Старый формат обычной клавиатуры
        keyboard = {
            "keyboard": [["Кнопка 1", "Кнопка 2"]],
            "resize_keyboard": True
        }
        result = markup_custom(keyboard)
        self.assertIsNone(result)  # Должен вернуть None для неподдерживаемого формата
    
    def test_missing_text_field(self):
        """Проверка обработки кнопок без поля text"""
        keyboard = {
            "inline_keyboard": [
                [{"url": "https://example.com"}],  # Нет text
                [{"text": "Валидная кнопка", "callback_data": "valid"}]
            ]
        }
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        # Проверяем что строка с невалидной кнопкой пропущена
        self.assertEqual(len(result.inline_keyboard), 1)


class TestCheckPyDisabled(unittest.TestCase):
    """Тесты отключения check.py"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_check_py_disabled_by_default(self):
        """Проверка что check.py отключен по умолчанию"""
        # Имитируем импорт check.py
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.modules', {}):
                exec(open('check.py').read(), {'__name__': '__main__'})
        
        self.assertIn('disabled', str(cm.exception).lower())
    
    @patch.dict(os.environ, {'ENABLE_CHECK_SCHEDULER': '1'})
    def test_check_py_can_be_enabled(self):
        """Проверка что check.py можно включить через переменную окружения"""
        # При ENABLE_CHECK_SCHEDULER=1 не должно быть SystemExit на проверке
        # Но будет ImportError так как не все модули загружены
        with self.assertRaises((ImportError, ModuleNotFoundError)):
            exec(open('check.py').read(), {'__name__': '__main__'})


class TestMailSchedulerAtomicity(unittest.IsolatedAsyncioTestCase):
    """Тесты атомарности планировщика рассылок"""
    
    async def test_status_transitions(self):
        """Проверка переходов статусов wait -> run -> sent/error"""
        m = Mail()
        
        # Создаем тестовую рассылку
        test_date = datetime.now() - timedelta(minutes=1)
        mail_id = await m.create_mail(
            date_mail=test_date,
            message_id=999999,
            from_id=123456789,
            keyboard=None
        )
        
        try:
            # Проверяем начальный статус
            mail = await m.get_mail(mail_id)
            self.assertEqual(mail['status'], 'wait')
            
            # Имитируем захват планировщиком
            await m.update_mail(mail_id, 'status', 'run')
            mail = await m.get_mail(mail_id)
            self.assertEqual(mail['status'], 'run')
            
            # Проверяем что рассылка не в списке ожидающих
            wait_mails = await m.get_wait_mails()
            mail_ids = [m['id'] for m in wait_mails] if wait_mails else []
            self.assertNotIn(mail_id, mail_ids)
            
            # Имитируем успешную отправку
            await m.update_mail(mail_id, 'status', 'sent')
            mail = await m.get_mail(mail_id)
            self.assertEqual(mail['status'], 'sent')
            
        finally:
            # Очистка
            await m.delete_mail(mail_id)
    
    async def test_concurrent_access_prevention(self):
        """Проверка предотвращения конкурентного доступа"""
        m = Mail()
        
        # Создаем несколько рассылок
        test_date = datetime.now() - timedelta(minutes=1)
        mail_ids = []
        
        for i in range(3):
            mail_id = await m.create_mail(
                date_mail=test_date,
                message_id=1000000 + i,
                from_id=123456789,
                keyboard=None
            )
            mail_ids.append(mail_id)
        
        try:
            # Первый планировщик захватывает первую рассылку
            await m.update_mail(mail_ids[0], 'status', 'run')
            
            # Проверяем что захваченная рассылка не видна другим
            wait_mails = await m.get_wait_mails()
            wait_ids = [m['id'] for m in wait_mails] if wait_mails else []
            
            self.assertNotIn(mail_ids[0], wait_ids)
            self.assertIn(mail_ids[1], wait_ids)
            self.assertIn(mail_ids[2], wait_ids)
            
        finally:
            # Очистка
            for mail_id in mail_ids:
                try:
                    await m.delete_mail(mail_id)
                except:
                    pass


class TestJSONParsing(unittest.TestCase):
    """Тесты парсинга JSON в обработчике"""
    
    def test_extract_valid_json_from_text(self):
        """Проверка извлечения валидного JSON из текста с мусором"""
        import re
        
        text = """
        Вот пример:
        {
          "inline_keyboard": [
            [{"text": "Кнопка", "url": "https://test.com"}]
          ]
        }
        И еще текст после
        """
        
        # Имитация логики из handlers/mail.py
        candidates = re.findall(r"\{[\s\S]*?\}", text)
        keyboard = None
        for c in candidates:
            try:
                keyboard = json.loads(c)
                break
            except:
                continue
        
        self.assertIsNotNone(keyboard)
        self.assertIn('inline_keyboard', keyboard)
    
    def test_multiple_json_blocks(self):
        """Проверка обработки нескольких JSON блоков"""
        import re
        
        text = """
        {
          "inline_keyboard": [
            [{"text": "Первый", "callback_data": "first"}]
          ]
        }
        
        {
          "inline_keyboard": [
            [{"text": "Второй", "callback_data": "second"}]
          ]
        }
        """
        
        candidates = re.findall(r"\{[\s\S]*?\}", text)
        self.assertEqual(len(candidates), 2)
        
        # Проверяем что оба валидные
        for c in candidates:
            data = json.loads(c)
            self.assertIn('inline_keyboard', data)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Интеграционные тесты"""
    
    async def test_full_mail_flow(self):
        """Проверка полного цикла создания и обработки рассылки"""
        m = Mail()
        
        # 1. Создаем рассылку с inline-клавиатурой
        keyboard = {
            "inline_keyboard": [
                [{"text": "Тест", "callback_data": "test"}]
            ]
        }
        
        test_date = datetime.now() - timedelta(seconds=10)
        mail_id = await m.create_mail(
            date_mail=test_date,
            message_id=2000000,
            from_id=987654321,
            keyboard=keyboard
        )
        
        try:
            # 2. Проверяем что рассылка в списке ожидающих
            wait_mails = await m.get_wait_mails()
            self.assertIsNotNone(wait_mails)
            mail_ids = [m['id'] for m in wait_mails] if wait_mails else []
            self.assertIn(mail_id, mail_ids)
            
            # 3. Имитируем обработку планировщиком
            await m.update_mail(mail_id, 'status', 'run')
            
            # 4. Проверяем что больше не в списке ожидающих
            wait_mails = await m.get_wait_mails()
            mail_ids = [m['id'] for m in wait_mails] if wait_mails else []
            self.assertNotIn(mail_id, mail_ids)
            
            # 5. Завершаем отправку
            await m.update_mail(mail_id, 'status', 'sent')
            
            # 6. Проверяем финальный статус
            mail = await m.get_mail(mail_id)
            self.assertEqual(mail['status'], 'sent')
            
        finally:
            await m.delete_mail(mail_id)
    
    def test_markup_custom_with_localized_example(self):
        """Проверка markup_custom с примером из локализации"""
        # Получаем пример из локализации
        example_json_str = get_text('mail.messages.json_example_inline', 'ru')
        
        # Парсим JSON
        keyboard = json.loads(example_json_str)
        
        # Применяем markup_custom
        result = markup_custom(keyboard)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.inline_keyboard), 2)  # Две строки кнопок
        
        # Проверяем первую кнопку (URL)
        first_button = result.inline_keyboard[0][0]
        self.assertIsNotNone(first_button.url)
        self.assertIn('example.com', first_button.url)
        
        # Проверяем вторую кнопку (callback)
        second_button = result.inline_keyboard[1][0]
        self.assertIsNotNone(second_button.callback_data)
        self.assertEqual(second_button.callback_data, 'support')


def run_tests():
    """Запуск всех тестов с детальным выводом"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем все тест-классы
    suite.addTests(loader.loadTestsFromTestCase(TestLocalization))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkupCustom))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckPyDisabled))
    suite.addTests(loader.loadTestsFromTestCase(TestMailSchedulerAtomicity))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Запускаем с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Выводим итоги
    print("\n" + "=" * 70)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 70)
    print(f"Всего тестов: {result.testsRun}")
    print(f"✅ Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Провалено: {len(result.failures)}")
    print(f"💥 Ошибок: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()[:100]}")
    
    if result.errors:
        print("\n💥 ТЕСТЫ С ОШИБКАМИ:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(':')[-1].strip()[:100]}")
    
    if result.wasSuccessful():
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("\n⚠️ ЕСТЬ ПРОБЛЕМЫ, ТРЕБУЮЩИЕ ВНИМАНИЯ")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
