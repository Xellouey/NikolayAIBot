import json

def rollback_buttons():
    filename = "json/interface_texts.json"
    
    # Hardcoded original Russian buttons
    russian_buttons = {
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
        "support_stats": "📊 Статистика"
    }
    
    # Load current texts
    texts = json.load(open(filename, 'r', encoding='utf-8'))
    
    # Restore buttons to Russian
    texts['buttons'] = russian_buttons
    
    # Save
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(texts, f, indent=4, ensure_ascii=False)
    
    print("Rollback to Russian completed. JSON saved.")

if __name__ == '__main__':
    rollback_buttons()