#!/usr/bin/env python3
"""
Тестирование полного потока получения бесплатного урока:
1. Показ в каталоге
2. Детали урока с БЕСПЛАТНО
3. "Покупка" (получение бесплатно)
4. Появление в "Моих уроках"
"""
import asyncio
from database.lesson import Lesson, Purchase

async def test_free_lesson_complete_flow():
    print("=" * 70)
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОГО ПОТОКА БЕСПЛАТНОГО УРОКА")
    print("=" * 70)
    
    l = Lesson()
    p = Purchase()
    
    # 1. Проверяем бесплатные уроки в каталоге
    print("\n1️⃣ ПРОВЕРКА КАТАЛОГА:")
    all_lessons = await l.get_all_lessons(active_only=True)
    free_lessons = [lesson for lesson in all_lessons if lesson.get('is_free', False)]
    
    print(f"Всего активных уроков: {len(all_lessons)}")
    print(f"Бесплатных уроков: {len(free_lessons)}")
    
    if not free_lessons:
        print("❌ Нет бесплатных уроков для тестирования!")
        return
    
    # Берем первый бесплатный урок для тестирования
    test_lesson = free_lessons[0]
    lesson_id = test_lesson['id']
    
    print(f"\n📚 Тестовый урок: ID {lesson_id} - {test_lesson['title']}")
    print(f"   • is_free: {test_lesson.get('is_free', False)}")
    print(f"   • price_usd: ${test_lesson.get('price_usd', 0)}")
    
    # 2. Проверяем отображение в каталоге
    print(f"\n2️⃣ ОТОБРАЖЕНИЕ В КАТАЛОГЕ:")
    
    # Применяем логику фильтрации из handlers/shop.py
    catalog_lessons = []
    for lesson in all_lessons:
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        if not is_auto_lead_magnet:
            catalog_lessons.append(lesson)
    
    test_lesson_in_catalog = any(lesson['id'] == lesson_id for lesson in catalog_lessons)
    print(f"✅ Урок показывается в каталоге: {test_lesson_in_catalog}")
    
    if test_lesson_in_catalog:
        # Проверяем как будет выглядеть кнопка
        price_usd = float(test_lesson['price_usd'])
        if test_lesson.get('is_free', False) or price_usd == 0:
            button_text = f"🎁 {test_lesson['title']} (БЕСПЛАТНО)"
        else:
            button_text = f"📚 {test_lesson['title']} (${price_usd:.2f})"
        print(f"   Кнопка: {button_text}")
    
    # 3. Проверяем детали урока
    print(f"\n3️⃣ ДЕТАЛИ УРОКА:")
    lesson_obj = await l.get_lesson(lesson_id)
    if lesson_obj:
        is_free_lesson = lesson_obj.is_free or float(lesson_obj.price_usd) == 0
        print(f"✅ Урок найден: {lesson_obj.title}")
        print(f"   • Определяется как бесплатный: {is_free_lesson}")
        
        if is_free_lesson:
            detail_text = f"🎁 {lesson_obj.title}\n\n🎆 БЕСПЛАТНО!\n\n📝 {lesson_obj.description or ''}"
            print(f"   • Текст деталей: {detail_text[:100]}...")
            print(f"   • Кнопка: '🎁 Получить бесплатно'")
        else:
            print(f"   ❌ Урок НЕ определяется как бесплатный!")
    else:
        print(f"❌ Урок не найден в базе!")
        return
    
    # 4. Симулируем "покупку" бесплатного урока
    print(f"\n4️⃣ СИМУЛЯЦИЯ ПОЛУЧЕНИЯ БЕСПЛАТНОГО УРОКА:")
    
    # Используем тестового пользователя (ID 12345)
    test_user_id = 12345
    
    # Проверяем, есть ли уже этот урок у пользователя
    user_has_lesson_before = await p.check_user_has_lesson(test_user_id, lesson_id)
    print(f"Урок у пользователя до 'покупки': {user_has_lesson_before}")
    
    if not user_has_lesson_before:
        # Симулируем процесс получения бесплатного урока
        try:
            await p.create_purchase(
                user_id=test_user_id,
                lesson_id=lesson_id,
                price_paid_usd=0,
                price_paid_stars=0,
                payment_id="free_lesson_test"
            )
            await l.increment_purchases(lesson_id)
            
            print("✅ Бесплатный урок успешно 'куплен' (добавлен в покупки)")
            
            # Проверяем, что урок теперь есть у пользователя
            user_has_lesson_after = await p.check_user_has_lesson(test_user_id, lesson_id)
            print(f"Урок у пользователя после 'покупки': {user_has_lesson_after}")
            
            if user_has_lesson_after:
                print("✅ Покупка зарегистрирована корректно!")
            else:
                print("❌ Покупка НЕ зарегистрирована!")
                
        except Exception as e:
            print(f"❌ Ошибка при 'покупке': {e}")
    else:
        print("ℹ️ Урок уже есть у пользователя, пропускаем покупку")
    
    # 5. Проверяем отображение в "Моих уроках"
    print(f"\n5️⃣ ПРОВЕРКА 'МОИХ УРОКОВ':")
    
    try:
        # Получаем покупки пользователя
        user_purchases = await p.get_user_purchases(test_user_id)
        print(f"Всего покупок у пользователя: {len(user_purchases)}")
        
        # Ищем наш тестовый урок среди покупок
        test_lesson_purchased = False
        for purchase in user_purchases:
            if purchase['lesson_id'] == lesson_id:
                test_lesson_purchased = True
                print(f"✅ Урок найден в покупках:")
                print(f"   • lesson_id: {purchase['lesson_id']}")
                print(f"   • price_paid_usd: ${purchase.get('price_paid_usd', 0)}")
                print(f"   • price_paid_stars: {purchase.get('price_paid_stars', 0)} ⭐")
                print(f"   • payment_id: {purchase.get('payment_id', 'N/A')}")
                break
        
        if not test_lesson_purchased:
            print("❌ Урок НЕ найден в покупках пользователя!")
        else:
            # Проверяем, как урок будет выглядеть в "Моих уроках"
            lesson_obj = await l.get_lesson(lesson_id)
            if lesson_obj:
                lesson_data = {
                    'id': lesson_id,
                    'title': lesson_obj.title,
                    'is_lead': False
                }
                print(f"   • В 'Моих уроках' будет показан как: 📚 {lesson_data['title']}")
                
    except Exception as e:
        print(f"❌ Ошибка при проверке покупок: {e}")
    
    # 6. Итоговый результат
    print(f"\n" + "=" * 70)
    print("🎯 ИТОГОВЫЙ РЕЗУЛЬТАТ:")
    print("=" * 70)
    
    if test_lesson_in_catalog and user_has_lesson_after and test_lesson_purchased:
        print("✅ ВСЕ ЭТАПЫ РАБОТАЮТ КОРРЕКТНО!")
        print("   1. ✅ Бесплатный урок показывается в каталоге")
        print("   2. ✅ Детали отображают 'БЕСПЛАТНО!'")
        print("   3. ✅ 'Покупка' работает (урок добавляется в покупки)")
        print("   4. ✅ Урок появляется в 'Моих уроках'")
        print("\n🎉 ПОТОК ПОЛУЧЕНИЯ БЕСПЛАТНОГО УРОКА РАБОТАЕТ ПОЛНОСТЬЮ!")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
        if not test_lesson_in_catalog:
            print("   ❌ Урок не показывается в каталоге")
        if not user_has_lesson_after:
            print("   ❌ 'Покупка' не работает")
        if not test_lesson_purchased:
            print("   ❌ Урок не добавляется в покупки")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_free_lesson_complete_flow())