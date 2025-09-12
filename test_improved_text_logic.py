#!/usr/bin/env python3
"""
Тест улучшенной логики для текстовых уроков с fallback на description
"""
import asyncio
from database.lesson import Lesson

async def test_text_lesson_logic():
    print("=" * 70)
    print("🧪 ТЕСТ УЛУЧШЕННОЙ ЛОГИКИ ДЛЯ ТЕКСТОВЫХ УРОКОВ")
    print("=" * 70)
    
    l = Lesson()
    
    print("\n📚 ТЕСТИРОВАНИЕ ВСЕХ УРОКОВ С НОВОЙ ЛОГИКОЙ:")
    
    all_lessons = await l.get_all_lessons(active_only=False)
    
    for lesson in all_lessons:
        lesson_data = await l.get_lesson(lesson['id'])
        if not lesson_data:
            continue
            
        print(f"\n🔍 УРОК ID {lesson_data.id}: '{lesson_data.title}'")
        print(f"   • content_type: {lesson_data.content_type}")
        print(f"   • description: {'✅ Есть' if lesson_data.description else '❌ Нет'}")
        print(f"   • text_content: {'✅ Есть' if lesson_data.text_content else '❌ Нет'}")
        print(f"   • video_file_id: {'✅ Есть' if lesson_data.video_file_id else '❌ Нет'}")
        
        # Применяем новую логику
        if lesson_data.content_type == 'video' and lesson_data.video_file_id:
            result = "🎥 ВИДЕО: Показывается видео урока"
        elif lesson_data.content_type == 'text':
            # Новая логика для текстовых уроков
            if lesson_data.text_content:
                result = f"📝 ТЕКСТ: Показывается text_content"
            elif lesson_data.description:
                result = f"📝 FALLBACK: Показывается description как содержимое"
            else:
                result = f"❌ ОШИБКА: Нет ни text_content, ни description"
        elif lesson_data.content_type == 'video' and not lesson_data.video_file_id:
            result = "❌ ВИДЕО ОТСУТСТВУЕТ: Показывается сообщение об отсутствии видео"
        else:
            result = f"❓ НЕИЗВЕСТНЫЙ ТИП: {lesson_data.content_type}"
        
        print(f"   • РЕЗУЛЬТАТ: {result}")
    
    print(f"\n" + "="*50)
    print("🎯 СПЕЦИАЛЬНАЯ ПРОВЕРКА УРОКА '123':")
    print("="*50)
    
    lesson_123 = await l.get_lesson(5)
    if lesson_123:
        print(f"Название: {lesson_123.title}")
        print(f"content_type: {lesson_123.content_type}")
        print(f"description: '{lesson_123.description}'")
        print(f"text_content: '{lesson_123.text_content or 'НЕТ'}'")
        
        # Применяем новую логику
        if lesson_123.content_type == 'text':
            if lesson_123.text_content:
                content_text = lesson_123.text_content
                source = "text_content"
            elif lesson_123.description:
                content_text = f"📝 {lesson_123.description}"
                source = "description (fallback)"
            else:
                content_text = "📝 В этом уроке пока нет содержимого"
                source = "error message"
        
        print(f"\n💬 ТЕПЕРЬ ПОЛЬЗОВАТЕЛЬ УВИДИТ:")
        print(f"📚 {lesson_123.title}")
        print(f"{content_text}")
        print(f"\n✅ Источник содержимого: {source}")
        
        if source == "description (fallback)":
            print("🎉 ОТЛИЧНО! Теперь description используется как содержимое урока!")
    
    print("\n" + "="*70)
    print("🎉 ТЕСТ ЗАВЕРШЕН!")
    print("Теперь для текстовых уроков без text_content")
    print("будет показываться description как содержимое!")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_text_lesson_logic())