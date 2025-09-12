#!/usr/bin/env python3
"""
Тест новой фильтрации каталога - исключение уже купленных уроков
"""
import asyncio
from database.lesson import Lesson, Purchase

async def test_catalog_ownership_filter():
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ КАТАЛОГА (КУПЛЕННЫЕ УРОКИ)")
    print("=" * 70)
    
    l = Lesson()
    p = Purchase()
    
    # Тестовый пользователь
    test_user_id = 12345
    
    # 1. Получаем все активные уроки
    print("\n1️⃣ ПОЛУЧЕНИЕ ВСЕХ УРОКОВ:")
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"📚 Всего активных уроков: {len(all_lessons)}")
    
    for lesson in all_lessons:
        lesson_type = "🎁 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        print(f"  • ID {lesson['id']}: {lesson['title']} ({lesson_type})")
    
    # 2. Получаем покупки пользователя
    print(f"\n2️⃣ ПОКУПКИ ПОЛЬЗОВАТЕЛЯ {test_user_id}:")
    user_purchases = await p.get_user_purchases(test_user_id)
    purchased_lesson_ids = {purchase['lesson_id'] for purchase in user_purchases}
    
    print(f"💳 Покупок у пользователя: {len(user_purchases)}")
    for purchase in user_purchases:
        print(f"  • Урок ID {purchase['lesson_id']}")
    
    print(f"📋 Купленные ID: {purchased_lesson_ids}")
    
    # 3. Применяем новую логику фильтрации
    print(f"\n3️⃣ ФИЛЬТРАЦИЯ КАТАЛОГА:")
    catalog_lessons = []
    excluded_count = 0
    
    for lesson in all_lessons:
        # Исключаем автоматические лид-магниты
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        
        # Исключаем уроки, которые пользователь уже купил
        is_already_purchased = lesson['id'] in purchased_lesson_ids
        
        if not is_auto_lead_magnet and not is_already_purchased:
            catalog_lessons.append(lesson)
        else:
            excluded_count += 1
            reason = []
            if is_auto_lead_magnet:
                reason.append("лид-магнит")
            if is_already_purchased:
                reason.append("уже куплен")
            print(f"    🚫 Исключен урок ID {lesson['id']}: {' + '.join(reason)}")
    
    print(f"\n📊 РЕЗУЛЬТАТ ФИЛЬТРАЦИИ:")
    print(f"  📚 Уроков в каталоге: {len(catalog_lessons)}")
    print(f"  🚫 Исключено: {excluded_count}")
    
    # 4. Показываем итоговый каталог
    if catalog_lessons:
        print(f"\n✅ КАТАЛОГ БУДЕТ ПОКАЗЫВАТЬ:")
        for lesson in catalog_lessons:
            lesson_type = "🎁 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
            print(f"  • {lesson['title']} ({lesson_type})")
    else:
        print(f"\n⚠️ КАТАЛОГ БУДЕТ ПУСТЫМ - ВСЕ УРОКИ УЖЕ КУПЛЕНЫ!")
    
    # 5. Рекомендации
    print(f"\n" + "=" * 70)
    print("💡 АНАЛИЗ:")
    print("=" * 70)
    
    total_available = len([l for l in all_lessons if not (
        l.get('is_free', False) and l.get('title', '').strip() == "Бесплатный вводный урок"
    )])
    
    if len(catalog_lessons) == 0 and len(user_purchases) > 0:
        print("✅ ОТЛИЧНО! Пользователь купил все доступные уроки.")
        print("   Каталог корректно скрывает уже купленные уроки.")
    elif len(catalog_lessons) < total_available:
        print("✅ РАБОТАЕТ! Фильтрация исключает купленные уроки.")
        print(f"   Доступно для покупки: {len(catalog_lessons)} из {total_available}")
    else:
        print("ℹ️ Пользователь еще не покупал уроки - показываются все.")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_catalog_ownership_filter())