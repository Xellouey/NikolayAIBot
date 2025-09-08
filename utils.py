import json
from decimal import Decimal
from datetime import datetime, timedelta
from database.lesson import SystemSettings
import re
import logging


def get_steps(filename="json/steps.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            steps = json.load(f)
        return steps
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {filename}.  Возвращается пустой словарь.")
        return {}


def update_steps(new_steps, filename="json/steps.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(new_steps, f, indent=4, ensure_ascii=False)
        
        
def get_admins(filename="json/admins.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            admins = json.load(f)
        return admins
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла {filename}.  Возвращается пустой список.")
        return []


def update_admins(new_admins, filename="json/admins.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(new_admins, f, indent=4, ensure_ascii=False)
        
        
def move_dict_item(dictionary, key, new_position):
    if key not in dictionary:
        raise KeyError(f"Key '{key}' not found in dictionary")
    
    # Проверяем границы с учетом того, что позиция может быть от 0 до len(dictionary)
    if new_position < 0 or new_position > len(dictionary):
        print(f"⚠️ Предупреждение: Позиция {new_position} вне границ (0-{len(dictionary)}). Используется ближайшая допустимая позиция.")
        new_position = max(0, min(new_position, len(dictionary) - 1))
    
    # Если позиция равна длине словаря, ставим в конец
    if new_position >= len(dictionary):
        new_position = len(dictionary) - 1
    
    items = list(dictionary.items())
    
    current_position = next(i for i, (k, _) in enumerate(items) if k == key)
    
    if current_position == new_position:
        return dictionary
    
    item = items.pop(current_position)
    items.insert(new_position, item)
    
    return dict(items)


def remove_dict_item(dictionary, key):
    if key not in dictionary:
        raise KeyError(f"Key '{key}' not found in dictionary")
    
    new_dict = dictionary.copy()
    del new_dict[key]
    return new_dict


def get_new_key():
    steps = get_steps()
    
    keys = list(steps.keys())
    last_key = keys[-1]

    if 'step' not in last_key:
        key = f'step1'
    else:
        new_index = int(last_key.split('step')[1]) + 1
        key = f'step{new_index}'
                
    return key


def get_interface_texts(filename="json/interface_texts.json"):
    """Get interface texts from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            texts = json.load(f)
        
        # Runtime validation
        def validate_texts(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    new_path = f"{path}.{key}" if path else key
                    if not validate_texts(value, new_path):
                        return False
                return True
            elif isinstance(data, str):
                return True
            else:
                logging.error(f"Invalid type {type(data)} at path {path}: {data}")
                return False
        
        if not validate_texts(texts):
            logging.warning("Interface texts validation failed, using fallback defaults")
            # Fallback default texts (minimal set)
            texts = {
                "buttons": {"back": "🔙 Назад"},
                "messages": {"welcome": "Добро пожаловать!"},
                "admin": {"messages": {"lesson_management": "Управление уроками"}}
            }
        
        return texts
    except FileNotFoundError:
        logging.warning(f"Interface texts file not found: {filename}, using fallback")
        # Fallback default texts
        return {
            "buttons": {"back": "🔙 Назад"},
            "messages": {"welcome": "Добро пожаловать!"},
            "admin": {"messages": {"lesson_management": "Управление уроками"}}
        }
    except json.JSONDecodeError:
        logging.error(f"JSON decode error in {filename}, using fallback")
        return {
            "buttons": {"back": "🔙 Назад"},
            "messages": {"welcome": "Добро пожаловать!"},
            "admin": {"messages": {"lesson_management": "Управление уроками"}}
        }


def update_interface_texts(new_texts, filename="json/interface_texts.json"):
    """Update interface texts JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(new_texts, f, indent=4, ensure_ascii=False)


def get_text(path, **kwargs):
    """Get text by path with formatting
    
    Args:
        path: dot-separated path like 'messages.welcome' or 'buttons.back'
        **kwargs: format arguments for text
    
    Returns:
        Formatted text or path if not found
    """
    texts = get_interface_texts()
    
    # Navigate through nested dict using path
    current = texts
    for key in path.split('.'):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return path  # Return path if not found
    
    # Format text if it's a string and has format args
    if isinstance(current, str) and kwargs:
        try:
            return current.format(**kwargs)
        except (KeyError, ValueError):
            return current
    
    return current


async def calculate_stars_price(usd_price):
    """Calculate price in Telegram Stars from USD
    
    Args:
        usd_price: Price in USD (float or Decimal)
    
    Returns:
        Price in Stars (int)
    """
    s = SystemSettings()
    exchange_rate = await s.get_usd_to_stars_rate()
    
    if isinstance(usd_price, str):
        usd_price = Decimal(usd_price)
    elif isinstance(usd_price, float):
        usd_price = Decimal(str(usd_price))
    
    stars_price = int(usd_price * exchange_rate)
    return max(1, stars_price)  # Minimum 1 star


def format_currency(amount, currency='USD'):
    """Format currency amount
    
    Args:
        amount: Amount to format
        currency: Currency code (USD, RUB, etc.)
    
    Returns:
        Formatted string
    """
    if currency == 'USD':
        return f"${amount:.2f}"
    elif currency == 'RUB':
        return f"{amount:.2f} ₽"
    else:
        return f"{amount:.2f} {currency}"


def get_period_start(days):
    """Get start date for period statistics
    
    Args:
        days: Number of days back (1 for today, 7 for week, etc.)
    
    Returns:
        datetime object
    """
    if days == 1:
        # Today from 00:00
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # N days ago from 00:00
        return (datetime.now() - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)


def validate_html_text(text: str, max_length: int = 4096) -> bool:
    """
    Validate HTML text for Telegram compatibility.
    
    Checks:
    - Text length <= max_length
    - Balanced opening/closing tags: b, i, u, s, code, pre, a
    - For <a> tags, valid href attribute
    - No invalid characters or malformed tags
    
    Args:
        text: HTML text to validate
        max_length: Maximum allowed length (default 4096 for Telegram)
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    if len(text) > max_length:
        return False
    
    # Telegram allowed tags
    allowed_tags = {'b', 'i', 'u', 's', 'code', 'pre', 'a'}
    
    # Remove content between tags for tag balance check
    # Simple stack-based tag balancer
    tag_stack = []
    tag_pattern = re.compile(r'<(/?)([a-zA-Z]+)(?:\s+href="([^"]*)")?\s*/?>', re.IGNORECASE)
    
    for match in tag_pattern.finditer(text):
        tag_name = match.group(2).lower()
        is_closing = bool(match.group(1))
        href = match.group(3)
        
        if tag_name not in allowed_tags:
            return False
        
        if is_closing:
            if not tag_stack or tag_stack[-1] != tag_name:
                return False  # Mismatched closing tag
            tag_stack.pop()
        else:
            if tag_name == 'a':
                if not href or not re.match(r'^https?://', href):
                    return False  # Invalid href for <a>
            tag_stack.append(tag_name)
    
    # Check if all tags are closed
    if tag_stack:
        return False
    
    # Check for invalid characters (basic: no control chars except \n)
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text):
        return False
    
    return True
