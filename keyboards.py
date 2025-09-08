import config
import logging
import utils
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
    if keyboard == None:
        return None
    
    items = []

    for button in keyboard:
        for name in button:
            url = button[name]
            items.append([InlineKeyboardButton(text=name, url=url)])
        
    markup_custom = InlineKeyboardMarkup(inline_keyboard=items)
    return markup_custom


def markup_editor():
    items = [
        [
            InlineKeyboardButton(text='➕ Создать шаг', callback_data='createStep')
        ],
        [
            InlineKeyboardButton(text='🤝 Вступление', callback_data='edit:join'),
            InlineKeyboardButton(text='👋 Старт', callback_data='edit:start')
        ]
    ]
    
    steps = utils.get_steps()
    s_list = list(steps.keys())
    
    try:
        step_bot = s_list[2:]
    except:
        step_bot = []
        
    row = []
    
    i = 1
    for step in step_bot:
        row.append(InlineKeyboardButton(text=f"👟 Шаг{i}", callback_data=f"edit:{step}"))
        
        if len(row) == 2:
            items.append(row)
            row = []
            
        i += 1
            
    if row != []:
        items.append(row)
        
    items.append([InlineKeyboardButton(text='↪️ Назад', callback_data='backAdmin')])
    
    markup_editor = InlineKeyboardMarkup(inline_keyboard=items)
    return markup_editor


def markup_edit(disable_default=False):
    items = [
        [KeyboardButton(text='👟 Шаг')]
    ]
    
    if disable_default == False:
        items.extend((
            [
                KeyboardButton(text='🖌 Позицию'),
                KeyboardButton(text='⏳ Задержку')
            ],
            [
                KeyboardButton(text='🔗 Кнопки'),
                KeyboardButton(text='⛔️ Удалить')
            ]
        ))
        
    items.append([KeyboardButton(text='❌ Отмена')])
    
    markup_edit = ReplyKeyboardMarkup(keyboard=items, resize_keyboard=True)
    return markup_edit


# ===== NEW SHOP KEYBOARDS =====

def markup_main_menu():
    """Main menu keyboard for shop"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('buttons.catalog')), callback_data='catalog')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.my_lessons')), callback_data='my_lessons')],
        [
            InlineKeyboardButton(text=str(utils.get_text('buttons.profile')), callback_data='profile'),
            InlineKeyboardButton(text=str(utils.get_text('buttons.support')), callback_data='support')
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_catalog(lessons):
    """Catalog keyboard with lessons"""
    items = []
    
    for lesson in lessons:
        # Show price in USD and Stars
        price_usd = float(lesson['price_usd'])
        price_stars = utils.calculate_stars_price(price_usd)
        
        if lesson['is_free']:
            button_text = f"🎁 {lesson['title']} (FREE)"
        else:
            button_text = f"📚 {lesson['title']} (${price_usd:.2f})"
            
        items.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"lesson:{lesson['id']}"
        )])
    
    # Back button
    items.append([InlineKeyboardButton(
        text=str(utils.get_text('buttons.back')), 
        callback_data='back_main'
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lesson_details(lesson_id, user_has_lesson=False, show_promocode=True):
    """Lesson details keyboard"""
    items = []
    if not user_has_lesson:
        items.append([InlineKeyboardButton(
            text=str(utils.get_text('buttons.buy')), 
            callback_data=f"buy:{lesson_id}"
        )])
        if show_promocode:
            items.append([InlineKeyboardButton(
                text=str(utils.get_text('buttons.enter_promocode')), 
                callback_data=f"promocode:{lesson_id}"
            )])
    items.append([InlineKeyboardButton(
        text=str(utils.get_text('buttons.back')), 
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
    items.append([InlineKeyboardButton(
        text=str(utils.get_text('buttons.back')), 
        callback_data='back_main'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_payment_confirm(lesson_id, price_usd, price_stars, promocode=None):
    """Payment confirmation keyboard"""
    items = [
        [InlineKeyboardButton(
            text=f"💳 Оплатить {price_stars} ⭐", 
            callback_data=f"pay:{lesson_id}:{promocode or 'none'}"
        )],
        [InlineKeyboardButton(
            text=str(utils.get_text('buttons.back')), 
            callback_data=f"lesson:{lesson_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_back_to_lesson(lesson_id):
    """Simple back to lesson keyboard"""
    items = [
        [InlineKeyboardButton(
            text=str(utils.get_text('buttons.back')), 
            callback_data=f"lesson:{lesson_id}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== ADMIN SHOP KEYBOARDS =====

def markup_admin_shop(user_id):
    """Admin panel keyboard for shop"""
    items = [
        [InlineKeyboardButton(text='📤 Рассылка', callback_data='mail')], 
        [InlineKeyboardButton(text='✏️ Редактор шагов', callback_data='editor')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.lessons_management')), callback_data='lessons_mgmt')],
        [InlineKeyboardButton(text='🎫 Поддержка', callback_data='admin_support')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.statistics')), callback_data='statistics')],
        [
            InlineKeyboardButton(text=str(utils.get_text('admin.buttons.settings')), callback_data='settings'),
            InlineKeyboardButton(text=str(utils.get_text('admin.buttons.promocodes')), callback_data='promocodes')
        ]
    ]
    
    if user_id in config.ADMINS:
        items.append([InlineKeyboardButton(text='🔑 Выдать / Забрать права администратора', callback_data='adminRights')]) 
    
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_lessons_management():
    """Lessons management keyboard"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.add_lesson')), callback_data='add_lesson')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.edit_lesson')), callback_data='edit_lesson')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.delete_lesson')), callback_data='delete_lesson')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_admin_settings():
    """Admin settings keyboard"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.currency_settings')), callback_data='currency_rate')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.text_settings')), callback_data='text_settings')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='backAdmin')]
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
        text=str(utils.get_text('admin.buttons.back_admin')), 
        callback_data='lessons_mgmt'
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
            text=str(utils.get_text('admin.buttons.back_admin')), 
            callback_data='edit_lesson'
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_promocodes_management():
    """Promocodes management keyboard"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.add_promocode')), callback_data='add_promocode')],
        [InlineKeyboardButton(text="📋 Список промокодов", callback_data='list_promocodes')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='backAdmin')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== SUPPORT SYSTEM KEYBOARDS =====

