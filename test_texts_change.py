import json
import logging
import sys
from utils import get_interface_texts, update_interface_texts

logging.basicConfig(level=logging.INFO)

def main():
    filename = "json/interface_texts.json"
    
    rollback = '--rollback' in sys.argv
    
    if rollback:
        # Hardcoded original Russian buttons (original state)
        original_russian = {
            "my_lessons": "📚 Мои уроки",
            "catalog": "🛍️ Каталог уроков",
            "back": "🔙 Назад",
            "buy": "💳 Купить",
            "details": "📋 Подробнее",
            "free_lesson": "🎁 Бесплатный урок",
            "support": "📞 Поддержка",
            "profile": "👤 Профиль",
            "cancel": "❌ Отмена",
            "confirm": "✅ Подтвердить",
            "skip": "➡️ Пропустить",
            "yes": "✅ Да",
            "no": "❌ Нет",
            "enter_promocode": "🏷️ Ввести промокод",
            "apply_promocode": "✅ Применить промокод",
            "create_ticket": "🎫 Создать тикет",
            "my_tickets": "📋 Мои тикеты",
            "view_ticket": "👁️ Просмотреть",
            "respond_ticket": "💬 Ответить",
            "close_ticket": "✅ Закрыть тикет",
            "open_tickets": "🟢 Открытые",
            "in_progress_tickets": "🟡 В работе",
            "closed_tickets": "🔴 Закрытые",
            "support_stats": "📊 Статистика поддержки"
        }
        
        # Load current and replace buttons
        texts = get_interface_texts()
        texts['buttons'] = original_russian
        update_interface_texts(texts)
        print("Rollback successful. Texts restored to original Russian using hardcoded values.")
        return
    
    # Load current texts
    texts = get_interface_texts()
    
    if 'buttons' not in texts:
        print("Error: 'buttons' category not found")
        return
    
    # Backup current
    with open('json/interface_texts_backup.json', 'w', encoding='utf-8') as f:
        json.dump(texts, f, indent=4, ensure_ascii=False)
    print("Backup created.")
    
    # English translations for buttons
    english_buttons = {
        "my_lessons": "📚 My Lessons",
        "catalog": "🛍️ Catalog",
        "back": "🔙 Back",
        "buy": "💳 Buy",
        "details": "📋 Details",
        "free_lesson": "🎁 Free Lesson",
        "support": "📞 Support",
        "profile": "👤 Profile",
        "cancel": "❌ Cancel",
        "confirm": "✅ Confirm",
        "skip": "➡️ Skip",
        "yes": "✅ Yes",
        "no": "❌ No",
        "enter_promocode": "🏷️ Enter Promo Code",
        "apply_promocode": "✅ Apply Promo Code",
        "create_ticket": "🎫 Create Ticket",
        "my_tickets": "📋 My Tickets",
        "view_ticket": "👁️ View Ticket",
        "respond_ticket": "💬 Respond Ticket",
        "close_ticket": "✅ Close Ticket",
        "open_tickets": "🟢 Open Tickets",
        "in_progress_tickets": "🟡 In Progress Tickets",
        "closed_tickets": "🔴 Closed Tickets",
        "support_stats": "📊 Support Stats"
    }
    
    # Change to English
    texts['buttons'] = english_buttons
    update_interface_texts(texts)
    
    print("Buttons changed to English. JSON saved.")
    print("To rollback, run: python test_texts_change.py --rollback")

if __name__ == '__main__':
    main()