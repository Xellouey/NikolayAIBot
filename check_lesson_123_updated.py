#!/usr/bin/env python3
"""
Проверка обновленного урока "123" после изменений админа
"""
import asyncio
from database.lesson import Lesson

async def check_updated_lesson_123():
    print("=" * 60)
    print("🔍 ПРОВЕРКА ОБНОВЛЕННОГО УРОКА '123'")
    print("=" * 60)
    
    l = Lesson()
    
    # Получаем данные урока ID 5
    lesson_data = await l.get_lesson(5)
    
    if not lesson_data:
        print("❌ Урок ID 5 не найден!")
        return
    
    print(f"\n📚 АКТУАЛЬНЫЕ ДАННЫЕ УРОКА:")
    print(f"   • ID: {lesson_data.id}")
    print(f"   • Название: '{lesson_data.title}'")
    print(f"   • ОПИСАНИЕ (description): '{lesson_data.description or 'НЕТ'}'")
    print(f"   • СОДЕРЖИМОЕ (text_content): '{lesson_data.text_content or 'НЕТ'}'")
    print(f"   • content_type: {lesson_data.content_type}")
    print(f"   • video_file_id: {lesson_data.video_file_id or 'НЕТ'}")
    print(f"   • is_free: {lesson_data.is_free}")
    print(f"   • is_active: {lesson_data.is_active}")
    
    print(f"\n🎯 АНАЛИЗ ПРОБЛЕМЫ:")
    print(f"✅ description (описание): {'ЕСТЬ' if lesson_data.description else 'НЕТ'}")
    print(f"❌ text_content (содержимое): {'ЕСТЬ' if lesson_data.text_content else 'НЕТ'}")
    
    print(f"\n💡 ОБЪЯСНЕНИЕ:")
    print("description - это краткое описание урока (что это за урок)")
    print("text_content - это само содержимое урока (материалы для изучения)")
    
    print(f"\n🔧 ВАРИАНТЫ РЕШЕНИЯ:")
    print("1. Добавить text_content через админ-панель")
    print("2. Изменить логику - показывать description как содержимое")
    print("3. Добавить видео к уроку")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_updated_lesson_123())