def markup_support_menu():
    """Support menu for users"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('buttons.create_ticket')), callback_data='create_ticket')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.my_tickets')), callback_data='my_tickets')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.back')), callback_data='back_main')]
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
        text=str(utils.get_text('buttons.back')),
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
        text=str(utils.get_text('buttons.back')),
        callback_data='my_tickets'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


# ===== ADMIN SUPPORT KEYBOARDS =====

def markup_admin_support_dashboard():
    """Admin support dashboard keyboard"""
    items = [
        [InlineKeyboardButton(text=str(utils.get_text('buttons.open_tickets')), callback_data='tickets_open')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.in_progress_tickets')), callback_data='tickets_in_progress')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.closed_tickets')), callback_data='tickets_closed')],
        [InlineKeyboardButton(text=str(utils.get_text('buttons.support_stats')), callback_data='support_stats')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='backAdmin')]
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
        text=str(utils.get_text('admin.buttons.back_admin')),
        callback_data='admin_support'
    )])
    return InlineKeyboardMarkup(inline_keyboard=items)


def markup_admin_ticket_actions(ticket_id, is_closed=False):
    """Admin ticket actions keyboard"""
    items = []
    if not is_closed:
        items.extend([
            [InlineKeyboardButton(text=str(utils.get_text('buttons.respond_ticket')), callback_data=f'respond_ticket:{ticket_id}')],
            [InlineKeyboardButton(text=str(utils.get_text('buttons.close_ticket')), callback_data=f'close_ticket:{ticket_id}')],
            [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f'change_status:{ticket_id}')]
        ])
    items.extend([
        [InlineKeyboardButton(text="💬 Показать переписку", callback_data=f'ticket_conversation:{ticket_id}')],
        [InlineKeyboardButton(text=str(utils.get_text('admin.buttons.back_admin')), callback_data='admin_support')]
    ])
    return InlineKeyboardMarkup(inline_keyboard=items)

def markup_text_categories():
    """Markup for text categories selection"""
    # не отображать без прямого указания, это тестовый функционал не для продакшена
    items = [
        [InlineKeyboardButton(text="🔘 Кнопки", callback_data='text_category:buttons')],
        [InlineKeyboardButton(text="💬 Сообщения", callback_data='text_category:messages')],
        # [InlineKeyboardButton(text="👨‍💼 Админ", callback_data='text_category:admin')],
        # [InlineKeyboardButton(text="📧 Почта", callback_data='text_category:mail')],
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