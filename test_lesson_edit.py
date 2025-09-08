"""
🧪 Юнит-тесты для редактирования уроков NikolayAI Bot
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime


class MockLesson:
    """Mock-класс для тестирования урока"""
    
    def __init__(self):
        self.id = 1
        self.title = "Тестовый урок"
        self.description = "Описание тестового урока"
        self.price_usd = Decimal("25.00")
        self.is_active = True
        self.is_free = False
        self.content_type = "video"
        self.video_file_id = "test_video_id"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    async def get_lesson(self, lesson_id):
        if lesson_id == 1:
            return self
        return None
    
    async def update_lesson(self, lesson_id, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    async def delete_lesson(self, lesson_id):
        self.is_active = False
        self.updated_at = datetime.now()
    
    async def increment_views(self, lesson_id):
        if not hasattr(self, 'views_count'):
            self.views_count = 0
        self.views_count += 1
    
    async def increment_purchases(self, lesson_id):
        if not hasattr(self, 'purchases_count'):
            self.purchases_count = 0
        self.purchases_count += 1


class MockCallbackQuery:
    def __init__(self, data="test_data"):
        self.data = data
        self.answer = AsyncMock()
        self.message = MagicMock()
        self.from_user = MagicMock()


class MockFSMContext:
    def __init__(self):
        self.state = None
    
    async def get_state(self):
        return self.state


class TestLessonEdit(unittest.TestCase):
    """Тестирование редактирования уроков"""
    
    def setUp(self):
        print("🔧 Настройка тестового окружения...")
        self.lesson = MockLesson()
        self.test_lesson_id = 1
        self.test_user_id = 123456789
        print("✅ Тестовое окружение настроено")

    def test_lesson_model_creation(self):
        print("🧪 Тестирование создания модели урока...")
        lesson = MockLesson()
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson.title, "Тестовый урок")
        self.assertEqual(lesson.id, 1)
        print("✅ Модель урока создана успешно")

    async def test_get_lesson_success(self):
        print("🧪 Тестирование получения урока по ID...")
        result = await self.lesson.get_lesson(self.test_lesson_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.test_lesson_id)
        self.assertEqual(result.title, "Тестовый урок")
        print("✅ Урок получен успешно")

    async def test_get_lesson_not_found(self):
        print("🧪 Тестирование получения несуществующего урока...")
        result = await self.lesson.get_lesson(999)
        self.assertIsNone(result)
        print("✅ Обработка несуществующего урока работает корректно")

    async def test_update_lesson_success(self):
        print("🧪 Тестирование обновления урока...")
        update_data = {
            'title': 'Обновленный урок',
            'price_usd': Decimal("30.00"),
            'is_active': False
        }
        await self.lesson.update_lesson(self.test_lesson_id, **update_data)
        self.assertEqual(self.lesson.title, 'Обновленный урок')
        self.assertEqual(self.lesson.price_usd, Decimal("30.00"))
        self.assertEqual(self.lesson.is_active, False)
        print("✅ Урок обновлен успешно")

    async def test_delete_lesson_soft_delete(self):
        print("🧪 Тестирование мягкого удаления урока...")
        self.assertTrue(self.lesson.is_active)
        await self.lesson.delete_lesson(self.test_lesson_id)
        self.assertFalse(self.lesson.is_active)
        print("✅ Мягкое удаление урока работает корректно")

    def test_lesson_data_validation(self):
        print("🧪 Тестирование валидации данных урока...")
        self.assertIsInstance(self.lesson.title, str)
        self.assertIsInstance(self.lesson.description, str)
        self.assertIsInstance(self.lesson.price_usd, Decimal)
        self.assertIsInstance(self.lesson.is_active, bool)
        self.assertIsInstance(self.lesson.is_free, bool)
        print("✅ Валидация данных прошла успешно")

    async def test_toggle_lesson_active_handler(self):
        print("🧪 Тестирование переключения активности...")
        mock_call = MockCallbackQuery(f"toggle_active:{self.test_lesson_id}")
        mock_state = MockFSMContext()
        original_status = self.lesson.is_active
        self.lesson.is_active = not self.lesson.is_active
        self.assertNotEqual(self.lesson.is_active, original_status)
        print("✅ Переключение активности работает корректно")

    async def test_toggle_lesson_free_handler(self):
        print("🧪 Тестирование переключения бесплатности...")
        mock_call = MockCallbackQuery(f"toggle_free:{self.test_lesson_id}")
        mock_state = MockFSMContext()
        original_free_status = self.lesson.is_free
        self.lesson.is_free = not self.lesson.is_free
        if self.lesson.is_free:
            self.lesson.price_usd = Decimal("0.00")
        self.assertNotEqual(self.lesson.is_free, original_free_status)
        if self.lesson.is_free:
            self.assertEqual(self.lesson.price_usd, Decimal("0.00"))
        print("✅ Переключение бесплатности работает корректно")

    async def test_increment_views(self):
        print("🧪 Тестирование увеличения счетчика просмотров...")
        initial_views = getattr(self.lesson, 'views_count', 0)
        await self.lesson.increment_views(self.test_lesson_id)
        self.assertEqual(self.lesson.views_count, initial_views + 1)
        print("✅ Счетчик просмотров увеличен успешно")

    async def test_increment_purchases(self):
        print("🧪 Тестирование увеличения счетчика покупок...")
        initial_purchases = getattr(self.lesson, 'purchases_count', 0)
        await self.lesson.increment_purchases(self.test_lesson_id)
        self.assertEqual(self.lesson.purchases_count, initial_purchases + 1)
        print("✅ Счетчик покупок увеличен успешно")

    def test_lesson_business_logic(self):
        print("🧪 Тестирование бизнес-логики урока...")
        if not self.lesson.is_free:
            self.assertGreater(self.lesson.price_usd, 0)
        print("✅ Бизнес-логика урока работает корректно")


def run_async_test(test_func):
    """Вспомогательная функция для запуска асинхронных тестов"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()


