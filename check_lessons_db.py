import asyncio
from database.lesson import Lesson

async def check_lessons():
    l = Lesson()
    
    print("=== Проверка всех уроков ===")
    all_lessons = await l.get_all_lessons(active_only=False)
    print(f"Всего уроков: {len(all_lessons)}")
    for lesson in all_lessons:
        print(f"  - ID: {lesson['id']}, Title: {lesson['title']}, Active: {lesson.get('active', False)}, Free: {lesson.get('is_free', False)}")
    
    print("\n=== Проверка активных уроков ===")
    active_lessons = await l.get_all_lessons(active_only=True)
    print(f"Активных уроков: {len(active_lessons)}")
    for lesson in active_lessons:
        print(f"  - ID: {lesson['id']}, Title: {lesson['title']}, Free: {lesson.get('is_free', False)}")
    
    print("\n=== Проверка платных уроков в каталоге ===")
    paid_lessons = [lesson for lesson in active_lessons if not lesson.get('is_free', False)]
    print(f"Платных уроков для каталога: {len(paid_lessons)}")
    for lesson in paid_lessons:
        print(f"  - ID: {lesson['id']}, Title: {lesson['title']}")

if __name__ == "__main__":
    asyncio.run(check_lessons())
