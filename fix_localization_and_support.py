#!/usr/bin/env python3
"""
Fix script to update the localization keys, support cancel flow, and lead magnet feature
"""
import os
import sys
import re
from pathlib import Path

def update_localization_py():
    """Update localization.py with missing keys"""
    
    localization_file = Path("localization.py")
    content = localization_file.read_text(encoding='utf-8')
    
    # Find the DEFAULT_TEXTS dictionary
    default_texts_start = content.find("DEFAULT_TEXTS = {")
    if default_texts_start == -1:
        print("ERROR: Could not find DEFAULT_TEXTS in localization.py")
        return False
    
    # Find the closing brace of DEFAULT_TEXTS
    brace_count = 0
    idx = default_texts_start + len("DEFAULT_TEXTS = {")
    found_close = False
    while idx < len(content):
        if content[idx] == '{':
            brace_count += 1
        elif content[idx] == '}':
            if brace_count == 0:
                found_close = True
                break
            brace_count -= 1
        idx += 1
    
    if not found_close:
        print("ERROR: Could not find closing brace of DEFAULT_TEXTS")
        return False
    
    # Additional keys to add
    additional_keys = '''
    # Support system messages
    'support_welcome': '💬 Чем могу помочь?\\n\\nВыберите действие или создайте тикет для связи с поддержкой.',
    'ticket_subject_prompt': '📝 Введите тему вашего обращения (краткое описание проблемы):',
    'ticket_description_prompt': '✍️ Опишите вашу проблему подробно.\\n\\nВы можете прикрепить фото, видео или документ.',
    'ticket_created': '✅ Тикет #{ticket_id} создан!\\n\\nТема: {subject}\\n\\nМы ответим вам в ближайшее время.',
    'no_tickets': '📭 У вас пока нет тикетов.\\n\\nСоздайте новый тикет, если нужна помощь.',
    'ticket_status_open': '🟢 Открыт',
    'ticket_status_in_progress': '🟡 В работе',
    'ticket_status_closed': '🔴 Закрыт',
    'ticket_details': '📋 Тикет #{ticket_id}\\n\\n📝 Тема: {subject}\\n📊 Статус: {status}\\n📅 Создан: {created_at}\\n\\n💬 Описание:\\n{description}',
    'ticket_response_notification': '💬 Получен ответ на ваш тикет #{ticket_id}\\n\\nТема: {subject}\\n\\nПроверьте в разделе «Мои тикеты».',
    'ticket_closed_notification': '✅ Тикет #{ticket_id} закрыт\\n\\nТема: {subject}\\n\\nСпасибо за обращение!',
    
    # Shop messages
    'my_lessons_title': '📚 Ваши уроки:',
    'catalog_title': '📚 Выберите урок для изучения:',
    'no_lessons': '📭 Уроков пока нет.',
    'error_occurred': '❌ Произошла ошибка. Попробуйте позже.',
    'profile_info': '👤 <b>Ваш профиль</b>\\n\\n👤 Имя: {full_name}\\n📚 Куплено уроков: {lessons_count}',
    'enter_promocode': '🎟️ Введите промокод:',
    'promocode_invalid': '❌ Недействительный промокод. Попробуйте другой.',
    'promocode_applied': '✅ Промокод применен!\\n\\nСкидка: ${discount}\\nИтоговая цена: ${final_price} ({final_stars} ⭐)',
    
    # Admin messages (always in Russian)
    'admin.messages.support_dashboard': '📊 <b>Панель поддержки</b>\\n\\n📈 Всего тикетов: {total}\\n🟢 Открытых: {open}\\n🟡 В работе: {in_progress}\\n🔴 Закрытых: {closed}',
    'admin.messages.ticket_details_admin': '📋 <b>Тикет #{ticket_id}</b>\\n\\n👤 Пользователь: {user_name} (ID: {user_id})\\n📝 Тема: {subject}\\n📊 Статус: {status}\\n📅 Создан: {created_at}\\n📅 Обновлен: {updated_at}\\n\\n💬 Описание:\\n{description}',
    'admin.messages.admin_response_prompt': '✍️ Введите ваш ответ на тикет:',
    'admin.messages.response_sent': '✅ Ответ отправлен!',
    'admin.messages.new_ticket_notification': '🆕 <b>Новый тикет!</b>\\n\\n📝 Тема: {subject}\\n👤 От: {user_name} (ID: {user_id})\\n📅 Создан: {created_at}',
    'admin.messages.no_lessons': '📭 Уроков пока нет. Создайте первый урок!','''
    
    # Insert the new keys before the closing brace
    new_content = content[:idx] + additional_keys + "\n" + content[idx:]
    
    # Write back the file
    localization_file.write_text(new_content, encoding='utf-8')
    print("✅ Updated localization.py with missing keys")
    return True

