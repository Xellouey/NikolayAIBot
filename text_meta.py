from typing import Tuple, Dict, Any, List
from localization import get_text
import keyboards as kb
from database import lesson
from database.lead_magnet import LeadMagnet

# В этом модуле определены функции, которые собирают экраны (сцены)
# для предпросмотра админом. В них подставляются тестовые данные,
# чтобы админ видел реальный вид экрана: текст + клавиатура.

l = lesson.Lesson()
p = lesson.Purchase()


async def build_scene(scene: str, user_id: int = 0, lang: str = 'ru') -> Tuple[str, Any]:
    """
    Сконструировать текст и клавиатуру для заданной сцены.
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


# Мэппинг использования ключей на сцены для подсказки админам
KEY_USAGE: Dict[str, List[str]] = {
    # Кнопки
    'btn_catalog': ['main'],
    'btn_my_lessons': ['main'],
    'btn_support': ['main'],
    'btn_back': ['catalog', 'my_lessons', 'support'],

    # Сообщения
    'welcome': ['main'],
    'catalog_title': ['catalog'],
    'my_lessons_title': ['my_lessons'],
    'support_welcome': ['support'],
    'no_lessons': ['my_lessons'],
}


def get_key_usage_scenes(key: str) -> List[str]:
    return KEY_USAGE.get(key, [])
