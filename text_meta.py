from typing import Tuple, Dict, Any, List
from localization import get_text
import keyboards as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import lesson
from database.lead_magnet import LeadMagnet

# В этом модуле определены функции, которые собирают экраны (сцены)
# для предпросмотра админом. В них подставляются тестовые данные,
# чтобы админ видел реальный вид экрана: текст + клавиатура.

l = lesson.Lesson()
p = lesson.Purchase()


async def build_scene(scene: str, user_id: int = 0, lang: str = 'ru') -> Tuple[str, Any]:
    """
    Сконструировать текст и клавиатуру для заданной сцены (обычный режим).
    Возвращает (text, reply_markup)
    """
    scene = scene.lower()

    if scene == 'main':
        text = get_text('welcome', lang)
        markup = kb.markup_main_menu(lang)
        return text, markup

    if scene == 'catalog':
        # Заготовим 2 примера уроков
        lessons = [
            {'id': 101, 'title': 'Midjourney: основы', 'price_usd': 19.99, 'is_free': False},
            {'id': 102, 'title': 'Бесплатный вводный урок', 'price_usd': 0, 'is_free': True},
        ]
        text = get_text('catalog_title', lang)
        markup = await kb.markup_catalog(lessons)
        return text, markup

    if scene == 'lesson_card':
        # Карточка урока (пример, без учёта покупки)
        sample_lesson = {'id': 301, 'title': 'Stable Diffusion PRO', 'description': 'Глубокий курс по SD', 'price_usd': 29.0}
        from localization import get_text as t
        text = t('messages.lesson_details', 'ru', title=sample_lesson['title'], price_usd=f"{sample_lesson['price_usd']:.2f}", price_stars='2900', description=sample_lesson['description']) if hasattr(t, '__call__') else 'Карточка урока'
        markup = kb.markup_lesson_details(sample_lesson['id'], user_has_lesson=False, show_promocode=True, is_free=False, has_preview=True, lang=lang)
        return text, markup

    if scene == 'payment':
        # Экран оплаты: используем карточку урока и кнопки оплаты/промокода
        sample_lesson = {'id': 401, 'title': 'AI Копирайтинг', 'description': 'Научитесь писать с AI', 'price_usd': 25.0}
        from localization import get_text as t
        text = t('messages.lesson_details', 'ru', title=sample_lesson['title'], price_usd=f"{sample_lesson['price_usd']:.2f}", price_stars='2500', description=sample_lesson['description']) if hasattr(t, '__call__') else 'Оплата'
        markup = kb.markup_lesson_details(sample_lesson['id'], user_has_lesson=False, show_promocode=True, is_free=False, has_preview=False, lang=lang)
        return text, markup

    if scene == 'my_lessons':
        lessons = []
        # Лид-магнит, если включен
        if await LeadMagnet.is_ready():
            lead_label = await LeadMagnet.get_text_for_locale('lessons_label', lang)
            lessons.append({
                'id': 'lead_magnet',
                'title': lead_label or 'Приветственный вводный урок',
                'is_lead': True
            })
        # Пример купленного урока
        lessons.append({'id': 201, 'title': 'ChatGPT для маркетинга', 'is_lead': False})
        text = get_text('my_lessons_title', lang)
        markup = kb.markup_my_lessons(lessons)
        return text, markup

    if scene == 'support':
        text = get_text('support_welcome', lang)
        markup = kb.markup_support_menu()
        return text, markup

    # Fallback
    return '❌ Сцена не найдена', kb.markup_main_menu(lang)


