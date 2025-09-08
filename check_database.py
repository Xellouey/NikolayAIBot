"""
🔧 Скрипт для проверки и создания тестовых уроков в базе данных
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.lesson import Lesson, Purchase, SystemSettings
from database.sql import configure_database
from decimal import Decimal

async def check_database():
    """Проверка состояния базы данных"""
    print("🔍 Проверка базы данных...")
    
    try:
        # Настраиваем базу данных
        configure_database()
        print("✅ База данных настроена")
        
        # Создаем экземпляр класса Lesson
        lesson_manager = Lesson()
        
        # Получаем все уроки
        lessons = await lesson_manager.get_all_lessons(active_only=False)
        print(f"📚 Найдено уроков в базе: {len(lessons)}")
        
        if lessons:
            for lesson in lessons:
                status = "✅ Активен" if lesson['is_active'] else "❌ Неактивен"
                price_text = "🆓 Бесплатно" if lesson['is_free'] else f"💰 ${lesson['price_usd']}"
                print(f"  • ID: {lesson['id']} | {lesson['title']} | {status} | {price_text}")
        else:
            print("⚠️ Уроков в базе данных нет")
            
        return len(lessons)
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")
        return 0

async def create_test_lessons():
    """Создание тестовых уроков"""
    print("\n🛠️ Создание тестовых уроков...")
    
    try:
        lesson_manager = Lesson()
        
        # Создаем тестовые уроки
        test_lessons = [
            {
                'title': 'Бесплатный урок - Введение',
                'description': 'Бесплатный урок для знакомства с платформой',
                'price_usd': Decimal('0.00'),
                'is_free': True,
                'is_active': True,
                'content_type': 'text',
                'text_content': 'Добро пожаловать в наш курс! Это бесплатный урок.',
                'preview_text': 'В этом уроке вы познакомитесь с основами...'
            },
            {
                'title': 'Python для начинающих',
                'description': 'Изучите основы программирования на Python',
                'price_usd': Decimal('29.99'),
                'is_free': False,
                'is_active': True,
                'content_type': 'text',
                'text_content': 'Python - это мощный язык программирования...',
                'preview_text': 'Изучите переменные, циклы, функции и многое другое'
            },
            {
                'title': 'Веб-разработка с React',
                'description': 'Создавайте современные веб-приложения',
                'price_usd': Decimal('49.99'),
                'is_free': False,
                'is_active': True,
                'content_type': 'text', 
                'text_content': 'React - это библиотека для создания пользовательских интерфейсов...',
                'preview_text': 'Научитесь создавать компоненты, работать с состоянием и хуками'
            }
        ]
        
        created_count = 0
        for lesson_data in test_lessons:
            try:
                lesson = await lesson_manager.create_lesson(**lesson_data)
                print(f"✅ Создан урок: {lesson_data['title']}")
                created_count += 1
            except Exception as e:
                print(f"❌ Ошибка создания урока '{lesson_data['title']}': {e}")
        
        print(f"\n📚 Создано тестовых уроков: {created_count}")
        return created_count
        
    except Exception as e:
        print(f"❌ Ошибка создания тестовых уроков: {e}")
        return 0

async def main():
    """Основная функция"""
    print("🚀 Проверка и настройка базы данных для каталога уроков...")
    print("=" * 60)
    
    # Проверяем текущее состояние
    lesson_count = await check_database()
    
    # Если уроков нет, создаем тестовые
    if lesson_count == 0:
        created = await create_test_lessons()
        if created > 0:
            print("\n🔄 Повторная проверка базы данных...")
            await check_database()
    
    print("\n" + "=" * 60)
    print("🎯 База данных готова!")
    print("💡 Теперь попробуйте запустить бота и нажать на уроки в каталоге")

if __name__ == '__main__':
    asyncio.run(main())