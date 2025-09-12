"""Simple localization system for bot texts"""
import logging
import os
import json
from typing import Dict, Optional
from database.lesson import Translations
from peewee import DoesNotExist

# Icon constants
BACK_ICON = '⬅️'  # Left arrow emoji for back button

# Loadable interface texts (admin-editable via json/interface_texts.json)
_INTERFACE_TEXTS = None


def _load_interface_texts() -> Dict:
    """Load interface texts JSON once (dynamically reloaded)."""
    global _INTERFACE_TEXTS
    if _INTERFACE_TEXTS is not None:
        return _INTERFACE_TEXTS
    try:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, 'json', 'interface_texts.json')
        with open(path, 'r', encoding='utf-8') as f:
            _INTERFACE_TEXTS = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load interface_texts.json: {e}")
        _INTERFACE_TEXTS = {}
    return _INTERFACE_TEXTS


# Default texts in Russian (base language)
DEFAULT_TEXTS = {
    # Welcome flow
    'welcome': '👋 Добро пожаловать в школу по нейросетям!\n\nЗдесь вы научитесь создавать удивительный контент с помощью AI.',
    'intro_video_caption': '🎬 Посмотрите вводное видео о наших курсах',
    'after_video': '👆 Отличное начало! Теперь вы можете изучать наши уроки.',
    
    # Main menu buttons
    'btn_catalog': '📚 Каталог уроков',
    'btn_my_lessons': '📝 Мои уроки',
    'btn_support': '💬 Поддержка',
    'btn_back': '⬅️ Назад',
    
    # Catalog
    'catalog_title': '📚 Выберите урок для изучения:',
    'lesson_price': '💰 Цена: {price} ⭐',
    'lesson_owned': '✅ Куплен',
    'btn_buy': '🛒 Купить',
    'btn_view': '👀 Смотреть',
    
    # Purchase
    'purchase_success': '✅ Спасибо за покупку! Урок теперь доступен.',
    'purchase_error': '❌ Ошибка при покупке. Попробуйте позже.',
    
    # Support
    'support_welcome': '💬 Напишите ваш вопрос, и мы ответим в ближайшее время.',
    'support_sent': '✅ Ваше сообщение отправлено. Ожидайте ответа.',
    
    # Mail (рассылка)
    'mail.messages.mail_help': (
        'Вы можете прикрепить к рассылке inline-клавиатуру в формате JSON. '
        'Inline-клавиатуры позволяют добавлять кнопки с ссылками или callback-действиями. '
        'Вставьте JSON в поле ниже. Если поле пустое — клавиатура не будет добавлена.'
    ),
    'mail.buttons.copy_json': '📋 Скопировать пример JSON',
    'mail.messages.json_example_inline': (
        '{\n'
        '  "inline_keyboard": [\n'
        '    [ {"text": "🌐 Открыть сайт", "url": "https://example.com"} ],\n'
        '    [ {"text": "💬 Поддержка", "callback_data": "support"} ]\n'
        '  ]\n'
        '}'
    ),
    'mail.messages.json_example_callback': (
        '{\n'
        '  "inline_keyboard": [\n'
        '    [ {"text": "📚 Каталог", "callback_data": "catalog"} ],\n'
        '    [ {"text": "💰 Мои уроки", "callback_data": "my_lessons"} ],\n'
        '    [ {"text": "🔙 Назад", "callback_data": "back_main"} ]\n'
        '  ]\n'
        '}'
    ),
    'mail.buttons.copy_inline': '📋 Пример с ссылками',
    'mail.buttons.copy_callback': '🔘 Пример с действиями',

    # Support system messages
    'support_welcome': '💬 Чем могу помочь?\n\nВыберите действие или создайте тикет для связи с поддержкой.',
    'ticket_subject_prompt': '📝 Введите тему вашего обращения (краткое описание проблемы):',
    'ticket_description_prompt': '✍️ Опишите вашу проблему подробно.\n\nВы можете прикрепить фото, видео или документ.',
    'ticket_created': '✅ Тикет #{ticket_id} создан!\n\nТема: {subject}\n\nМы ответим вам в ближайшее время.',
    'no_tickets': '📭 У вас пока нет тикетов.\n\nСоздайте новый тикет, если нужна помощь.',
    'ticket_status_open': '🟢 Открыт',
    'ticket_status_in_progress': '🟡 В работе',
    'ticket_status_closed': '🔴 Закрыт',
    'ticket_details': '📋 Тикет #{ticket_id}\n\n📝 Тема: {subject}\n📊 Статус: {status}\n📅 Создан: {created_at}\n\n💬 Описание:\n{description}',
    'ticket_response_notification': '💬 Получен ответ на ваш тикет #{ticket_id}\n\nТема: {subject}\n\nПроверьте в разделе «Мои тикеты».',
    'ticket_closed_notification': '✅ Тикет #{ticket_id} закрыт\n\nТема: {subject}\n\nСпасибо за обращение!',
    
    # Shop messages
    'my_lessons_title': '📚 Ваши уроки:',
    'catalog_title': '📚 Выберите урок для изучения:',
    'no_lessons': '📭 Уроков пока нет.',
    'error_occurred': '❌ Произошла ошибка. Попробуйте позже.',
    'profile_info': '👤 <b>Ваш профиль</b>\n\n👤 Имя: {full_name}\n📚 Куплено уроков: {lessons_count}',
    'enter_promocode': '🎟️ Введите промокод:',
    'promocode_invalid': '❌ Недействительный промокод. Попробуйте другой.',
    'promocode_applied': '✅ Промокод применен!\n\nСкидка: ${discount}\nИтоговая цена: ${final_price} ({final_stars} ⭐)',
    
    # Admin messages (always in Russian) - also available without 'messages.' prefix
    'admin.support_dashboard': '📊 <b>Панель поддержки</b>\n\n📈 Всего тикетов: {total}\n🟢 Открытых: {open}\n🟡 В работе: {in_progress}\n🔴 Закрытых: {closed}',
    'admin.ticket_details_admin': '📋 <b>Тикет #{ticket_id}</b>\n\n👤 Пользователь: {user_name} (ID: {user_id})\n📝 Тема: {subject}\n📊 Статус: {status}\n📅 Создан: {created_at}\n📅 Обновлен: {updated_at}\n\n💬 Описание:\n{description}',
    'admin.admin_response_prompt': '✍️ Введите ваш ответ на тикет:',
    'admin.response_sent': '✅ Ответ отправлен!',
    'admin.new_ticket_notification': '🆕 <b>Новый тикет!</b>\n\n📝 Тема: {subject}\n👤 От: {user_name} (ID: {user_id})\n📅 Создан: {created_at}',
    'admin.no_lessons': '📭 Уроков пока нет. Создайте первый урок!',
    # Legacy support for old format
    'admin.messages.support_dashboard': '📊 <b>Панель поддержки</b>\n\n📈 Всего тикетов: {total}\n🟢 Открытых: {open}\n🟡 В работе: {in_progress}\n🔴 Закрытых: {closed}',
    'admin.messages.ticket_details_admin': '📋 <b>Тикет #{ticket_id}</b>\n\n👤 Пользователь: {user_name} (ID: {user_id})\n📝 Тема: {subject}\n📊 Статус: {status}\n📅 Создан: {created_at}\n📅 Обновлен: {updated_at}\n\n💬 Описание:\n{description}',
    'admin.messages.admin_response_prompt': '✍️ Введите ваш ответ на тикет:',
    'admin.messages.response_sent': '✅ Ответ отправлен!',
    'admin.messages.new_ticket_notification': '🆕 <b>Новый тикет!</b>\n\n📝 Тема: {subject}\n👤 От: {user_name} (ID: {user_id})\n📅 Создан: {created_at}',
    'admin.messages.no_lessons': '📭 Уроков пока нет. Создайте первый урок!',
}


