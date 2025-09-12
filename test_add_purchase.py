#!/usr/bin/env python3
"""
Добавление тестовой покупки для проверки обработчика view_lesson
"""
import asyncio
from database.lesson import Lesson, Purchase

async def add_test_purchase():
    print("🛒 ДОБАВЛЕНИЕ ТЕСТОВОЙ ПОКУПКИ")
    print("=" * 50)
    
    l = Lesson()
    p = Purchase()
    
    # Добавляем покупку бесплатного урока "Как сделать нейрофотосессию" (ID 4)
    test_user_id = 12345
    lesson_id = 4
    
    print(f"Добавляем покупку урока ID {lesson_id} для пользователя {test_user_id}...")
    
    try:
        # Проверяем, есть ли уже эта покупка
        has_lesson = await p.check_user_has_lesson(test_user_id, lesson_id)
        if has_lesson:
            print("✅ Покупка уже существует!")
        else:
            # Создаем покупку
            await p.create_purchase(
                user_id=test_user_id,
                lesson_id=lesson_id,
                price_paid_usd=0,
                price_paid_stars=0,
                payment_id="test_purchase"
            )
            print("✅ Тестовая покупка добавлена!")
            
            # Увеличиваем счетчик покупок урока
            await l.increment_purchases(lesson_id)
        
        # Проверяем результат
        has_lesson_after = await p.check_user_has_lesson(test_user_id, lesson_id)
        print(f"Проверка доступа: {has_lesson_after}")
        
        if has_lesson_after:
            print("\n🎉 ГОТОВО К ТЕСТИРОВАНИЮ!")
            print("Теперь можно:")
            print("1. Запустить бота")
            print("2. Зайти в 'Мои уроки'")
            print("3. Нажать на урок 'Как сделать нейрофотосессию'")
            print("4. Проверить логи в консоли бота")
        else:
            print("❌ Что-то пошло не так...")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(add_test_purchase())