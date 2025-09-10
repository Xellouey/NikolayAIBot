"""Simple localization system for bot texts"""
import logging
from typing import Dict, Optional
from database.lesson import Translations
from peewee import DoesNotExist

# Icon constants
BACK_ICON = '⬅️'  # Left arrow emoji for back button

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
}


class Localization:
    """Simple localization handler"""
    
    @staticmethod
    def get_text(key: str, lang: str = 'ru', **kwargs) -> str:
        """
        Get localized text by key
        
        Args:
            key: Text key (e.g., 'welcome', 'btn_catalog')
            lang: Language code (default 'ru')
            **kwargs: Format arguments for text
        
        Returns:
            Localized and formatted text
        """
        # For Russian, use default texts
        if lang == 'ru':
            text = DEFAULT_TEXTS.get(key, key)
        else:
            # Try to get translation from database
            try:
                translation = Translations.select().where(
                    (Translations.text_key == key) &
                    (Translations.language == lang)
                ).first()
                
                if translation and translation.value:
                    text = translation.value
                else:
                    # Fallback to Russian
                    text = DEFAULT_TEXTS.get(key, key)
                    
            except Exception as e:
                logging.error(f"Error getting translation for {key}/{lang}: {e}")
                text = DEFAULT_TEXTS.get(key, key)
        
        # Format text if needed
        if kwargs:
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
    return Localization.get_text(key, lang, **kwargs)
