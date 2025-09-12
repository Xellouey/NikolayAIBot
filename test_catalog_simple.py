import asyncio
from database.lesson import Lesson
import keyboards as kb
from localization import get_text

async def test_catalog_flow():
    """Test catalog flow with current database state"""
    l = Lesson()
    
    print("=== Тестирование потока каталога ===")
    
    # 1. Получаем все активные уроки
    lessons = await l.get_all_lessons(active_only=True)
    print(f"\n✅ Активных уроков в БД: {len(lessons)}")
    for lesson in lessons:
        print(f"  - ID: {lesson['id']}, Title: {lesson['title']}, Free: {lesson.get('is_free', False)}")
    
    # 2. Фильтруем только платные уроки (как в каталоге)
    paid_lessons = [lesson for lesson in lessons if not lesson.get('is_free', False)]
    print(f"\n✅ Платных уроков для каталога: {len(paid_lessons)}")
    
    if not paid_lessons:
        print("\n❌ НЕТ ПЛАТНЫХ УРОКОВ!")
        print(f"Будет показано сообщение: {get_text('admin.no_lessons')}")
        print("Это и есть причина ошибки!")
    else:
        print("\n✅ Каталог будет показан с уроками:")
        for lesson in paid_lessons:
            print(f"  - {lesson['title']}")
            
    # 3. Проверяем создание клавиатуры
    if paid_lessons:
        try:
            markup = await kb.markup_catalog(paid_lessons)
            print("\n✅ Клавиатура каталога создана успешно")
        except Exception as e:
            print(f"\n❌ Ошибка при создании клавиатуры: {e}")

if __name__ == "__main__":
    asyncio.run(test_catalog_flow())
