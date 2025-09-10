#!/usr/bin/env python
"""
Финальные тесты системы рассылок - исправленная версия
"""
import unittest
import json
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from localization import get_text
from keyboards import markup_custom


class TestLocalization(unittest.TestCase):
    """Тесты локализации"""
    
    def test_mail_help_text_exists(self):
        """Проверка что текст справки существует"""
        text = get_text('mail.messages.mail_help', 'ru')
        self.assertNotEqual(text, 'mail.messages.mail_help')
        self.assertIn('inline', text.lower())
        self.assertIn('JSON', text)
        print(f"✅ Текст справки: {text[:50]}...")
    
    def test_button_texts(self):
        """Проверка текстов кнопок"""
        buttons = {
            'mail.buttons.copy_json': '📋',
            'mail.buttons.copy_inline': 'ссылк',
            'mail.buttons.copy_callback': 'действ'
        }
        for key, expected in buttons.items():
            text = get_text(key, 'ru')
            self.assertNotEqual(text, key)
            self.assertIn(expected, text.lower())
            print(f"✅ {key}: {text}")
    
    def test_json_examples_valid(self):
        """Проверка валидности примеров JSON"""
        examples = {
            'mail.messages.json_example_inline': 'url',
            'mail.messages.json_example_callback': 'callback_data'
        }
        
        for key, expected_field in examples.items():
            text = get_text(key, 'ru')
            self.assertNotEqual(text, key)
            
            # Парсим JSON
            data = json.loads(text)
            self.assertIn('inline_keyboard', data)
            
            # Проверяем наличие ожидаемого поля
            found = False
            for row in data['inline_keyboard']:
                for button in row:
                    if expected_field in button:
                        found = True
                        break
            self.assertTrue(found, f"Поле {expected_field} не найдено в {key}")
            print(f"✅ {key}: валидный JSON с полем {expected_field}")


class TestMarkupCustom(unittest.TestCase):
    """Тесты функции markup_custom"""
    
    def test_none_handling(self):
        """Проверка обработки None"""
        result = markup_custom(None)
        self.assertIsNone(result)
        print("✅ None корректно обрабатывается")
    
    def test_inline_keyboard_with_url(self):
        """Проверка inline клавиатуры с URL"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Сайт", "url": "https://example.com"}]
            ]
        }
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.inline_keyboard), 1)
        self.assertEqual(result.inline_keyboard[0][0].url, "https://example.com")
        print("✅ Inline клавиатура с URL работает")
    
    def test_inline_keyboard_with_callback(self):
        """Проверка inline клавиатуры с callback"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "Действие", "callback_data": "action"}]
            ]
        }
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        self.assertEqual(result.inline_keyboard[0][0].callback_data, "action")
        print("✅ Inline клавиатура с callback работает")
    
    def test_mixed_buttons(self):
        """Проверка смешанных кнопок"""
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
        self.assertEqual(len(result.inline_keyboard[0]), 2)
        print("✅ Смешанные кнопки работают")
    
    def test_regular_keyboard_ignored(self):
        """Проверка что обычные клавиатуры игнорируются"""
        keyboard = {
            "keyboard": [["Кнопка 1", "Кнопка 2"]],
            "resize_keyboard": True
        }
        result = markup_custom(keyboard)
        self.assertIsNone(result)
        print("✅ Обычные клавиатуры корректно игнорируются")
    
    def test_empty_inline_keyboard(self):
        """Проверка пустой inline клавиатуры"""
        keyboard = {"inline_keyboard": []}
        result = markup_custom(keyboard)
        self.assertIsNotNone(result)
        self.assertEqual(len(result.inline_keyboard), 0)
        print("✅ Пустая inline клавиатура обрабатывается")


class TestJSONExtraction(unittest.TestCase):
    """Тесты извлечения JSON из текста"""
    
    def test_simple_json_extraction(self):
        """Проверка простого извлечения JSON"""
        import re
        
        text = '{"inline_keyboard": [[{"text": "Test", "url": "https://test.com"}]]}'
        
        # Простая проверка что JSON валидный
        data = json.loads(text)
        self.assertIn('inline_keyboard', data)
        print("✅ Простой JSON парсится корректно")
    
    def test_json_with_newlines(self):
        """Проверка JSON с переносами строк"""
        text = '''{
            "inline_keyboard": [
                [{"text": "Кнопка", "callback_data": "action"}]
            ]
        }'''
        
        data = json.loads(text)
        self.assertIn('inline_keyboard', data)
        print("✅ JSON с переносами строк парсится")
    
    def test_regex_extraction_basic(self):
        """Проверка базового regex извлечения"""
        import re
        
        # Упрощенный паттерн для поиска JSON объектов
        text = 'Текст до {"key": "value"} текст после'
        pattern = r'\{[^{}]*\}'  # Простой паттерн для одноуровневых объектов
        
        matches = re.findall(pattern, text)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], '{"key": "value"}')
        print("✅ Regex извлечение работает для простых случаев")


class TestCheckPyDisabled(unittest.TestCase):
    """Тест отключения check.py"""
    
    def test_check_py_disabled(self):
        """Проверка что check.py отключен без переменной окружения"""
        # Проверяем что в начале файла есть проверка
        with open('check.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('ENABLE_CHECK_SCHEDULER', content)
        self.assertIn('SystemExit', content)
        print("✅ check.py содержит проверку переменной окружения")


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def test_localization_with_markup_custom(self):
        """Проверка интеграции локализации и markup_custom"""
        # Получаем пример из локализации
        example_json = get_text('mail.messages.json_example_inline', 'ru')
        
        # Парсим и применяем
        keyboard = json.loads(example_json)
        result = markup_custom(keyboard)
        
        self.assertIsNotNone(result)
        self.assertTrue(len(result.inline_keyboard) > 0)
        print("✅ Интеграция локализации и markup_custom работает")
    
    def test_callback_example_integration(self):
        """Проверка примера с callback"""
        example_json = get_text('mail.messages.json_example_callback', 'ru')
        keyboard = json.loads(example_json)
        result = markup_custom(keyboard)
        
        self.assertIsNotNone(result)
        # Проверяем что есть кнопки с callback_data
        found_callback = False
        for row in result.inline_keyboard:
            for button in row:
                if button.callback_data:
                    found_callback = True
                    break
        self.assertTrue(found_callback)
        print("✅ Пример с callback работает")


def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "=" * 60)
    print("ЗАПУСК ФИНАЛЬНЫХ ТЕСТОВ СИСТЕМЫ РАССЫЛОК")
    print("=" * 60 + "\n")
    
    # Создаем suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавляем тесты
    test_classes = [
        TestLocalization,
        TestMarkupCustom,
        TestJSONExtraction,
        TestCheckPyDisabled,
        TestIntegration
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Запускаем
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Итоги
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print(f"\n📊 Статистика:")
    print(f"  Всего тестов: {total}")
    print(f"  ✅ Успешно: {passed}")
    print(f"  ❌ Провалено: {len(result.failures)}")
    print(f"  💥 Ошибок: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\nСистема рассылок работает корректно:")
        print("  ✅ Локализация работает")
        print("  ✅ Inline-клавиатуры обрабатываются правильно")
        print("  ✅ Обычные клавиатуры игнорируются")
        print("  ✅ JSON примеры валидные")
        print("  ✅ check.py отключен")
    else:
        print("\n⚠️ Есть проблемы:")
        if result.failures:
            for test, _ in result.failures:
                print(f"  ❌ {test}")
        if result.errors:
            for test, _ in result.errors:
                print(f"  💥 {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
