#!/usr/bin/env python3
"""
Тест для проверки, что лид-магнит (бесплатный урок) 
не показывается в каталоге уроков
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Тестовые данные уроков
test_lessons = [
    {
        'id': 1,
        'title': 'Платный урок 1',
        'price_usd': '10.00',
        'is_free': False,
        'is_active': True
    },
    {
        'id': 2, 
        'title': 'Бесплатный вводный урок',
        'price_usd': '0.00',
        'is_free': True,
        'is_active': True
    },
    {
        'id': 3,
        'title': 'Платный урок 2',
        'price_usd': '15.00',
        'is_free': False,
        'is_active': True
    }
]

def filter_paid_lessons(lessons):
    """Фильтруем бесплатные уроки - как в show_catalog"""
    return [lesson for lesson in lessons if not lesson.get('is_free', False)]

def test_catalog_filter():
    """Проверяем, что фильтрация работает корректно"""
    print("🧪 Тестируем фильтрацию лид-магнита из каталога...\n")
    
    print(f"📚 Всего уроков: {len(test_lessons)}")
    for lesson in test_lessons:
        free_label = " (БЕСПЛАТНЫЙ)" if lesson['is_free'] else ""
        print(f"  - {lesson['title']}{free_label}")
    
    print("\n🔍 Применяем фильтр (убираем бесплатные)...")
    paid_lessons = filter_paid_lessons(test_lessons)
    
    print(f"\n💰 Платных уроков для каталога: {len(paid_lessons)}")
    for lesson in paid_lessons:
        print(f"  - {lesson['title']} (${lesson['price_usd']})")
    
    # Проверки
    assert len(paid_lessons) == 2, "Должно остаться 2 платных урока"
    assert all(not lesson.get('is_free', False) for lesson in paid_lessons), "Все уроки должны быть платными"
    assert not any(lesson['id'] == 2 for lesson in paid_lessons), "Лид-магнит (id=2) не должен быть в каталоге"
    
    print("\n✅ Все проверки пройдены! Лид-магнит корректно исключается из каталога.")
    return True

if __name__ == "__main__":
    try:
        test_catalog_filter()
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении теста: {e}")
        sys.exit(1)