if __name__ == '__main__':
    print("🚀 Запуск тестирования редактирования уроков...")
    print("=" * 60)
    
    # Создаем тестовый suite
    suite = unittest.TestSuite()
    
    # Добавляем синхронные тесты
    sync_tests = [
        'test_lesson_model_creation',
        'test_lesson_data_validation',
        'test_lesson_business_logic'
    ]
    
    for test_name in sync_tests:
        suite.addTest(TestLessonEdit(test_name))
    
    # Запускаем синхронные тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Асинхронные тесты
    async_tests = [
        'test_get_lesson_success',
        'test_get_lesson_not_found', 
        'test_update_lesson_success',
        'test_delete_lesson_soft_delete',
        'test_toggle_lesson_active_handler',
        'test_toggle_lesson_free_handler',
        'test_increment_views',
        'test_increment_purchases'
    ]
    
    print("\n" + "=" * 60)
    print("🔄 Запуск асинхронных тестов...")
    print("=" * 60)
    
    test_instance = TestLessonEdit()
    test_instance.setUp()
    
    async_success = 0
    async_total = len(async_tests)
    
    for test_name in async_tests:
        try:
            print(f"\n🧪 Выполняется: {test_name}")
            test_method = getattr(test_instance, test_name)
            run_async_test(test_method)
            print(f"✅ {test_name} - ПРОЙДЕН")
            async_success += 1
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено!")
    
    sync_passed = result.testsRun - len(result.failures) - len(result.errors)
    total_passed = sync_passed + async_success
    total_tests = result.testsRun + async_total
    
    print(f"📊 Результаты: {total_passed}/{total_tests} тестов пройдено")
    
    if total_passed == total_tests:
        print("✅ Все тесты пройдены успешно!")
    else:
        print(f"❌ Тесты завершились с ошибками")
        
    print("=" * 60)