class Localization:
    """Simple localization handler"""
    
    @staticmethod
    def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
        """
        Get localized text by key.
        
        Resolution order (dynamic reload):
        1) json/interface_texts.json (admin-edited), supports:
           - dotted keys like 'messages.catalog_title'
           - btn_* keys mapped to buttons category (e.g., 'btn_back' -> buttons.back)
           - plain keys searched across common categories (messages, buttons, mail)
        2) DEFAULT_TEXTS (Russian base)
        3) DB Translations (optional) for non-'ru' languages, then fallback to DEFAULT_TEXTS
        
        Admin panel remains Russian and should not rely on this function for its own labels.
        """
        # Normalize key - remove 'messages.' prefix if present for backward compatibility
        if key.startswith('messages.'):
            key = key.replace('messages.', '')
        if key.startswith('admin.messages.'):
            key = key.replace('admin.messages.', 'admin.')
        
        text: Optional[str] = None

        # 1) Try interface_texts.json (admin-edited)
        try:
            itexts = _load_interface_texts()
            if itexts:
                # Dotted key: category.key
                if '.' in key:
                    category, subkey = key.split('.', 1)
                    if category in itexts and isinstance(itexts[category], dict):
                        text = itexts[category].get(subkey)
                else:
                    # btn_* convenience mapping -> buttons category
                    if key.startswith('btn_'):
                        btn_key = key[4:]
                        text = itexts.get('buttons', {}).get(btn_key)
                    # Plain key search across common categories
                    if text is None:
                        for cat in ('messages', 'buttons', 'mail'):
                            if isinstance(itexts.get(cat), dict) and key in itexts.get(cat, {}):
                                text = itexts[cat][key]
                                break
        except Exception as e:
            logging.error(f"Error resolving key from interface_texts.json: {e}")
            text = None

        # 2) Fallback to default/localized DB
        if text is None:
            if lang == 'ru':
                text = DEFAULT_TEXTS.get(key, key)
            else:
                try:
                    translation = Translations.select().where(
                        (Translations.text_key == key) &
                        (Translations.language == lang)
                    ).first()
                    if translation and translation.value:
                        text = translation.value
                    else:
                        text = DEFAULT_TEXTS.get(key, key)
                except Exception as e:
                    logging.error(f"Error getting translation for {key}/{lang}: {e}")
                    text = DEFAULT_TEXTS.get(key, key)

        # 3) Format text if needed
        if kwargs and isinstance(text, str):
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text

        return text
    
    @staticmethod
    def set_translation(key: str, lang: str, value: str) -> bool:
        """
        Set or update translation for a text key
        
        Args:
            key: Text key
            lang: Language code
            value: Translated text
        
        Returns:
            True if successful
        """
        if lang == 'ru':
            # Don't save Russian translations, they're defaults
            return False
            
        try:
            translation, created = Translations.get_or_create(
                text_key=key,
                language=lang,
                defaults={'value': value}
            )
            
            if not created:
                translation.value = value
                translation.save()
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving translation {key}/{lang}: {e}")
            return False
    
    @staticmethod
    def get_all_keys() -> list:
        """Get all available text keys"""
        return list(DEFAULT_TEXTS.keys())
    
    @staticmethod
    def get_translations_for_language(lang: str) -> Dict[str, str]:
        """
        Get all translations for a specific language
        
        Args:
            lang: Language code
        
        Returns:
            Dictionary of key -> translated text
        """
        if lang == 'ru':
            return DEFAULT_TEXTS.copy()
        
        # Start with defaults
        texts = DEFAULT_TEXTS.copy()
        
        # Override with translations from DB
        try:
            translations = Translations.select().where(
                Translations.language == lang
            )
            
            for trans in translations:
                if trans.text_key in texts:
                    texts[trans.text_key] = trans.value
                    
        except Exception as e:
            logging.error(f"Error loading translations for {lang}: {e}")
        
        return texts


# Convenience function for imports
def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
    """Shortcut for Localization.get_text"""
    # Normalize key - remove 'messages.' prefix if present for backward compatibility
    if key.startswith('messages.'):
        key = key.replace('messages.', '')
    if key.startswith('admin.messages.'):
        key = key.replace('admin.messages.', 'admin.')
    
    return Localization.get_text(key, lang, **kwargs)