async def build_scene_preview(scene: str, lang: str = 'ru') -> Tuple[str, InlineKeyboardMarkup]:
    """
    Сконструировать текст и клавиатуру для предпросмотра админом.
    Кнопки в предпросмотре ведут на редактирование соответствующих ключей.
    """
    scene = scene.lower()

    def back_row():
        return [InlineKeyboardButton(text='↩️ Назад', callback_data='scene_preview')]

    if scene == 'main':
        text = get_text('welcome', lang)
        items = [
            [InlineKeyboardButton(text=get_text('btn_catalog', lang), callback_data='scene_edit_key:main:buttons:btn_catalog')],
            [InlineKeyboardButton(text=get_text('btn_my_lessons', lang), callback_data='scene_edit_key:main:buttons:btn_my_lessons')],
            [InlineKeyboardButton(text=get_text('btn_support', lang), callback_data='scene_edit_key:main:buttons:btn_support')],
            [InlineKeyboardButton(text='✏️ Изменить текст экрана', callback_data='scene_edit_message:main:messages.welcome')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'profile':
        # Профиль пользователя
        text = get_text('profile_info', lang, full_name='Иван Иванов', lessons_count=3)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст профиля', callback_data='scene_edit_message:profile:messages.profile_info')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'catalog':
        text = get_text('catalog_title', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст экрана', callback_data='scene_edit_message:catalog:messages.catalog_title')],
            [InlineKeyboardButton(text='✏️ Изменить кнопку Назад', callback_data='scene_edit_key:catalog:buttons:btn_back')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'my_lessons':
        text = get_text('my_lessons_title', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст экрана', callback_data='scene_edit_message:my_lessons:messages.my_lessons_title')],
            [InlineKeyboardButton(text='✏️ Изменить кнопку Назад', callback_data='scene_edit_key:my_lessons:buttons:btn_back')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'support':
        text = get_text('support_welcome', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст экрана', callback_data='scene_edit_message:support:messages.support_welcome')],
            [InlineKeyboardButton(text='✏️ Изменить кнопку Назад', callback_data='scene_edit_key:support:buttons:btn_back')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'support_subject':
        text = get_text('ticket_subject_prompt', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст темы', callback_data='scene_edit_message:support_subject:messages.ticket_subject_prompt')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'support_description':
        text = get_text('ticket_description_prompt', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст описания', callback_data='scene_edit_message:support_description:messages.ticket_description_prompt')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'support_my_tickets':
        text = get_text('no_tickets', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст "нет тикетов"', callback_data='scene_edit_message:support_my_tickets:messages.no_tickets')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'support_ticket_details':
        text = get_text('ticket_details', lang, ticket_id=123, subject='Пример темы', status='🟢 Открыт', created_at='2025-01-01', description='Описание тикета...')
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст деталей тикета', callback_data='scene_edit_message:support_ticket_details:messages.ticket_details')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'payment':
        # Редактирование: текст карточки и кнопки Купить/Промокод
        from localization import get_text as t
        text = t('messages.lesson_details', 'ru', title='Название урока', price_usd='25.00', price_stars='2500', description='Описание урока')
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст карточки', callback_data='scene_edit_message:payment:messages.lesson_details')],
            [InlineKeyboardButton(text='✏️ Изменить кнопку Купить', callback_data='scene_edit_key:payment:buttons:btn_buy')],
            [InlineKeyboardButton(text='✏️ Изменить кнопку Ввести промокод', callback_data='scene_edit_key:payment:buttons:enter_promocode')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    if scene == 'promocode':
        # Редактирование ключей промокода
        text = get_text('enter_promocode', lang)
        items = [
            [InlineKeyboardButton(text='✏️ Изменить текст "Введите промокод"', callback_data='scene_edit_message:promocode:messages.enter_promocode')],
            [InlineKeyboardButton(text='✏️ Изменить текст "Промокод недействителен"', callback_data='scene_edit_message:promocode:messages.promocode_invalid')],
            [InlineKeyboardButton(text='✏️ Изменить текст "Промокод применен"', callback_data='scene_edit_message:promocode:messages.promocode_applied')],
            back_row()
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=items)

    # Fallback
    return '❌ Сцена не найдена', InlineKeyboardMarkup(inline_keyboard=[back_row()])


# Мэппинг использования ключей на сцены для подсказки админам
KEY_USAGE: Dict[str, List[str]] = {
    # Кнопки
    'btn_catalog': ['main'],
    'btn_my_lessons': ['main'],
    'btn_support': ['main'],
    'btn_back': ['catalog', 'my_lessons', 'support'],
    'btn_buy': ['lesson_card', 'payment'],
    'btn_enter_promocode': ['payment'],

    # Сообщения
    'welcome': ['main'],
    'catalog_title': ['catalog'],
    'my_lessons_title': ['my_lessons'],
    'profile_info': ['profile'],
    'support_welcome': ['support'],
    'ticket_subject_prompt': ['support_subject'],
    'ticket_description_prompt': ['support_description'],
    'no_tickets': ['support_my_tickets'],
    'ticket_details': ['support_ticket_details'],
    'lesson_details': ['lesson_card', 'payment'],
    'enter_promocode': ['promocode', 'payment'],
    'promocode_invalid': ['promocode'],
    'promocode_applied': ['promocode'],
}


def get_key_usage_scenes(key: str) -> List[str]:
    return KEY_USAGE.get(key, [])
