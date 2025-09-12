import asyncio
from database.lesson import Lesson
from database.lead_magnet import LeadMagnet
import keyboards as kb
from localization import get_text

async def test_full_flow():
    """Test full flow from main menu to catalog"""
    print("=== ПОЛНОЕ ТЕСТИРОВАНИЕ НАВИГАЦИИ ===\n")
    
    # 1. Test main menu
    print("1. Главное меню:")
    main_menu = kb.markup_main_menu('ru')
    print(f"   ✅ Клавиатура главного меню создана")
    for row in main_menu.inline_keyboard:
        for button in row:
            print(f"      - {button.text} -> {button.callback_data}")
    
    # 2. Test catalog
    print("\n2. Каталог уроков:")
    l = Lesson()
    lessons = await l.get_all_lessons(active_only=True)
    print(f"   Всего активных уроков: {len(lessons)}")
    
    paid_lessons = [lesson for lesson in lessons if not lesson.get('is_free', False)]
    print(f"   Платных уроков: {len(paid_lessons)}")
    
    if paid_lessons:
        catalog_markup = await kb.markup_catalog(paid_lessons)
        print(f"   ✅ Клавиатура каталога создана")
        for row in catalog_markup.inline_keyboard:
            for button in row:
                print(f"      - {button.text} -> {button.callback_data}")
    else:
        print(f"   ⚠️ Нет платных уроков - будет показано: {get_text('admin.no_lessons')}")
    
    # 3. Test my lessons
    print("\n3. Мои уроки:")
    my_lessons = []
    
    # Check lead magnet
    if await LeadMagnet.is_ready():
        lead_label = await LeadMagnet.get_text_for_locale('lessons_label', 'ru')
        my_lessons.append({
            'id': 'lead_magnet',
            'title': lead_label or 'Приветственный вводный урок',
            'is_lead': True
        })
        print(f"   ✅ Лид-магнит доступен: {lead_label or 'Приветственный вводный урок'}")
    else:
        print(f"   ℹ️ Лид-магнит не настроен")
    
    if my_lessons:
        my_lessons_markup = kb.markup_my_lessons(my_lessons)
        print(f"   ✅ Клавиатура 'Мои уроки' создана")
        for row in my_lessons_markup.inline_keyboard:
            for button in row:
                print(f"      - {button.text} -> {button.callback_data}")
    else:
        print(f"   ⚠️ Нет уроков - будет показано: {get_text('no_lessons')}")
    
    # 4. Test support menu
    print("\n4. Поддержка:")
    from keyboards import markup_support_menu
    support_markup = markup_support_menu()
    print(f"   ✅ Клавиатура поддержки создана")
    for row in support_markup.inline_keyboard:
        for button in row:
            print(f"      - {button.text} -> {button.callback_data}")
    
    print("\n=== ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
    print("\n📌 РЕЗЮМЕ:")
    if paid_lessons:
        print("✅ Каталог работает корректно")
    else:
        print("⚠️ В каталоге нет платных уроков - пользователь увидит сообщение об отсутствии уроков")
    
    if await LeadMagnet.is_ready():
        print("✅ Лид-магнит настроен и доступен")
    else:
        print("ℹ️ Лид-магнит не настроен")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
