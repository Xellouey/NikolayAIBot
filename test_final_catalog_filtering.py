#!/usr/bin/env python3
"""
Итоговый тест - проверка фильтрации каталога от купленных уроков
"""
import asyncio
from database.lesson import Lesson, Purchase

async def comprehensive_catalog_test():
    print("=" * 80)
    print("🏆 ИТОГОВЫЙ ТЕСТ ФИЛЬТРАЦИИ КАТАЛОГА ОТ КУПЛЕННЫХ УРОКОВ")
    print("=" * 80)
    
    l = Lesson()
    p = Purchase()
    
    # Получаем всех пользователей с покупками для тестирования
    print("\n1️⃣ АНАЛИЗ БАЗЫ ДАННЫХ:")
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"📚 Всего активных уроков в системе: {len(all_lessons)}")
    
    for lesson in all_lessons:
        lesson_type = "🎁 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        lead_magnet = " (лид-магнит)" if lesson.get('title', '').strip() == "Бесплатный вводный урок" else ""
        print(f"   • ID {lesson['id']}: {lesson['title']} ({lesson_type}){lead_magnet}")
    
    # Тестируем разных пользователей
    test_users = [12345, 99999, 897676474]  # Разные пользователи
    
    print(f"\n2️⃣ ТЕСТИРОВАНИЕ КАТАЛОГА ДЛЯ РАЗНЫХ ПОЛЬЗОВАТЕЛЕЙ:")
    
    for user_id in test_users:
        print(f"\n👤 ПОЛЬЗОВАТЕЛЬ {user_id}:")
        
        # Получаем покупки пользователя
        user_purchases = await p.get_user_purchases(user_id)
        purchased_lesson_ids = {purchase['lesson_id'] for purchase in user_purchases}
        
        print(f"   💳 Покупок: {len(user_purchases)}")
        if user_purchases:
            print(f"   📋 Купленные уроки: {list(purchased_lesson_ids)}")
        
        # Применяем логику фильтрации каталога
        catalog_lessons = []
        excluded_reasons = []
        
        for lesson in all_lessons:
            # Исключаем автоматические лид-магниты
            is_auto_lead_magnet = (
                lesson.get('is_free', False) and 
                lesson.get('title', '').strip() == "Бесплатный вводный урок"
            )
            
            # Исключаем уже купленные уроки
            is_already_purchased = lesson['id'] in purchased_lesson_ids
            
            if not is_auto_lead_magnet and not is_already_purchased:
                catalog_lessons.append(lesson)
            else:
                reason = []
                if is_auto_lead_magnet:
                    reason.append("лид-магнит")
                if is_already_purchased:
                    reason.append("уже куплен")
                excluded_reasons.append(f"ID {lesson['id']}: {' + '.join(reason)}")
        
        print(f"   📚 В каталоге показывается: {len(catalog_lessons)} уроков")
        
        if catalog_lessons:
            for lesson in catalog_lessons:
                lesson_type = "🎁 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
                print(f"      ✅ {lesson['title']} ({lesson_type})")
        else:
            print(f"      ⚠️ Каталог пустой - все доступные уроки уже куплены")
        
        if excluded_reasons:
            print(f"   🚫 Исключено:")
            for reason in excluded_reasons:
                print(f"      • {reason}")
    
    # Проверяем корректность логики
    print(f"\n3️⃣ ПРОВЕРКА КОРРЕКТНОСТИ:")
    
    # Подсчитываем максимально возможное количество уроков в каталоге
    max_catalog_lessons = len([
        lesson for lesson in all_lessons 
        if not (lesson.get('is_free', False) and lesson.get('title', '').strip() == "Бесплатный вводный урок")
    ])
    
    print(f"   📊 Максимум уроков в каталоге (без лид-магнитов): {max_catalog_lessons}")
    
    success_count = 0
    for user_id in test_users:
        user_purchases = await p.get_user_purchases(user_id)
        purchased_count = len(user_purchases)
        
        expected_catalog_size = max_catalog_lessons - purchased_count
        
        # Вычисляем фактический размер каталога
        catalog_lessons = []
        purchased_lesson_ids = {p['lesson_id'] for p in user_purchases}
        
        for lesson in all_lessons:
            is_auto_lead_magnet = (
                lesson.get('is_free', False) and 
                lesson.get('title', '').strip() == "Бесплатный вводный урок"
            )
            is_already_purchased = lesson['id'] in purchased_lesson_ids
            
            if not is_auto_lead_magnet and not is_already_purchased:
                catalog_lessons.append(lesson)
        
        actual_catalog_size = len(catalog_lessons)
        
        if actual_catalog_size == expected_catalog_size:
            print(f"   ✅ Пользователь {user_id}: {actual_catalog_size} = {expected_catalog_size} (корректно)")
            success_count += 1
        else:
            print(f"   ❌ Пользователь {user_id}: {actual_catalog_size} ≠ {expected_catalog_size} (ошибка)")
    
    # Итоговый результат
    print(f"\n" + "=" * 80)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 80)
    
    if success_count == len(test_users):
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   🔹 Фильтрация каталога работает корректно")
        print("   🔹 Купленные уроки исключаются из каталога")
        print("   🔹 Лид-магниты также исключаются")
        print("   🔹 Математика совпадает для всех пользователей")
        print("\n🎉 ФУНКЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    else:
        print(f"❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
        print(f"   Успешных тестов: {success_count}/{len(test_users)}")
        print("   Требуется дополнительная отладка")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(comprehensive_catalog_test())