import json
from decimal import Decimal
from datetime import datetime, timedelta
from database.lesson import SystemSettings, Translations
from peewee import DoesNotExist
import re
import logging


# Steps functionality removed - using fixed flow
        
        
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
        
        
# Step manipulation functions removed - using fixed flow


# get_text function removed - use localization.get_text instead

# Interface texts functionality removed - use localization module instead


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
