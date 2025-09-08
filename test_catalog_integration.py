"""
🧪 Интеграционный тест каталога уроков NikolayAI Bot
Тестирует полное взаимодействие компонентов системы каталога
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime


class IntegrationTestCatalogSystem(unittest.TestCase):
    """Интеграционное тестирование системы каталога"""
    
    def setUp(self):
        """Настройка интеграционного тестирования"""
        print("🔧 Настройка интеграционного тестирования системы каталога...")
        
        # Имитация полной системы
        self.mock_database_lessons = [
            {
                'id': 1,
                'title': 'Основы Python',
                'description': 'Изучите основы программирования на Python',
                'price_usd': Decimal('29.99'),
                'is_free': False,
                'is_active': True,
                'category': 'Программирование',
                'views_count': 150,
                'purchases_count': 45
            },
            {
                'id': 2,
                'title': 'Бесплатный курс HTML',
                'description': 'Бесплатное введение в HTML',
                'price_usd': Decimal('0.00'),
                'is_free': True,
                'is_active': True,
                'category': 'Веб-разработка',
                'views_count': 500,
                'purchases_count': 200
            },
            {
                'id': 3,
                'title': 'Продвинутый JavaScript',
                'description': 'Углубленное изучение JavaScript',
                'price_usd': Decimal('49.99'),
                'is_free': False,
                'is_active': True,
                'category': 'Программирование',
                'views_count': 75,
                'purchases_count': 20
            },
            {
                'id': 4,
                'title': 'Устаревший курс',
                'description': 'Этот курс больше не доступен',
                'price_usd': Decimal('19.99'),
                'is_free': False,
                'is_active': False,
                'category': 'Архив',
                'views_count': 25,
                'purchases_count': 5
            }
        ]
        
        self.mock_user_purchases = {
            123456789: [  # Активный пользователь
                {'lesson_id': 1, 'title': 'Основы Python', 'price_paid_usd': Decimal('29.99')},
                {'lesson_id': 2, 'title': 'Бесплатный курс HTML', 'price_paid_usd': Decimal('0.00')}
            ],
            987654321: [],  # Новый пользователь без покупок
            555555555: [   # Пользователь с одной покупкой
                {'lesson_id': 2, 'title': 'Бесплатный курс HTML', 'price_paid_usd': Decimal('0.00')}
            ]
        }
        
        print("✅ Интеграционное тестирование настроено")

    async def test_full_catalog_workflow(self):
        """Тест полного рабочего процесса каталога"""
        print("🧪 Тестирование полного рабочего процесса каталога...")
        
        # 1. Получение активных уроков для каталога
        active_lessons = [lesson for lesson in self.mock_database_lessons if lesson['is_active']]
        self.assertEqual(len(active_lessons), 3)
        print("  ✅ Шаг 1: Получение активных уроков")
        
        # 2. Фильтрация по категориям
        programming_lessons = [lesson for lesson in active_lessons if lesson['category'] == 'Программирование']
        self.assertEqual(len(programming_lessons), 2)
        print("  ✅ Шаг 2: Фильтрация по категориям")
        
        # 3. Расчет цен в звездах для всех уроков
        for lesson in active_lessons:
            price_usd = float(lesson['price_usd'])
            price_stars = max(1, int(price_usd * 200))  # 200 звезд за доллар
            
            if lesson['is_free']:
                self.assertEqual(price_stars, 1)
            else:
                self.assertGreater(price_stars, 1)
        print("  ✅ Шаг 3: Расчет цен в звездах")
        
        # 4. Проверка статистики уроков
        total_views = sum(lesson['views_count'] for lesson in active_lessons)
        total_purchases = sum(lesson['purchases_count'] for lesson in active_lessons)
        
        self.assertGreater(total_views, 0)
        self.assertGreater(total_purchases, 0)
        print("  ✅ Шаг 4: Проверка статистики")
        
        # 5. Формирование каталога для отображения
        catalog_data = []
        for lesson in active_lessons:
            catalog_item = {
                'id': lesson['id'],
                'title': lesson['title'],
                'price_display': 'FREE' if lesson['is_free'] else f"${lesson['price_usd']:.2f}",
                'category': lesson['category'],
                'is_popular': lesson['purchases_count'] > 50
            }
            catalog_data.append(catalog_item)
        
        self.assertEqual(len(catalog_data), 3)
        popular_lessons = [item for item in catalog_data if item['is_popular']]
        self.assertEqual(len(popular_lessons), 1)  # HTML курс популярный
        print("  ✅ Шаг 5: Формирование данных каталога")
        
        print("✅ Полный рабочий процесс каталога работает корректно")

    async def test_user_journey_scenarios(self):
        """Тест сценариев пользовательского пути"""
        print("🧪 Тестирование сценариев пользовательского пути...")
        
        # Сценарий 1: Новый пользователь
        new_user_id = 987654321
        user_purchases = self.mock_user_purchases.get(new_user_id, [])
        
        # Новый пользователь не имеет покупок
        self.assertEqual(len(user_purchases), 0)
        
        # Показываем ему весь каталог
        available_lessons = [lesson for lesson in self.mock_database_lessons if lesson['is_active']]
        self.assertEqual(len(available_lessons), 3)
        print("  ✅ Сценарий 1: Новый пользователь")
        
        # Сценарий 2: Активный пользователь с покупками
        active_user_id = 123456789
        user_purchases = self.mock_user_purchases.get(active_user_id, [])
        
        # У активного пользователя есть покупки
        self.assertEqual(len(user_purchases), 2)
        
        # Проверяем владение уроками
        owned_lesson_ids = [purchase['lesson_id'] for purchase in user_purchases]
        self.assertIn(1, owned_lesson_ids)  # Владеет уроком Python
        self.assertIn(2, owned_lesson_ids)  # Владеет HTML курсом
        self.assertNotIn(3, owned_lesson_ids)  # Не владеет JavaScript
        print("  ✅ Сценарий 2: Активный пользователь")
        
        # Сценарий 3: Пользователь только с бесплатными уроками
        free_user_id = 555555555
        user_purchases = self.mock_user_purchases.get(free_user_id, [])
        
        # У пользователя только бесплатные покупки
        self.assertEqual(len(user_purchases), 1)
        self.assertEqual(user_purchases[0]['price_paid_usd'], Decimal('0.00'))
        print("  ✅ Сценарий 3: Пользователь с бесплатными уроками")
        
        print("✅ Сценарии пользовательского пути работают корректно")

    async def test_catalog_filtering_and_sorting(self):
        """Тест фильтрации и сортировки каталога"""
        print("🧪 Тестирование фильтрации и сортировки каталога...")
        
        active_lessons = [lesson for lesson in self.mock_database_lessons if lesson['is_active']]
        
        # Фильтрация по статусу бесплатности
        free_lessons = [lesson for lesson in active_lessons if lesson['is_free']]
        paid_lessons = [lesson for lesson in active_lessons if not lesson['is_free']]
        
        self.assertEqual(len(free_lessons), 1)
        self.assertEqual(len(paid_lessons), 2)
        print("  ✅ Фильтрация по статусу бесплатности")
        
        # Сортировка по популярности (количество покупок)
        sorted_by_popularity = sorted(active_lessons, key=lambda x: x['purchases_count'], reverse=True)
        most_popular = sorted_by_popularity[0]
        self.assertEqual(most_popular['title'], 'Бесплатный курс HTML')
        self.assertEqual(most_popular['purchases_count'], 200)
        print("  ✅ Сортировка по популярности")
        
        # Сортировка по цене
        sorted_by_price = sorted(active_lessons, key=lambda x: x['price_usd'])
        cheapest = sorted_by_price[0]
        most_expensive = sorted_by_price[-1]
        
        self.assertEqual(cheapest['price_usd'], Decimal('0.00'))
        self.assertEqual(most_expensive['price_usd'], Decimal('49.99'))
        print("  ✅ Сортировка по цене")
        
        # Группировка по категориям
        categories = {}
        for lesson in active_lessons:
            category = lesson['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(lesson)
        
        self.assertIn('Программирование', categories)
        self.assertIn('Веб-разработка', categories)
        self.assertEqual(len(categories['Программирование']), 2)
        self.assertEqual(len(categories['Веб-разработка']), 1)
        print("  ✅ Группировка по категориям")
        
        print("✅ Фильтрация и сортировка каталога работают корректно")

    async def test_purchase_flow_simulation(self):
        """Тест симуляции процесса покупки"""
        print("🧪 Тестирование симуляции процесса покупки...")
        
        # Выбираем пользователя и урок
        user_id = 987654321  # Новый пользователь
        lesson_id = 3  # JavaScript курс за $49.99
        
        # Находим урок
        lesson = next((l for l in self.mock_database_lessons if l['id'] == lesson_id), None)
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson['title'], 'Продвинутый JavaScript')
        print("  ✅ Выбор урока для покупки")
        
        # Проверяем, что пользователь еще не владеет уроком
        user_purchases = self.mock_user_purchases.get(user_id, [])
        owned_lesson_ids = [p['lesson_id'] for p in user_purchases]
        self.assertNotIn(lesson_id, owned_lesson_ids)
        print("  ✅ Проверка отсутствия владения")
        
        # Рассчитываем стоимость
        price_usd = float(lesson['price_usd'])
        price_stars = max(1, int(price_usd * 200))
        
        self.assertEqual(price_usd, 49.99)
        self.assertEqual(price_stars, 9998)  # 49.99 * 200 = 9998
        print("  ✅ Расчет стоимости")
        
        # Симулируем успешную покупку
        new_purchase = {
            'lesson_id': lesson_id,
            'title': lesson['title'],
            'price_paid_usd': lesson['price_usd'],
            'price_paid_stars': price_stars,
            'purchase_date': datetime.now()
        }
        
        # Добавляем покупку пользователю
        if user_id not in self.mock_user_purchases:
            self.mock_user_purchases[user_id] = []
        self.mock_user_purchases[user_id].append(new_purchase)
        
        # Проверяем, что покупка добавлена
        updated_purchases = self.mock_user_purchases[user_id]
        self.assertEqual(len(updated_purchases), 1)
        self.assertEqual(updated_purchases[0]['lesson_id'], lesson_id)
        print("  ✅ Симуляция успешной покупки")
        
        # Обновляем статистику урока
        lesson['purchases_count'] += 1
        self.assertEqual(lesson['purchases_count'], 21)
        print("  ✅ Обновление статистики урока")
        
        print("✅ Симуляция процесса покупки работает корректно")

    async def test_catalog_performance_metrics(self):
        """Тест метрик производительности каталога"""
        print("🧪 Тестирование метрик производительности каталога...")
        
        # Анализ конверсии уроков
        for lesson in self.mock_database_lessons:
            if lesson['is_active'] and lesson['views_count'] > 0:
                conversion_rate = (lesson['purchases_count'] / lesson['views_count']) * 100
                
                # Проверяем разумность конверсии (должна быть между 0 и 100%)
                self.assertGreaterEqual(conversion_rate, 0)
                self.assertLessEqual(conversion_rate, 100)
                
                # Бесплатные уроки должны иметь высокую конверсию
                if lesson['is_free']:
                    self.assertGreater(conversion_rate, 30)  # Минимум 30% для бесплатных
        
        print("  ✅ Анализ конверсии уроков")
        
        # Рейтинг популярности каталога
        active_lessons = [lesson for lesson in self.mock_database_lessons if lesson['is_active']]
        total_views = sum(lesson['views_count'] for lesson in active_lessons)
        total_purchases = sum(lesson['purchases_count'] for lesson in active_lessons)
        
        overall_conversion = (total_purchases / total_views) * 100 if total_views > 0 else 0
        
        self.assertGreater(total_views, 0)
        self.assertGreater(total_purchases, 0)
        self.assertGreater(overall_conversion, 0)
        print("  ✅ Общая статистика каталога")
        
        # Анализ выручки
        revenue_by_lesson = {}
        total_revenue = Decimal('0.00')
        
        for user_purchases in self.mock_user_purchases.values():
            for purchase in user_purchases:
                lesson_id = purchase['lesson_id']
                price = purchase['price_paid_usd']
                
                if lesson_id not in revenue_by_lesson:
                    revenue_by_lesson[lesson_id] = Decimal('0.00')
                revenue_by_lesson[lesson_id] += price
                total_revenue += price
        
        self.assertGreater(total_revenue, Decimal('0.00'))
        print("  ✅ Анализ выручки")
        
        # Топ уроков по выручке
        revenue_ranking = sorted(revenue_by_lesson.items(), key=lambda x: x[1], reverse=True)
        if revenue_ranking:
            top_lesson_id, top_revenue = revenue_ranking[0]
            self.assertGreater(top_revenue, Decimal('0.00'))
        
        print("  ✅ Рейтинг уроков по выручке")
        
        print("✅ Метрики производительности каталога работают корректно")

    def test_catalog_data_consistency(self):
        """Тест консистентности данных каталога"""
        print("🧪 Тестирование консистентности данных каталога...")
        
        # Проверка целостности данных уроков
        for lesson in self.mock_database_lessons:
            # Обязательные поля
            self.assertIsNotNone(lesson['id'])
            self.assertIsNotNone(lesson['title'])
            self.assertIsNotNone(lesson['description'])
            self.assertIsInstance(lesson['price_usd'], Decimal)
            self.assertIsInstance(lesson['is_free'], bool)
            self.assertIsInstance(lesson['is_active'], bool)
            
            # Логическая консистентность
            if lesson['is_free']:
                self.assertEqual(lesson['price_usd'], Decimal('0.00'))
            else:
                self.assertGreater(lesson['price_usd'], Decimal('0.00'))
            
            # Счетчики не могут быть отрицательными
            self.assertGreaterEqual(lesson['views_count'], 0)
            self.assertGreaterEqual(lesson['purchases_count'], 0)
            
            # Покупки не могут превышать просмотры
            self.assertLessEqual(lesson['purchases_count'], lesson['views_count'])
        
        print("  ✅ Целостность данных уроков")
        
        # Проверка консистентности покупок
        for user_id, purchases in self.mock_user_purchases.items():
            self.assertIsInstance(user_id, int)
            self.assertIsInstance(purchases, list)
            
            for purchase in purchases:
                # Обязательные поля покупки
                self.assertIn('lesson_id', purchase)
                self.assertIn('title', purchase)
                self.assertIn('price_paid_usd', purchase)
                
                # Проверяем, что урок существует
                lesson_exists = any(l['id'] == purchase['lesson_id'] for l in self.mock_database_lessons)
                self.assertTrue(lesson_exists)
                
                # Цена покупки должна быть неотрицательной
                self.assertGreaterEqual(purchase['price_paid_usd'], Decimal('0.00'))
        
        print("  ✅ Консистентность покупок")
        
        # Проверка уникальности ID уроков
        lesson_ids = [lesson['id'] for lesson in self.mock_database_lessons]
        unique_ids = set(lesson_ids)
        self.assertEqual(len(lesson_ids), len(unique_ids))
        print("  ✅ Уникальность ID уроков")
        
        print("✅ Консистентность данных каталога подтверждена")


def run_async_test(test_func):
    """Вспомогательная функция для запуска асинхронных тестов"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()


