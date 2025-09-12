#!/usr/bin/env python3
"""
Исправление каталога - бесплатные уроки должны показываться в каталоге.
Исключаем только автоматически созданные лид-магниты.
"""
import asyncio
from database.lesson import Lesson

async def activate_lessons():
    """Активируем все неактивные уроки"""
    print("🔧 Активация неактивных уроков...")
    
    l = Lesson()
    all_lessons = await l.get_all_lessons(active_only=False)
    
    inactive_count = 0
    for lesson in all_lessons:
        if not lesson.get('is_active', True):
            success = await l.update_lesson(lesson['id'], is_active=True)
            if success:
                print(f"  ✅ Активирован урок ID {lesson['id']}: {lesson['title']}")
                inactive_count += 1
            else:
                print(f"  ❌ Ошибка активации урока ID {lesson['id']}")
    
    print(f"✅ Активировано уроков: {inactive_count}")
    return inactive_count

async def test_catalog_filtering():
    """Тестируем новую логику фильтрации каталога"""
    print("\n🧪 Тестирование логики фильтрации каталога...")
    
    l = Lesson()
    all_lessons = await l.get_all_lessons(active_only=True)
    
    print(f"📚 Всего активных уроков: {len(all_lessons)}")
    for lesson in all_lessons:
        free_text = "🆓 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        print(f"  - ID {lesson['id']}: {lesson['title']} ({free_text})")
    
    # Новая логика фильтрации: исключаем только автоматические лид-магниты
    # Лид-магнит имеет специальное название "Бесплатный вводный урок"
    catalog_lessons = []
    excluded_count = 0
    
    for lesson in all_lessons:
        # Исключаем автоматически созданные лид-магниты
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        
        if not is_auto_lead_magnet:
            catalog_lessons.append(lesson)
        else:
            excluded_count += 1
            print(f"    🚫 Исключен автоматический лид-магнит: {lesson['title']}")
    
    print(f"\n📊 Результат фильтрации:")
    print(f"  📚 Уроков в каталоге: {len(catalog_lessons)}")
    print(f"  🚫 Исключено лид-магнитов: {excluded_count}")
    
    if catalog_lessons:
        print(f"\n✅ Каталог будет показывать:")
        for lesson in catalog_lessons:
            free_text = "🆓 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
            print(f"  - {lesson['title']} ({free_text})")
    else:
        print(f"\n❌ Каталог будет пустым!")
    
    return catalog_lessons

async def main():
    print("=" * 60)
    print("🔧 ИСПРАВЛЕНИЕ КАТАЛОГА БЕСПЛАТНЫХ УРОКОВ")
    print("=" * 60)
    
    # 1. Активируем уроки
    await activate_lessons()
    
    # 2. Тестируем фильтрацию
    await test_catalog_filtering()
    
    print("\n" + "=" * 60)
    print("✅ Исправление завершено!")
    print("💡 Теперь нужно обновить код фильтрации в handlers/shop.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())