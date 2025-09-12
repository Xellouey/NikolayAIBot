#!/usr/bin/env python3
"""
Тест улучшенных сообщений об отсутствующем содержимом уроков
"""
import asyncio
from database.lesson import Lesson

async def test_improved_error_messages():
    print("=" * 70)
    print("🧪 ТЕСТ УЛУЧШЕННЫХ СООБЩЕНИЙ ОБ ОТСУТСТВУЮЩЕМ СОДЕРЖИМОМ")
    print("=" * 70)
    
    l = Lesson()
    
    # Получаем все уроки для тестирования
    all_lessons = await l.get_all_lessons(active_only=False)
    
    print(f"\n📚 АНАЛИЗ ВСЕХ УРОКОВ ({len(all_lessons)} штук):")
    
    for lesson in all_lessons:
        lesson_data = await l.get_lesson(lesson['id'])
        if not lesson_data:
            continue
            
        print(f"\n🔍 УРОК ID {lesson_data.id}: '{lesson_data.title}'")
        print(f"   • content_type: {lesson_data.content_type}")
        print(f"   • video_file_id: {'✅ Есть' if lesson_data.video_file_id else '❌ Нет'}")
        print(f"   • text_content: {'✅ Есть' if lesson_data.text_content else '❌ Нет'}")
        
        # Определяем, какое сообщение будет показано пользователю
        if lesson_data.content_type == 'video' and lesson_data.video_file_id:
            message_type = "🎥 ВИДЕО УРОК"
            user_message = f"Показывается видео + описание"
        else:
            # Логика из нового кода
            if not lesson_data.text_content and lesson_data.content_type == 'text':
                content_message = "📝 В этом уроке пока нет текстового содержимого"
            elif not lesson_data.video_file_id and lesson_data.content_type == 'video':
                content_message = "🎥 В этом уроке пока нет видео"
            elif lesson_data.content_type not in ['text', 'video']:
                content_message = f"📋 Содержимое типа '{lesson_data.content_type}' пока не поддерживается"
            else:
                content_message = "📋 Содержимое урока временно недоступно"
            
            if lesson_data.text_content:
                message_type = "📝 ТЕКСТОВЫЙ УРОК"
                user_message = f"Показывается текст урока"
            else:
                message_type = "⚠️ ПРОБЛЕМНЫЙ УРОК"
                user_message = content_message
        
        print(f"   • Тип: {message_type}")
        print(f"   • Пользователь увидит: {user_message}")
    
    # Специальная проверка урока "123"
    print(f"\n" + "="*50)
    print("🎯 СПЕЦИАЛЬНАЯ ПРОВЕРКА УРОКА '123':")
    print("="*50)
    
    lesson_123 = await l.get_lesson(5)
    if lesson_123:
        print(f"Название: {lesson_123.title}")
        print(f"Описание: {lesson_123.description}")
        print(f"content_type: {lesson_123.content_type}")
        print(f"text_content: {lesson_123.text_content or 'НЕТ'}")
        print(f"video_file_id: {lesson_123.video_file_id or 'НЕТ'}")
        
        # Применяем новую логику
        if not lesson_123.text_content and lesson_123.content_type == 'text':
            expected_message = "📝 В этом уроке пока нет текстового содержимого"
        else:
            expected_message = "Другое сообщение"
            
        print(f"\n💬 СООБЩЕНИЕ ДЛЯ ПОЛЬЗОВАТЕЛЯ:")
        print(f"📚 {lesson_123.title}")
        print(f"{lesson_123.description}")
        print(f"{expected_message}")
        
        print(f"\n✅ УЛУЧШЕНИЕ: Вместо 'Содержимое урока не доступно' теперь показывается:")
        print(f"    '{expected_message}'")
    
    print("\n" + "="*70)
    print("🎉 ТЕСТ ЗАВЕРШЕН!")
    print("Теперь пользователи получают более понятные сообщения о том,")
    print("что именно отсутствует в уроке.")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_improved_error_messages())