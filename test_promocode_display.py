#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.lesson import Promocode
import asyncio

async def test_promocode_display():
    """Test promocode display functionality"""
    
    promo = Promocode()
    
    print("🧪 Тестирование отображения промокодов...")
    
    # Получаем все промокоды
    promocodes = await promo.get_all_promocodes()
    print(f"📊 Найдено промокодов: {len(promocodes)}")
    
    if promocodes:
        print("\n📋 Тестирование отображения промокодов:")
        print("━━━━━━━━━━━━━━━━━━━━")
        
        for p in promocodes:
            # Только активные промокоды
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
            
            usage_count = p.get('used_count', 0)  # Правильное поле - used_count, а не usage_count
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
    else:
        print("📭 Промокодов пока нет")
    
    print("━━━━━━━━━━━━━━━━━━━━")
    print("✅ Тест отображения промокодов завершен")

if __name__ == "__main__":
    asyncio.run(test_promocode_display())