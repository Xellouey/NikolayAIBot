#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.lesson import Promocode
import asyncio
from decimal import Decimal

async def test_promocode_creation():
    """Test promocode creation and display"""
    
    promo = Promocode()
    
    print("🧪 Тестирование создания и отображения промокодов...")
    
    # Тестируем создание процентного промокода 30%
    print("\n📋 Создание процентного промокода...")
    try:
        await promo.create_promocode(
            code="TEST30",
            discount_type="percentage", 
            discount_value=Decimal("0.30"),  # 30% как доля
            usage_limit=5
        )
        print("✅ Процентный промокод TEST30 создан")
    except Exception as e:
        print(f"❌ Ошибка создания процентного промокода: {e}")
    
    # Тестируем создание фиксированного промокода $10
    print("\n📋 Создание фиксированного промокода...")
    try:
        await promo.create_promocode(
            code="SAVE10",
            discount_type="fixed",
            discount_value=Decimal("10.00"),  # $10 фиксированная скидка
            usage_limit=None  # без лимита
        )
        print("✅ Фиксированный промокод SAVE10 создан")
    except Exception as e:
        print(f"❌ Ошибка создания фиксированного промокода: {e}")
    
    # Получаем все промокоды и проверяем отображение
    print("\n📋 Проверка отображения всех промокодов:")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    promocodes = await promo.get_all_promocodes()
    
    for p in promocodes:
        if not p.get('is_active', False):
            continue
            
        # Правильно получаем данные о скидке из базы
        discount_type = p.get('discount_type', 'percentage')
        discount_value = p.get('discount_value', 0)
        
        # Форматируем скидку для отображения
        if discount_type == 'percentage':
            # Для процентных скидок конвертируем из доли в проценты
            discount_percent = float(discount_value) * 100 if float(discount_value) <= 1 else float(discount_value)
            discount_text = f"{int(discount_percent)}%" if discount_percent.is_integer() else f"{discount_percent:.1f}%"
        else:  # fixed
            # Для фиксированных скидок отображаем в долларах
            discount_amount = float(discount_value)
            discount_text = f"${int(discount_amount)}" if discount_amount.is_integer() else f"${discount_amount:.2f}"
        
        usage_count = p.get('used_count', 0)
        usage_limit = p.get('usage_limit')
        usage_text = f"{usage_count}/{usage_limit if usage_limit else '∞'}"
        
        # Проверяем срок действия
        expires_at = p.get('expires_at')
        if expires_at:
            from datetime import datetime
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            expires_text = f"до {expires_at.strftime('%d.%m.%Y')}"
        else:
            expires_text = "бессрочно"
        
        print(f"🎫 {p.get('code', 'N/A')}")
        print(f"   💰 Скидка: {discount_text}")
        print(f"   📊 Использовано: {usage_text}")
        print(f"   ⏰ Срок: {expires_text}")
        print()
    
    print("━━━━━━━━━━━━━━━━━━━━")
    print("✅ Тест создания и отображения промокодов завершен")

if __name__ == "__main__":
    asyncio.run(test_promocode_creation())