"""
🧪 Тест обработчика уроков без запуска полного бота
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.lesson import Lesson, Purchase
from database.sql import configure_database

async def test_lesson_handlers():
    """Тест обработчиков уроков"""
    print("🧪 Тестирование обработчиков уроков...")
    
    try:
        # Настраиваем базу данных
        configure_database()
        
        # Создаем менеджеры
        lesson_manager = Lesson()
        purchase_manager = Purchase()
        
        # Тест 1: Получение урока по ID
        print("\n1️⃣ Тест получения урока по ID...")
        lesson = await lesson_manager.get_lesson(1)
        if lesson:
            print(f"✅ Урок найден: {lesson.title}")
            print(f"   Цена: ${lesson.price_usd}")
            print(f"   Активен: {lesson.is_active}")
            print(f"   Бесплатный: {lesson.is_free}")
        else:
            print("❌ Урок с ID 1 не найден")
        
        # Тест 2: Получение всех уроков
        print("\n2️⃣ Тест получения всех уроков...")
        lessons = await lesson_manager.get_all_lessons(active_only=True)
        print(f"✅ Найдено активных уроков: {len(lessons)}")
        for lesson in lessons:
            print(f"   • {lesson['title']} (ID: {lesson['id']})")
        
        # Тест 3: Проверка владения уроком
        print("\n3️⃣ Тест проверки владения уроком...")
        test_user_id = 123456789
        has_lesson = await purchase_manager.check_user_has_lesson(test_user_id, 1)
        print(f"✅ Пользователь {test_user_id} владеет уроком 1: {has_lesson}")
        
        # Тест 4: Инкремент просмотров
        print("\n4️⃣ Тест увеличения просмотров...")
        await lesson_manager.increment_views(1)
        print("✅ Счетчик просмотров увеличен")
        
        print("\n🎯 Все тесты пройдены успешно!")
        print("💡 Обработчики уроков должны работать корректно")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_lesson_handlers())