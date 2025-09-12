#!/usr/bin/env python3
"""Check lessons in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import lesson
import asyncio

async def check_lessons():
    """Check all lessons in database"""
    l = lesson.Lesson()
    
    print("=" * 50)
    print("ПРОВЕРКА УРОКОВ В БАЗЕ ДАННЫХ")
    print("=" * 50)
    
    # Get all lessons (including inactive)
    all_lessons = await l.get_all_lessons(active_only=False)
    
    if not all_lessons:
        print("❌ В базе данных нет уроков")
        return
    
    print(f"\n📚 Всего уроков в БД: {len(all_lessons)}\n")
    
    for idx, lesson_data in enumerate(all_lessons, 1):
        print(f"{idx}. ID: {lesson_data.get('id')}")
        print(f"   Название: {lesson_data.get('title')}")
        print(f"   Цена USD: ${lesson_data.get('price_usd')}")
        print(f"   Бесплатный: {'✅ ДА' if lesson_data.get('is_free') else '❌ НЕТ'}")
        print(f"   Активен: {'✅ ДА' if lesson_data.get('is_active') else '❌ НЕТ'}")
        print(f"   Тип контента: {lesson_data.get('content_type')}")
        print(f"   Video ID: {lesson_data.get('video_file_id') or 'НЕТ'}")
        print("-" * 30)
    
    # Check active lessons only
    active_lessons = await l.get_all_lessons(active_only=True)
    print(f"\n✅ Активных уроков: {len(active_lessons)}")
    
    # Check free lessons
    free_lessons = [les for les in all_lessons if les.get('is_free')]
    print(f"🎁 Бесплатных уроков: {len(free_lessons)}")
    
    # Check paid lessons
    paid_lessons = [les for les in all_lessons if not les.get('is_free')]
    print(f"💰 Платных уроков: {len(paid_lessons)}")
    
    # Check what would be shown in catalog (paid active lessons)
    catalog_lessons = [les for les in active_lessons if not les.get('is_free')]
    print(f"\n📚 В КАТАЛОГЕ БУДЕТ ПОКАЗАНО: {len(catalog_lessons)} уроков")
    if catalog_lessons:
        for les in catalog_lessons:
            print(f"  - {les.get('title')} (${les.get('price_usd')})")

if __name__ == "__main__":
    asyncio.run(check_lessons())
