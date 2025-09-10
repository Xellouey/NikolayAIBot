import config
import logging
import utils
from localization import get_text
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def markup_admin(user_id):
    """Original admin markup - redirect to new shop admin"""
    return markup_admin_shop(user_id)


def markup_pass():
    items = [
        [KeyboardButton(text='➡️ Пропустить')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_pass = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_pass


def markup_phone():
    items = [
        [KeyboardButton(text='📞 Авторизация', request_contact=True)]
    ]
    
    markup_phone = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True, one_time_keyboard=True)
    return markup_phone


def markup_cancel():
    items = [
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_cancel = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_cancel


def markup_remove():
    markup_remove = ReplyKeyboardRemove()
    return markup_remove


def markup_confirm():
    items = [
        [KeyboardButton(text='✅ Да')],
        [KeyboardButton(text='❌ Отмена')]
    ]
    
    markup_confirm = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_confirm


def markup_custom(keyboard):
    """Create custom inline keyboard from JSON data"""
    if keyboard is None:
        return None
    
    # Handle inline_keyboard format
    if isinstance(keyboard, dict) and 'inline_keyboard' in keyboard:
        # Standard Telegram inline keyboard format
        items = []
        for row in keyboard['inline_keyboard']:
            button_row = []
            for button in row:
                if 'text' in button:
                    btn_params = {'text': button['text']}
                    # Add URL if present
                    if 'url' in button:
                        btn_params['url'] = button['url']
                    # Add callback_data if present
                    elif 'callback_data' in button:
                        btn_params['callback_data'] = button['callback_data']
                    button_row.append(InlineKeyboardButton(**btn_params))
            if button_row:
                items.append(button_row)
        return InlineKeyboardMarkup(inline_keyboard=items)
    
    # Fallback for legacy format (if any)
    return None


# Functions markup_editor and markup_edit removed - no longer needed
# Bot uses fixed linear navigation without dynamic step editing


# ===== NEW SHOP KEYBOARDS =====

def markup_main_menu(lang='ru'):
    """Main menu keyboard for shop"""
    from localization import get_text
    items = [
        [InlineKeyboardButton(text=get_text('btn_catalog', lang), callback_data='catalog')],
        [InlineKeyboardButton(text=get_text('btn_my_lessons', lang), callback_data='my_lessons')],
        [InlineKeyboardButton(text=get_text('btn_support', lang), callback_data='support')]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=items)


async def markup_catalog(lessons):
    """Catalog keyboard with lessons"""
    items = []
    
    for lesson in lessons:
        # Show price in USD and Stars
        price_usd = float(lesson['price_usd'])
        price_stars = await utils.calculate_stars_price(price_usd)
        
        if lesson['is_free']:
            button_text = f"🎁 {lesson['title']} (FREE)"
        else:
            button_text = f"📚 {lesson['title']} (${price_usd:.2f})"
            
        items.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"lesson:{lesson['id']}"
        )])
    
    # Back button
    from localization import get_text
    items.append([InlineKeyboardButton(
        text=get_text('btn_back', 'ru'), 
        callback_data='back_main'
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lesson_details(lesson_id, user_has_lesson=False, show_promocode=True, lang='ru'):
    """Lesson details keyboard"""
    from localization import get_text
    items = []
    if not user_has_lesson:
        items.append([InlineKeyboardButton(
            text=get_text('btn_buy', lang), 
            callback_data=f"buy:{lesson_id}"
        )])
        if show_promocode:
            items.append([InlineKeyboardButton(
                text='🎟️ Промокод', 
                callback_data=f"promocode:{lesson_id}"
            )])
    items.append([InlineKeyboardButton(
        text=get_text('btn_back', lang), 
        callback_data='catalog'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_my_lessons(lessons):
    """My lessons keyboard"""
    items = []
    for lesson in lessons:
        items.append([InlineKeyboardButton(
            text=f"📚 {lesson['title']}", 
            callback_data=f"view_lesson:{lesson['id']}"
        )])
    from localization import get_text
    items.append([InlineKeyboardButton(
        text=get_text('btn_back', 'ru'), 
        callback_data='back_main'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_payment_confirm(lesson_id, price_usd, price_stars, promocode=None):
    """Payment confirmation keyboard"""
    from localization import BACK_ICON
    items = [
        [InlineKeyboardButton(
            text=f"💳 Оплатить {price_stars} ⭐", 
            callback_data=f"pay:{lesson_id}:{promocode or 'none'}"
        )],
        [InlineKeyboardButton(
            text=f'{BACK_ICON} Назад', 
            callback_data=f"lesson:{lesson_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_back_to_lesson(lesson_id):
    """Simple back to lesson keyboard"""
    from localization import BACK_ICON
    items = [
        [InlineKeyboardButton(
            text=f'{BACK_ICON} Назад', 
            callback_data=f"lesson:{lesson_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== ADMIN SHOP KEYBOARDS =====

def markup_admin_shop(user_id):
    """Admin panel keyboard for shop - ALWAYS IN RUSSIAN"""
    items = [
        [InlineKeyboardButton(text='📤 Рассылка', callback_data='mail')], 
        [InlineKeyboardButton(text='📚 Управление уроками', callback_data='lessons_mgmt')],
        [InlineKeyboardButton(text='🎫 Поддержка', callback_data='admin_support')],
        [InlineKeyboardButton(text='📊 Статистика', callback_data='statistics')],
        [
            InlineKeyboardButton(text='⛙️ Настройки', callback_data='settings'),
            InlineKeyboardButton(text='🎫 Промокоды', callback_data='promocodes')
        ]
    ]
    
    if user_id in config.ADMINS:
        items.append([InlineKeyboardButton(text='🔑 Выдать / Забрать права администратора', callback_data='adminRights')]) 
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lessons_management():
    """Lessons management keyboard - ALWAYS IN RUSSIAN"""
    items = [
        [InlineKeyboardButton(text='➕ Добавить урок', callback_data='add_lesson')],
        [InlineKeyboardButton(text='✏️ Редактировать урок', callback_data='edit_lesson')],
        [InlineKeyboardButton(text='🗑️ Удалить урок', callback_data='delete_lesson')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_admin_settings():
    """Admin settings keyboard - ALWAYS IN RUSSIAN"""
    items = [
        [InlineKeyboardButton(text='💱 Курс валют', callback_data='currency_rate')],
        [InlineKeyboardButton(text='📝 Настройки текстов', callback_data='text_settings')],
        [InlineKeyboardButton(text='🌍 Переводы', callback_data='translations')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lesson_edit_list(lessons):
    """List of lessons for editing"""
    items = []
    for lesson in lessons:
        status = "🟢" if lesson['is_active'] else "🔴"
        price_text = "FREE" if lesson['is_free'] else f"${lesson['price_usd']}"
        items.append([InlineKeyboardButton(
            text=f"{status} {lesson['title']} ({price_text})", 
            callback_data=f"edit_lesson_id:{lesson['id']}"
        )])
    items.append([InlineKeyboardButton(
        text='↪️ Назад', 
        callback_data='edit_lesson'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lesson_edit_fields(lesson_id):
    """Edit lesson fields keyboard"""
    items = [
        [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_field:title:{lesson_id}")],
        [InlineKeyboardButton(text="📋 Описание", callback_data=f"edit_field:description:{lesson_id}")],
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field:price:{lesson_id}")],
        [InlineKeyboardButton(text="🎬 Видео", callback_data=f"edit_field:video:{lesson_id}")],
        [InlineKeyboardButton(text="🎭 Превью", callback_data=f"edit_field:preview:{lesson_id}")],
        [
            InlineKeyboardButton(text="✅ Активность", callback_data=f"toggle_active:{lesson_id}"),
            InlineKeyboardButton(text="🎁 Бесплатный", callback_data=f"toggle_free:{lesson_id}")
        ],
        [InlineKeyboardButton(
            text='↪️ Назад', 
            callback_data='edit_lesson'
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_promocodes_management():
    """Promocodes management keyboard - ALWAYS IN RUSSIAN"""
    items = [
        [InlineKeyboardButton(text='➕ Добавить промокод', callback_data='add_promocode')],
        [InlineKeyboardButton(text='📋 Список промокодов', callback_data='list_promocodes')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== SUPPORT SYSTEM KEYBOARDS =====

def markup_support_menu():
    """Support menu for users"""
    items = [
        [InlineKeyboardButton(text='🎫 Создать тикет', callback_data='create_ticket')],
        [InlineKeyboardButton(text='📋 Мои тикеты', callback_data='my_tickets')],
        [InlineKeyboardButton(text='⬅️ Назад', callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_user_tickets(tickets):
    """User tickets list keyboard"""
    items = []
    for ticket in tickets:
        status_emoji = {
            'open': '🟢',
            'in_progress': '🟡', 
            'closed': '🔴'
        }.get(ticket['status'], '⚪')
        button_text = f"{status_emoji} #{ticket['id']} - {ticket['subject'][:30]}{'...' if len(ticket['subject']) > 30 else ''}"
        items.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"view_ticket:{ticket['id']}"
        )])
    items.append([InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='support'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_ticket_details(ticket_id, is_closed=False):
    """Ticket details keyboard for user"""
    items = []
    if not is_closed:
        items.append([InlineKeyboardButton(
            text="💬 Посмотреть переписку",
            callback_data=f"ticket_conversation:{ticket_id}"
        )])
    items.append([InlineKeyboardButton(
        text='⬅️ Назад',
        callback_data='my_tickets'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== ADMIN SUPPORT KEYBOARDS =====

def markup_admin_support_dashboard():
    """Admin support dashboard keyboard - ALWAYS IN RUSSIAN"""
    items = [
        [InlineKeyboardButton(text='🟢 Открытые тикеты', callback_data='tickets_open')],
        [InlineKeyboardButton(text='🟡 В работе', callback_data='tickets_in_progress')],
        [InlineKeyboardButton(text='🔴 Закрытые тикеты', callback_data='tickets_closed')],
        [InlineKeyboardButton(text='📊 Статистика поддержки', callback_data='support_stats')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_admin_tickets_list(tickets):
    """Admin tickets list keyboard"""
    items = []
    for ticket in tickets:
        status_emoji = {
            'open': '🟢',
            'in_progress': '🟡',
            'closed': '🔴'
        }.get(ticket['status'], '⚪')
        priority_emoji = {
            'urgent': '🔥',
            'high': '⚠️',
            'normal': '',
            'low': '🔽'
        }.get(ticket['priority'], '')
        button_text = f"{status_emoji}{priority_emoji} #{ticket['id']} - {ticket['subject'][:25]}{'...' if len(ticket['subject']) > 25 else ''}"
        items.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"admin_ticket:{ticket['id']}"
        )])
    items.append([InlineKeyboardButton(
        text='↪️ Назад',
        callback_data='admin_support'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_admin_ticket_actions(ticket_id, is_closed=False):
    """Admin ticket actions keyboard"""
    items = []
    if not is_closed:
        items.extend([
            [InlineKeyboardButton(text='💬 Ответить', callback_data=f'respond_ticket:{ticket_id}')],
            [InlineKeyboardButton(text='✅ Закрыть тикет', callback_data=f'close_ticket:{ticket_id}')],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f'change_status:{ticket_id}')]
        ])
    items.extend([
        [InlineKeyboardButton(text="💬 Показать переписку", callback_data=f'ticket_conversation:{ticket_id}')],
        [InlineKeyboardButton(text='↪️ Назад', callback_data='admin_support')]
    ])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_text_categories():
    """Markup for text categories selection"""
    # не отображать без прямого указания, это тестовый функционал не для продакшена
    items = [
        [InlineKeyboardButton(text="🔘 Кнопки", callback_data='text_category:buttons')],
        [InlineKeyboardButton(text="💬 Сообщения", callback_data='text_category:messages')],
        [InlineKeyboardButton(text="👨‍💼 Админ", callback_data='text_category:admin')],
        [InlineKeyboardButton(text="📧 Почта", callback_data='text_category:mail')],
        [InlineKeyboardButton(text="↩️ Назад к настройкам", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_text_keys(category):
    """Markup for text keys in selected category"""
    texts = utils.get_interface_texts()
    if category not in texts:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Категория не найдена", callback_data='text_settings')]])
    
    keys = list(texts[category].keys())
    items = []
    for key in keys:
        value = texts[category][key]
        # Log type for diagnostics
        logging.info(f"Value type for key '{key}' in category '{category}': {type(value)}")
        # Type check and fallback
        if not isinstance(value, str):
            logging.warning(f"Non-string value for key '{key}' in category '{category}': {value}. Converting to str.")
            value = str(value)
        short_value = value[:20] + '...' if len(value) > 20 else value
        items.append([InlineKeyboardButton(text=f"{key}: {short_value}", callback_data=f'text_key:{category}:{key}')])
    
    items.append([InlineKeyboardButton(text="↩️ Назад к категориям", callback_data='text_settings')])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_text_edit(key, category):
    """Markup for editing specific text key"""
    items = [
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f'text_edit:{category}:{key}')],
        [InlineKeyboardButton(text="↩️ Назад к ключам", callback_data=f'text_category:{category}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)
