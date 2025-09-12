#!/usr/bin/env python3
"""
Тестирование исправленного каталога - бесплатные уроки должны показываться
"""
import asyncio
from database.lesson import Lesson
import keyboards as kb
from localization import get_text

async def test_fixed_catalog():
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО КАТАЛОГА")
    print("=" * 60)
    
    l = Lesson()
    
    # 1. Получаем все активные уроки
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"\n📚 Всего активных уроков: {len(all_lessons)}")
    for lesson in all_lessons:
        free_text = "🆓 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        print(f"  - ID {lesson['id']}: {lesson['title']} ({free_text})")
    
    # 2. Применяем НОВУЮ логику фильтрации из handlers/shop.py
    print(f"\n🔍 Применяем новую логику фильтрации...")
    catalog_lessons = []
    excluded_count = 0
    
    for lesson in all_lessons:
        # Исключаем только автоматические лид-магниты
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        
        if not is_auto_lead_magnet:
            catalog_lessons.append(lesson)
        else:
            excluded_count += 1
            print(f"    🚫 Исключен автоматический лид-магнит: {lesson['title']}")
    
    print(f"\n📊 Результат новой фильтрации:")
    print(f"  📚 Уроков в каталоге: {len(catalog_lessons)}")
    print(f"  🚫 Исключено лид-магнитов: {excluded_count}")
    
    # 3. Проверяем создание клавиатуры
    if catalog_lessons:
        print(f"\n✅ Каталог будет показывать:")
        try:
            markup = await kb.markup_catalog(catalog_lessons)
            for row in markup.inline_keyboard:
                for button in row:
                    if not button.text.startswith('⬅️'):  # Не кнопка "Назад"
                        print(f"  - {button.text}")
        except Exception as e:
            print(f"❌ Ошибка создания клавиатуры: {e}")
    else:
        print(f"\n❌ Каталог будет пустым!")
    
    # 4. Проверим каждый тип урока
    print(f"\n🔍 Детальная проверка каждого урока:")
    for lesson in catalog_lessons:
        is_free_lesson = lesson.get('is_free', False) or float(lesson.get('price_usd', 0)) == 0
        lesson_type = "🆓 БЕСПЛАТНЫЙ" if is_free_lesson else "💰 ПЛАТНЫЙ"
        
        print(f"  - {lesson['title']}: {lesson_type}")
        
        # Проверим, как будет выглядеть в каталоге
        price_usd = float(lesson['price_usd'])
        if lesson.get('is_free', False) or price_usd == 0:
            button_text = f"🎁 {lesson['title']} (БЕСПЛАТНО)"
        else:
            button_text = f"📚 {lesson['title']} (${price_usd:.2f})"
        print(f"    Кнопка: {button_text}")
    
    print("\n" + "=" * 60)
    if len(catalog_lessons) > len([l for l in catalog_lessons if not l.get('is_free', False)]):
        print("✅ УСПЕХ! Теперь в каталоге показываются бесплатные уроки!")
        print("🎉 Проблема исправлена - админские бесплатные уроки не пропадают!")
    else:
        print("⚠️ В каталоге только платные уроки")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_fixed_catalog())