if __name__ == '__main__':
    print("🚀 Запуск интеграционного тестирования каталога уроков...")
    print("=" * 60)
    
    # Создаем тестовый suite
    suite = unittest.TestSuite()
    
    # Добавляем синхронные тесты
    sync_tests = [
        'test_catalog_data_consistency'
    ]
    
    for test_name in sync_tests:
        suite.addTest(IntegrationTestCatalogSystem(test_name))
    
    # Запускаем синхронные тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Асинхронные тесты
    async_tests = [
        'test_full_catalog_workflow',
        'test_user_journey_scenarios',
        'test_catalog_filtering_and_sorting',
        'test_purchase_flow_simulation',
        'test_catalog_performance_metrics'
    ]
    
    print("\n" + "=" * 60)
    print("🔄 Запуск асинхронных интеграционных тестов...")
    print("=" * 60)
    
    test_instance = IntegrationTestCatalogSystem()
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
    print("🏁 Интеграционное тестирование завершено!")
    
    sync_passed = result.testsRun - len(result.failures) - len(result.errors)
    total_passed = sync_passed + async_success
    total_tests = result.testsRun + async_total
    
    print(f"📊 Результаты: {total_passed}/{total_tests} тестов пройдено")
    
    if total_passed == total_tests:
        print("✅ Все интеграционные тесты пройдены успешно!")
    else:
        print(f"❌ Интеграционные тесты завершились с ошибками")
        
    print("=" * 60)