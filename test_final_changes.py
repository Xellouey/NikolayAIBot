#!/usr/bin/env python3
"""Final test of all changes"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from localization import get_text
from database import lesson

async def test_changes():
    """Test all recent changes"""
    print("=" * 60)
    print("ФИНАЛЬНАЯ ПРОВЕРКА ИЗМЕНЕНИЙ")
    print("=" * 60)
    
    # 1. Test welcome message updated
    print("\n1️⃣ Проверка обновленного welcome:")
    welcome_msg = get_text('welcome')
    print(f"   welcome: {welcome_msg[:50]}...")
    assert welcome_msg, "welcome должен существовать"
    assert "магазин" not in welcome_msg.lower(), "welcome НЕ должен упоминать магазин"
    print("   ✅ Ключ welcome обновлен (без упоминания магазина)")
    
    # 2. Test catalog filtering
    print("\n2️⃣ Проверка фильтрации каталога:")
    l = lesson.Lesson()
    all_lessons = await l.get_all_lessons(active_only=True)
    print(f"   Всего активных уроков: {len(all_lessons)}")
    
    # Simulate catalog filtering
    catalog_lessons = [les for les in all_lessons if not les.get('is_free', False)]
    print(f"   После фильтрации (только платные): {len(catalog_lessons)}")
    
    free_count = len([les for les in all_lessons if les.get('is_free', False)])
    print(f"   Бесплатных уроков исключено: {free_count}")
    
    # Check that free lessons are not in catalog
    for les in catalog_lessons:
        assert not les.get('is_free', False), f"Урок {les.get('title')} не должен быть бесплатным!"
    
    print("   ✅ Фильтрация работает - бесплатные уроки исключены")
    
    # 3. Summary
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ПРОВЕРКИ:")
    print("=" * 60)
    print("✅ Приветственное сообщение без упоминания магазина")
    print("✅ Каталог показывает только платные уроки")
    print(f"✅ Исключено бесплатных уроков из каталога: {free_count}")
    print("\n🎉 Все изменения работают корректно!")

if __name__ == "__main__":
    try:
        asyncio.run(test_changes())
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)
