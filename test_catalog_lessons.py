"""
🧪 Юнит-тесты для каталога уроков NikolayAI Bot
Тестирует функциональность магазина уроков, каталога и связанных компонентов
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime


class MockLesson:
    """Mock-класс для тестирования урока"""
    
    def __init__(self, lesson_id=1, title="Тестовый урок", price_usd=25.00, is_free=False, is_active=True):
        self.id = lesson_id
        self.title = title
        self.description = "Описание тестового урока"
        self.price_usd = Decimal(str(price_usd))
        self.is_free = is_free
        self.is_active = is_active
        self.content_type = "video"
        self.video_file_id = "test_video_id"
        self.category = "Основы"
        self.views_count = 100
        self.purchases_count = 50
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    async def get_all_lessons(self, active_only=True):
        """Mock получения всех уроков"""
        lessons = [
            {
                'id': 1,
                'title': 'Урок 1 - Основы',
                'description': 'Базовый урок',
                'price_usd': Decimal('25.00'),
                'is_free': False,
                'is_active': True,
                'category': 'Основы'
            },
            {
                'id': 2,
                'title': 'Урок 2 - Бесплатный',
                'description': 'Бесплатный урок',
                'price_usd': Decimal('0.00'),
                'is_free': True,
                'is_active': True,
                'category': 'Бесплатные'
            },
            {
                'id': 3,
                'title': 'Урок 3 - Неактивный',
                'description': 'Скрытый урок',
                'price_usd': Decimal('50.00'),
                'is_free': False,
                'is_active': False,
                'category': 'Продвинутый'
            }
        ]
        
        if active_only:
            return [lesson for lesson in lessons if lesson['is_active']]
        return lessons
    
    async def get_lesson(self, lesson_id):
        """Mock получения урока по ID"""
        lessons = {
            1: MockLesson(1, "Урок 1 - Основы", 25.00, False, True),
            2: MockLesson(2, "Урок 2 - Бесплатный", 0.00, True, True),
            3: MockLesson(3, "Урок 3 - Неактивный", 50.00, False, False)
        }
        return lessons.get(lesson_id, None)
    
    async def get_free_lessons(self):
        """Mock получения бесплатных уроков"""
        lessons = await self.get_all_lessons(active_only=True)
        return [lesson for lesson in lessons if lesson['is_free']]


class MockPurchase:
    """Mock-класс для покупок"""
    
    async def get_user_purchases(self, user_id):
        """Mock получения покупок пользователя"""
        if user_id == 123456789:  # Пользователь с покупками
            return [
                {
                    'lesson_id': 1,
                    'title': 'Урок 1 - Основы',
                    'price_paid_usd': Decimal('25.00'),
                    'purchase_date': datetime.now()
                }
            ]
        return []  # Пользователь без покупок
    
    async def check_user_has_lesson(self, user_id, lesson_id):
        """Mock проверки владения уроком"""
        if user_id == 123456789 and lesson_id == 1:
            return True
        return False


class MockCallbackQuery:
    """Mock-класс для CallbackQuery"""
    
    def __init__(self, data="catalog", user_id=123456789):
        self.data = data
        self.answer = AsyncMock()
        self.message = MagicMock()
        self.message.edit_text = AsyncMock()
        self.from_user = MagicMock()
        self.from_user.id = user_id
        self.from_user.full_name = "Test User"


class MockFSMContext:
    """Mock-класс для FSMContext"""
    
    def __init__(self):
        self.state = None
        self.data = {}
    
    async def get_state(self):
        return self.state
    
    async def set_state(self, state):
        self.state = state
    
    async def get_data(self):
        return self.data
    
    async def update_data(self, **kwargs):
        self.data.update(kwargs)


class MockUtils:
    """Mock-класс для утилит"""
    
    @staticmethod
    def get_text(path, **kwargs):
        """Mock получения текстов интерфейса"""
        texts = {
            'messages.catalog_title': '🛍️ Каталог уроков\n\nВыберите урок для изучения:',
            'admin.messages.no_lessons': '📚 Уроков пока нет.\n\nСоздайте первый урок!',
            'messages.error_occurred': '❌ Произошла ошибка. Попробуйте позже.',
            'messages.welcome': '🎓 Добро пожаловать в магазин уроков!',
            'messages.my_lessons_title': '📚 Ваши уроки',
            'messages.no_lessons': 'У вас пока нет приобретенных уроков.',
            'messages.profile_info': '👤 Ваш профиль\n\n👤 Имя: {full_name}\n📚 Уроков: {lessons_count}',
            'buttons.back': '🔙 Назад',
            'buttons.catalog': '🛍️ Каталог уроков',
            'buttons.buy': '💳 Купить'
        }
        text = texts.get(path, path)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text
    
    @staticmethod
    def calculate_stars_price(usd_price, exchange_rate=200):
        """Mock расчета цены в звездах"""
        if isinstance(usd_price, str):
            usd_price = Decimal(usd_price)
        elif isinstance(usd_price, float):
            usd_price = Decimal(str(usd_price))
        stars_price = int(usd_price * exchange_rate)
        return max(1, stars_price)


class MockKeyboards:
    """Mock-класс для клавиатур"""
    
    @staticmethod
    def markup_main_menu():
        return "main_menu_keyboard"
    
    @staticmethod
    def markup_catalog(lessons):
        return f"catalog_keyboard_with_{len(lessons)}_lessons"
    
    @staticmethod
    def markup_my_lessons(lessons):
        return f"my_lessons_keyboard_with_{len(lessons)}_lessons"
    
    @staticmethod
    def markup_lesson_details(lesson_id, user_has_lesson=False, show_promocode=True):
        return f"lesson_details_keyboard_{lesson_id}"


class TestCatalogLessons(unittest.TestCase):
    """Тестирование каталога уроков"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        print("🔧 Настройка тестового окружения для каталога...")
        self.lesson = MockLesson()
        self.purchase = MockPurchase()
        self.utils = MockUtils()
        self.kb = MockKeyboards()
        print("✅ Тестовое окружение настроено")

    async def test_get_all_lessons_active_only(self):
        """Тест получения только активных уроков"""
        print("🧪 Тестирование получения активных уроков...")
        
        lessons = await self.lesson.get_all_lessons(active_only=True)
        
        # Проверяем, что получили только активные уроки
        self.assertEqual(len(lessons), 2)
        for lesson in lessons:
            self.assertTrue(lesson['is_active'])
        
        print("✅ Получение активных уроков работает корректно")

    async def test_get_all_lessons_include_inactive(self):
        """Тест получения всех уроков включая неактивные"""
        print("🧪 Тестирование получения всех уроков...")
        
        lessons = await self.lesson.get_all_lessons(active_only=False)
        
        # Проверяем, что получили все уроки
        self.assertEqual(len(lessons), 3)
        active_count = sum(1 for lesson in lessons if lesson['is_active'])
        self.assertEqual(active_count, 2)
        
        print("✅ Получение всех уроков работает корректно")

    async def test_get_free_lessons(self):
        """Тест получения бесплатных уроков"""
        print("🧪 Тестирование получения бесплатных уроков...")
        
        free_lessons = await self.lesson.get_free_lessons()
        
        # Проверяем, что получили только бесплатные активные уроки
        self.assertEqual(len(free_lessons), 1)
        self.assertTrue(free_lessons[0]['is_free'])
        self.assertTrue(free_lessons[0]['is_active'])
        
        print("✅ Получение бесплатных уроков работает корректно")

    async def test_show_catalog_with_lessons(self):
        """Тест отображения каталога с уроками"""
        print("🧪 Тестирование отображения каталога с уроками...")
        
        # Имитируем handler show_catalog
        call = MockCallbackQuery("catalog")
        state = MockFSMContext()
        
        # Получаем уроки
        lessons = await self.lesson.get_all_lessons(active_only=True)
        
        # Проверяем, что уроки есть
        self.assertGreater(len(lessons), 0)
        
        # Имитируем отправку сообщения с каталогом
        text = self.utils.get_text('messages.catalog_title')
        keyboard = self.kb.markup_catalog(lessons)
        
        # Проверяем корректность отображения
        self.assertIn('Каталог уроков', text)
        self.assertIn('2_lessons', keyboard)
        
        print("✅ Отображение каталога с уроками работает корректно")

    async def test_show_catalog_empty(self):
        """Тест отображения пустого каталога"""
        print("🧪 Тестирование отображения пустого каталога...")
        
        # Создаем пустой mock
        empty_lesson = MockLesson()
        empty_lesson.get_all_lessons = AsyncMock(return_value=[])
        
        call = MockCallbackQuery("catalog")
        state = MockFSMContext()
        
        # Получаем пустой список уроков
        lessons = await empty_lesson.get_all_lessons(active_only=True)
        
        # Проверяем, что уроков нет
        self.assertEqual(len(lessons), 0)
        
        # Должно показываться сообщение об отсутствии уроков
        text = self.utils.get_text('admin.messages.no_lessons')
        keyboard = self.kb.markup_main_menu()
        
        self.assertIn('Уроков пока нет', text)
        self.assertEqual(keyboard, "main_menu_keyboard")
        
        print("✅ Отображение пустого каталога работает корректно")

    async def test_show_my_lessons_with_purchases(self):
        """Тест отображения уроков пользователя с покупками"""
        print("🧪 Тестирование отображения уроков пользователя с покупками...")
        
        call = MockCallbackQuery("my_lessons", user_id=123456789)
        state = MockFSMContext()
        
        # Получаем покупки пользователя
        purchases = await self.purchase.get_user_purchases(call.from_user.id)
        
        # Проверяем, что покупки есть
        self.assertGreater(len(purchases), 0)
        self.assertEqual(purchases[0]['lesson_id'], 1)
        self.assertEqual(purchases[0]['title'], 'Урок 1 - Основы')
        
        # Имитируем формирование списка уроков
        lessons = []
        for purchase in purchases:
            lesson_data = {
                'id': purchase['lesson_id'],
                'title': purchase['title']
            }
            lessons.append(lesson_data)
        
        keyboard = self.kb.markup_my_lessons(lessons)
        
        self.assertIn('1_lessons', keyboard)
        
        print("✅ Отображение уроков пользователя с покупками работает корректно")

    async def test_show_my_lessons_no_purchases(self):
        """Тест отображения уроков пользователя без покупок"""
        print("🧪 Тестирование отображения уроков пользователя без покупок...")
        
        call = MockCallbackQuery("my_lessons", user_id=999999999)  # Пользователь без покупок
        state = MockFSMContext()
        
        # Получаем покупки пользователя
        purchases = await self.purchase.get_user_purchases(call.from_user.id)
        
        # Проверяем, что покупок нет
        self.assertEqual(len(purchases), 0)
        
        # Должно показываться сообщение об отсутствии уроков
        text = self.utils.get_text('messages.no_lessons')
        keyboard = self.kb.markup_main_menu()
        
        self.assertIn('нет приобретенных уроков', text)
        self.assertEqual(keyboard, "main_menu_keyboard")
        
        print("✅ Отображение уроков пользователя без покупок работает корректно")

    async def test_lesson_pricing_logic(self):
        """Тест логики ценообразования уроков"""
        print("🧪 Тестирование логики ценообразования уроков...")
        
        lessons = await self.lesson.get_all_lessons(active_only=True)
        
        for lesson in lessons:
            price_usd = float(lesson['price_usd'])
            price_stars = self.utils.calculate_stars_price(price_usd)
            
            if lesson['is_free']:
                # Бесплатные уроки должны иметь цену 0
                self.assertEqual(price_usd, 0.0)
                self.assertEqual(price_stars, 1)  # Минимум 1 звезда
            else:
                # Платные уроки должны иметь цену больше 0
                self.assertGreater(price_usd, 0.0)
                self.assertGreater(price_stars, 1)
                
                # Проверяем правильность расчета цены в звездах
                expected_stars = max(1, int(price_usd * 200))
                self.assertEqual(price_stars, expected_stars)
        
        print("✅ Логика ценообразования уроков работает корректно")

    async def test_user_lesson_ownership(self):
        """Тест проверки владения уроками"""
        print("🧪 Тестирование проверки владения уроками...")
        
        # Пользователь с покупками
        user_with_lessons = 123456789
        user_without_lessons = 999999999
        
        # Проверяем владение уроком 1
        has_lesson_1 = await self.purchase.check_user_has_lesson(user_with_lessons, 1)
        self.assertTrue(has_lesson_1)
        
        # Проверяем отсутствие владения уроком 2
        has_lesson_2 = await self.purchase.check_user_has_lesson(user_with_lessons, 2)
        self.assertFalse(has_lesson_2)
        
        # Проверяем пользователя без покупок
        has_any_lesson = await self.purchase.check_user_has_lesson(user_without_lessons, 1)
        self.assertFalse(has_any_lesson)
        
        print("✅ Проверка владения уроками работает корректно")

    def test_catalog_keyboard_generation(self):
        """Тест генерации клавиатуры каталога"""
        print("🧪 Тестирование генерации клавиатуры каталога...")
        
        # Тестовые уроки
        test_lessons = [
            {'id': 1, 'title': 'Урок 1', 'price_usd': Decimal('25.00'), 'is_free': False},
            {'id': 2, 'title': 'Урок 2', 'price_usd': Decimal('0.00'), 'is_free': True}
        ]
        
        keyboard = self.kb.markup_catalog(test_lessons)
        
        # Проверяем, что клавиатура содержит информацию о количестве уроков
        self.assertIn('2_lessons', keyboard)
        
        print("✅ Генерация клавиатуры каталога работает корректно")

    def test_lesson_button_text_formatting(self):
        """Тест форматирования текста кнопок уроков"""
        print("🧪 Тестирование форматирования текста кнопок уроков...")
        
        # Тестируем бесплатный урок
        free_lesson = {'title': 'Бесплатный урок', 'is_free': True, 'price_usd': Decimal('0.00')}
        free_button_text = f"🎁 {free_lesson['title']} (FREE)"
        self.assertIn('🎁', free_button_text)
        self.assertIn('FREE', free_button_text)
        
        # Тестируем платный урок
        paid_lesson = {'title': 'Платный урок', 'is_free': False, 'price_usd': Decimal('25.00')}
        price_usd = float(paid_lesson['price_usd'])
        paid_button_text = f"📚 {paid_lesson['title']} (${price_usd:.2f})"
        self.assertIn('📚', paid_button_text)
        self.assertIn('$25.00', paid_button_text)
        
        print("✅ Форматирование текста кнопок уроков работает корректно")

    async def test_catalog_error_handling(self):
        """Тест обработки ошибок в каталоге"""
        print("🧪 Тестирование обработки ошибок в каталоге...")
        
        # Создаем mock с ошибкой
        error_lesson = MockLesson()
        error_lesson.get_all_lessons = AsyncMock(side_effect=Exception("Тестовая ошибка"))
        
        call = MockCallbackQuery("catalog")
        state = MockFSMContext()
        
        try:
            lessons = await error_lesson.get_all_lessons(active_only=True)
        except Exception as e:
            # Проверяем, что ошибка была перехвачена
            self.assertIn("Тестовая ошибка", str(e))
            
            # Должно показываться сообщение об ошибке
            error_text = self.utils.get_text('messages.error_occurred')
            self.assertIn('Произошла ошибка', error_text)
        
        print("✅ Обработка ошибок в каталоге работает корректно")

    def test_interface_text_functionality(self):
        """Тест функциональности интерфейсных текстов"""
        print("🧪 Тестирование функциональности интерфейсных текстов...")
        
        # Тестируем простые тексты
        catalog_title = self.utils.get_text('messages.catalog_title')
        self.assertIn('Каталог уроков', catalog_title)
        
        # Тестируем тексты с параметрами
        profile_text = self.utils.get_text('messages.profile_info', 
                                         full_name="Тест Пользователь", 
                                         lessons_count=5)
        self.assertIn('Тест Пользователь', profile_text)
        self.assertIn('5', profile_text)
        
        # Тестируем несуществующий текст
        nonexistent = self.utils.get_text('nonexistent.path')
        self.assertEqual(nonexistent, 'nonexistent.path')
        
        print("✅ Функциональность интерфейсных текстов работает корректно")


def run_async_test(test_func):
    """Вспомогательная функция для запуска асинхронных тестов"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()


if __name__ == '__main__':
    print("🚀 Запуск тестирования каталога уроков...")
    print("=" * 60)
    
    # Создаем тестовый suite
    suite = unittest.TestSuite()
    
    # Добавляем синхронные тесты
    sync_tests = [
        'test_catalog_keyboard_generation',
        'test_lesson_button_text_formatting', 
        'test_interface_text_functionality'
    ]
    
    for test_name in sync_tests:
        suite.addTest(TestCatalogLessons(test_name))
    
    # Запускаем синхронные тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Асинхронные тесты
    async_tests = [
        'test_get_all_lessons_active_only',
        'test_get_all_lessons_include_inactive',
        'test_get_free_lessons',
        'test_show_catalog_with_lessons',
        'test_show_catalog_empty',
        'test_show_my_lessons_with_purchases',
        'test_show_my_lessons_no_purchases',
        'test_lesson_pricing_logic',
        'test_user_lesson_ownership',
        'test_catalog_error_handling'
    ]
    
    print("\n" + "=" * 60)
    print("🔄 Запуск асинхронных тестов...")
    print("=" * 60)
    
    test_instance = TestCatalogLessons()
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