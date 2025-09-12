#!/usr/bin/env python3
"""
Диагностика урока "123" - почему показывается "Содержимое урока не доступно"
"""
import asyncio
from database.lesson import Lesson

async def diagnose_lesson_123():
    print("=" * 60)
    print("🔍 ДИАГНОСТИКА УРОКА '123' (ID 5)")
    print("=" * 60)
    
    l = Lesson()
    
    # Получаем данные урока ID 5
    lesson_data = await l.get_lesson(5)
    
    if not lesson_data:
        print("❌ Урок ID 5 не найден!")
        return
    
    print(f"\n📚 ДАННЫЕ УРОКА:")
    print(f"   • ID: {lesson_data.id}")
    print(f"   • Название: {lesson_data.title}")
    print(f"   • Описание: {lesson_data.description or 'НЕТ'}")
    print(f"   • content_type: {lesson_data.content_type}")
    print(f"   • video_file_id: {lesson_data.video_file_id or 'НЕТ'}")
    print(f"   • text_content: {lesson_data.text_content or 'НЕТ'}")
    print(f"   • is_free: {lesson_data.is_free}")
    print(f"   • is_active: {lesson_data.is_active}")
    
    print(f"\n🔍 АНАЛИЗ ЛОГИКИ ОТОБРАЖЕНИЯ:")
    
    # Проверяем условие для видео
    has_video = lesson_data.content_type == 'video' and lesson_data.video_file_id
    print(f"   • Имеет видео: {has_video}")
    if not has_video:
        if lesson_data.content_type != 'video':
            print(f"     - content_type не 'video' (текущий: '{lesson_data.content_type}')")
        if not lesson_data.video_file_id:
            print(f"     - video_file_id отсутствует")
    
    # Проверяем текстовое содержимое
    has_text = bool(lesson_data.text_content)
    print(f"   • Имеет текст: {has_text}")
    if not has_text:
        print(f"     - text_content пустой или отсутствует")
    
    print(f"\n💡 ОБЪЯСНЕНИЕ ПРОБЛЕМЫ:")
    if not has_video and not has_text:
        print("❌ У урока НЕТ НИ ВИДЕО, НИ ТЕКСТА!")
        print("   Поэтому показывается: 'Содержимое урока не доступно'")
        
        print(f"\n🛠️ РЕШЕНИЯ:")
        print("1. Добавить видео через админ-панель")
        print("2. Добавить текстовое содержимое")
        print("3. Улучшить сообщение об ошибке")
        
    elif not has_video:
        print("ℹ️ У урока есть текст, но нет видео")
        print("   Должен показываться текст урока")
        
    elif not has_text:
        print("ℹ️ У урока есть видео, но нет текста")
        print("   Должно показываться видео")
    else:
        print("✅ У урока есть и видео, и текст")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(diagnose_lesson_123())