#!/usr/bin/env python3
"""
Тест каталога для пользователя без покупок
"""
import asyncio
from database.lesson import Lesson, Purchase

async def test_catalog_for_new_user():
    print("=" * 60)
    print("🧪 КАТАЛОГ ДЛЯ НОВОГО ПОЛЬЗОВАТЕЛЯ (БЕЗ ПОКУПОК)")
    print("=" * 60)
    
    l = Lesson()
    p = Purchase()
    
    # Новый пользователь без покупок
    new_user_id = 99999
    
    # 1. Получаем все активные уроки
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"\n📚 Всего активных уроков: {len(all_lessons)}")
    
    # 2. Получаем покупки нового пользователя (должно быть 0)
    user_purchases = await p.get_user_purchases(new_user_id)
    purchased_lesson_ids = {purchase['lesson_id'] for purchase in user_purchases}
    
    print(f"💳 Покупок у нового пользователя: {len(user_purchases)}")
    
    # 3. Применяем фильтрацию
    catalog_lessons = []
    for lesson in all_lessons:
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        is_already_purchased = lesson['id'] in purchased_lesson_ids
        
        if not is_auto_lead_magnet and not is_already_purchased:
            catalog_lessons.append(lesson)
    
    print(f"\n✅ КАТАЛОГ ДЛЯ НОВОГО ПОЛЬЗОВАТЕЛЯ:")
    print(f"   Доступно уроков: {len(catalog_lessons)}")
    
    for lesson in catalog_lessons:
        lesson_type = "🎁 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        print(f"   • {lesson['title']} ({lesson_type})")
    
    # 4. Сравнение с пользователем, который что-то купил
    experienced_user_id = 12345
    experienced_purchases = await p.get_user_purchases(experienced_user_id)
    experienced_purchased_ids = {p['lesson_id'] for p in experienced_purchases}
    
    experienced_catalog = []
    for lesson in all_lessons:
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        is_already_purchased = lesson['id'] in experienced_purchased_ids
        
        if not is_auto_lead_magnet and not is_already_purchased:
            experienced_catalog.append(lesson)
    
    print(f"\n📊 СРАВНЕНИЕ:")
    print(f"   Новый пользователь видит: {len(catalog_lessons)} уроков")
    print(f"   Опытный пользователь видит: {len(experienced_catalog)} уроков")
    print(f"   Разница: {len(catalog_lessons) - len(experienced_catalog)} уроков")
    
    if len(catalog_lessons) > len(experienced_catalog):
        print("   ✅ Система работает! Новый пользователь видит больше уроков.")
    elif len(catalog_lessons) == len(experienced_catalog):
        print("   ℹ️ Опытный пользователь еще не купил дополнительные уроки.")
    else:
        print("   ❌ Что-то не так с логикой!")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_catalog_for_new_user())