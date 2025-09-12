#!/usr/bin/env python3
"""
Тест обработчика view_lesson: для просмотра купленных уроков
"""
import asyncio
from database.lesson import Lesson, Purchase

async def test_view_lesson_handler():
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТЧИКА view_lesson:")
    print("=" * 60)
    
    l = Lesson()
    p = Purchase()
    
    # 1. Проверяем наличие уроков в базе
    print("\n1️⃣ ПРОВЕРКА УРОКОВ В БАЗЕ:")
    all_lessons = await l.get_all_lessons(active_only=False)
    print(f"Всего уроков в базе: {len(all_lessons)}")
    
    for lesson in all_lessons:
        print(f"  • ID {lesson['id']}: {lesson['title']}")
        print(f"    - Активен: {lesson.get('is_active', 'N/A')}")
        print(f"    - Бесплатный: {lesson.get('is_free', 'N/A')}")
        print(f"    - Цена: ${lesson.get('price_usd', 'N/A')}")
        
        # Получаем детальную информацию
        lesson_obj = await l.get_lesson(lesson['id'])
        if lesson_obj:
            print(f"    - content_type: {lesson_obj.content_type}")
            print(f"    - video_file_id: {'Есть' if lesson_obj.video_file_id else 'Нет'}")
            print(f"    - text_content: {'Есть' if lesson_obj.text_content else 'Нет'}")
            print(f"    - description: {'Есть' if lesson_obj.description else 'Нет'}")
        else:
            print(f"    ❌ Не удалось получить детали урока!")
        print()
    
    # 2. Проверяем покупки тестового пользователя
    test_user_id = 12345
    print(f"\n2️⃣ ПРОВЕРКА ПОКУПОК ПОЛЬЗОВАТЕЛЯ {test_user_id}:")
    
    user_purchases = await p.get_user_purchases(test_user_id)
    print(f"Покупок у пользователя: {len(user_purchases)}")
    
    for purchase in user_purchases:
        print(f"  • Урок ID {purchase['lesson_id']}: ${purchase.get('price_paid_usd', 0)}")
    
    # 3. Проверяем доступ к урокам
    print(f"\n3️⃣ ПРОВЕРКА ДОСТУПА К УРОКАМ:")
    
    for lesson in all_lessons:
        lesson_id = lesson['id']
        has_access = await p.check_user_has_lesson(test_user_id, lesson_id)
        access_text = "✅ Есть доступ" if has_access else "❌ Нет доступа"
        print(f"  • Урок {lesson_id} '{lesson['title']}': {access_text}")
    
    # 4. Симуляция callback данных
    print(f"\n4️⃣ СИМУЛЯЦИЯ CALLBACK ДАННЫХ:")
    
    for lesson in all_lessons:
        lesson_id = lesson['id']
        callback_data = f"view_lesson:{lesson_id}"
        print(f"  • Callback: {callback_data}")
        
        # Проверяем парсинг
        if ':' in callback_data:
            lesson_id_str = callback_data.split(':')[1]
            try:
                parsed_id = int(lesson_id_str)
                print(f"    ✅ Парсинг успешен: {parsed_id}")
            except ValueError as e:
                print(f"    ❌ Ошибка парсинга: {e}")
        else:
            print(f"    ❌ Неверный формат callback")
    
    # 5. Рекомендации
    print(f"\n" + "=" * 60)
    print("💡 РЕКОМЕНДАЦИИ ДЛЯ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    if len(all_lessons) == 0:
        print("❌ Нет уроков в базе - нужно создать тестовые уроки")
    elif len(user_purchases) == 0:
        print("⚠️ У тестового пользователя нет покупок")
        print("🔧 Чтобы протестировать просмотр урока:")
        print("   1. Купите один из бесплатных уроков в боте")
        print("   2. Или добавьте покупку в базу вручную")
    else:
        print("✅ Готово к тестированию!")
        print("🤖 Попробуйте нажать на урок в разделе 'Мои уроки' в боте")
        print("📝 Проверьте логи в консоли - они должны показать подробную информацию")
    
    print(f"\n🔍 ЧТО ИСКАТЬ В ЛОГАХ:")
    print(f"   • 🔍 VIEW_LESSON: Начало обработки callback: view_lesson:X")
    print(f"   • 🔍 VIEW_LESSON: Получение данных урока ID X...")
    print(f"   • ✅ VIEW_LESSON: Урок найден: 'Название урока'")
    print(f"   • 🔍 VIEW_LESSON: content_type: video/text")
    print(f"   • 🔍 VIEW_LESSON: Пользователь владеет уроком: True/False")
    print(f"   • ✅ VIEW_LESSON: Обработка завершена успешно")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_view_lesson_handler())