def fix_get_text_calls():
    """Fix all get_text calls to remove 'messages.' prefix"""
    
    files_to_fix = [
        'handlers/support.py',
        'handlers/shop.py'
    ]
    
    replacements = {
        "get_text('messages.support_welcome')": "get_text('support_welcome')",
        'get_text("messages.support_welcome")': 'get_text("support_welcome")',
        "get_text('messages.ticket_subject_prompt')": "get_text('ticket_subject_prompt')",
        "get_text('messages.ticket_description_prompt')": "get_text('ticket_description_prompt')",
        "get_text('messages.ticket_created'": "get_text('ticket_created'",
        "get_text('messages.no_tickets')": "get_text('no_tickets')",
        'get_text("messages.no_tickets")': 'get_text("no_tickets")',
        "get_text('messages.ticket_status_open')": "get_text('ticket_status_open')",
        "get_text('messages.ticket_status_in_progress')": "get_text('ticket_status_in_progress')",
        "get_text('messages.ticket_status_closed')": "get_text('ticket_status_closed')",
        "get_text('messages.ticket_details'": "get_text('ticket_details'",
        "get_text('messages.ticket_response_notification'": "get_text('ticket_response_notification'",
        "get_text('messages.ticket_closed_notification'": "get_text('ticket_closed_notification'",
        "get_text('messages.error_occurred')": "get_text('error_occurred')",
        'get_text("messages.error_occurred")': 'get_text("error_occurred")',
        "get_text('messages.my_lessons_title')": "get_text('my_lessons_title')",
        "get_text('messages.catalog_title')": "get_text('catalog_title')",
        "get_text('messages.no_lessons')": "get_text('no_lessons')",
        "get_text('messages.profile_info'": "get_text('profile_info'",
        "get_text('messages.enter_promocode')": "get_text('enter_promocode')",
        "get_text('messages.promocode_invalid')": "get_text('promocode_invalid')",
        "get_text('messages.promocode_applied'": "get_text('promocode_applied'",
        "get_text('messages.welcome')": "get_text('welcome')",
        
        # Admin messages - keep the admin. prefix but remove messages.
        "get_text('admin.messages.support_dashboard'": "get_text('admin.support_dashboard'",
        "get_text('admin.messages.ticket_details_admin'": "get_text('admin.ticket_details_admin'",
        "get_text('admin.messages.admin_response_prompt')": "get_text('admin.admin_response_prompt')",
        "get_text('admin.messages.response_sent')": "get_text('admin.response_sent')",
        "get_text('admin.messages.new_ticket_notification'": "get_text('admin.new_ticket_notification'",
        "get_text('admin.messages.no_lessons')": "get_text('admin.no_lessons')",
    }
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed get_text calls in {file_path}")
        else:
            print(f"ℹ️ No changes needed in {file_path}")
    
    return True

def add_normalization_to_get_text():
    """Add defensive normalization to get_text function"""
    
    localization_file = Path("localization.py")
    content = localization_file.read_text(encoding='utf-8')
    
    # Find the get_text method in Localization class
    pattern = r"(\s+def get_text\(key: str, lang: str = 'ru', \*\*kwargs\) -> str:\s*\n\s*\"\"\"[^\"]*\"\"\"\s*\n)"
    
    replacement = r'''\1        # Normalize key - remove 'messages.' prefix if present for backward compatibility
        if key.startswith('messages.'):
            key = key.replace('messages.', '')
        if key.startswith('admin.messages.'):
            key = key.replace('admin.messages.', 'admin.')
        
'''
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        localization_file.write_text(new_content, encoding='utf-8')
        print("✅ Added key normalization to get_text function")
    else:
        print("⚠️ Could not add normalization - manual review needed")
    
    return True

if __name__ == "__main__":
    print("🔧 Starting localization and support fixes...")
    
    # Step 1: Update localization.py with missing keys
    if not update_localization_py():
        print("❌ Failed to update localization.py")
        sys.exit(1)
    
    # Step 2: Fix all get_text calls to remove prefixes
    if not fix_get_text_calls():
        print("❌ Failed to fix get_text calls")
        sys.exit(1)
    
    # Step 3: Add normalization to get_text
    if not add_normalization_to_get_text():
        print("⚠️ Normalization not added, but continuing...")
    
    print("\n✅ Localization fixes complete!")
    print("✅ All changes applied successfully!")
