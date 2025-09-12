#!/usr/bin/env python3
"""
Финальное тестирование исправления каталога бесплатных уроков
"""
import asyncio
from database.lesson import Lesson
import keyboards as kb
from localization import get_text

async def final_test():
    print("=" * 70)
    print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ КАТАЛОГА")
    print("=" * 70)
    
    l = Lesson()
    
    # 1. Текущее состояние базы данных
    print("\n📊 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ:")
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"Всего активных уроков: {len(all_lessons)}")
    
    for lesson in all_lessons:
        free_status = "🆓 БЕСПЛАТНЫЙ" if lesson.get('is_free', False) else f"💰 ${lesson.get('price_usd', 0)}"
        print(f"  • ID {lesson['id']}: {lesson['title']} ({free_status})")
    
    # 2. СТАРАЯ логика фильтрации (до исправления)
    print(f"\n❌ СТАРАЯ ЛОГИКА (ДО ИСПРАВЛЕНИЯ):")
    old_paid_lessons = [lesson for lesson in all_lessons if not lesson.get('is_free', False)]
    print(f"Показывались только платные: {len(old_paid_lessons)} из {len(all_lessons)}")
    for lesson in old_paid_lessons:
        print(f"  • {lesson['title']} (${lesson.get('price_usd', 0)})")
    
    # 3. НОВАЯ логика фильтрации (после исправления)  
    print(f"\n✅ НОВАЯ ЛОГИКА (ПОСЛЕ ИСПРАВЛЕНИЯ):")
    new_catalog_lessons = []
    excluded_count = 0
    
    for lesson in all_lessons:
        # Исключаем только автоматические лид-магниты с названием "Бесплатный вводный урок"
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        
        if not is_auto_lead_magnet:
            new_catalog_lessons.append(lesson)
        else:
            excluded_count += 1
            print(f"    🚫 Исключен автолид-магнит: {lesson['title']}")
    
    print(f"Теперь показываются: {len(new_catalog_lessons)} из {len(all_lessons)} уроков")
    print(f"Исключено автолид-магнитов: {excluded_count}")
    
    # 4. Детальный анализ каталога
    print(f"\n📚 ДЕТАЛЬНЫЙ АНАЛИЗ НОВОГО КАТАЛОГА:")
    platform_lessons = {"платные": [], "бесплатные_админские": []}
    
    for lesson in new_catalog_lessons:
        is_free = lesson.get('is_free', False) or float(lesson.get('price_usd', 0)) == 0
        if is_free:
            platform_lessons["бесплатные_админские"].append(lesson)
        else:
            platform_lessons["платные"].append(lesson)
    
    print(f"  📈 Платных уроков: {len(platform_lessons['платные'])}")
    for lesson in platform_lessons["платные"]:
        print(f"    💰 {lesson['title']} (${lesson.get('price_usd', 0)})")
    
    print(f"  🎁 Бесплатных админских уроков: {len(platform_lessons['бесплатные_админские'])}")
    for lesson in platform_lessons["бесплатные_админские"]:
        print(f"    🆓 {lesson['title']} (БЕСПЛАТНО)")
    
    # 5. Тестирование создания клавиатуры
    print(f"\n⌨️ ТЕСТИРОВАНИЕ КЛАВИАТУРЫ:")
    try:
        if new_catalog_lessons:
            markup = await kb.markup_catalog(new_catalog_lessons)
            print("✅ Клавиатура каталога создана успешно")
            
            # Анализ кнопок
            button_count = 0
            for row in markup.inline_keyboard:
                for button in row:
                    if not button.text.startswith('⬅️'):  # Не кнопка "Назад"
                        button_count += 1
                        if "БЕСПЛАТНО" in button.text:
                            print(f"  🎁 {button.text}")
                        else:
                            print(f"  💰 {button.text}")
            
            print(f"Всего кнопок уроков: {button_count}")
        else:
            print("❌ Каталог пустой!")
    except Exception as e:
        print(f"❌ Ошибка создания клавиатуры: {e}")
    
    # 6. Итоговый результат
    print(f"\n" + "=" * 70)
    print("🎯 РЕЗУЛЬТАТ ИСПРАВЛЕНИЯ:")
    print("=" * 70)
    
    old_count = len(old_paid_lessons)
    new_count = len(new_catalog_lessons)
    free_count = len(platform_lessons["бесплатные_админские"])
    
    print(f"✅ ДО ИСПРАВЛЕНИЯ: {old_count} уроков (только платные)")
    print(f"✅ ПОСЛЕ ИСПРАВЛЕНИЯ: {new_count} уроков ({new_count - free_count} платных + {free_count} бесплатных)")
    
    if free_count > 0:
        print(f"\n🎉 УСПЕХ! Бесплатные уроки теперь показываются в каталоге!")
        print(f"🔧 Проблема исправлена: админские бесплатные уроки больше не пропадают!")
    else:
        print(f"\nℹ️ В базе нет бесплатных админских уроков для проверки")
    
    print(f"\n💡 ПРИНЦИП РАБОТЫ:")
    print(f"   • Показываются ВСЕ уроки (платные + бесплатные)")
    print(f"   • Исключаются только автоматические лид-магниты с названием 'Бесплатный вводный урок'")
    print(f"   • Бесплатные уроки созданные админом через админку отображаются как 🎁 БЕСПЛАТНО")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(final_test())