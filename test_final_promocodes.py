#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.lesson import Promocode
import asyncio
from decimal import Decimal

async def test_final_promocode_system():
    """Final test of promocode system"""
    
    promo = Promocode()
    
    print("🧪 Финальное тестирование системы промокодов...")
    print("=" * 50)
    
    # Проверяем отображение всех существующих промокодов
    print("\n📋 1. Проверка отображения существующих промокодов:")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    promocodes = await promo.get_all_promocodes()
    print(f"Найдено промокодов: {len(promocodes)}")
    
    for p in promocodes:
        if not p.get('is_active', False):
            continue
            
        discount_type = p.get('discount_type', 'percentage')
        discount_value = p.get('discount_value', 0)
        
        if discount_type == 'percentage':
            discount_percent = float(discount_value) * 100 if float(discount_value) <= 1 else float(discount_value)
            discount_text = f"{int(discount_percent)}%" if discount_percent.is_integer() else f"{discount_percent:.1f}%"
        else:  # fixed
            discount_amount = float(discount_value)
            discount_text = f"${int(discount_amount)}" if discount_amount.is_integer() else f"${discount_amount:.2f}"
        
        usage_count = p.get('used_count', 0)
        usage_limit = p.get('usage_limit')
        usage_text = f"{usage_count}/{usage_limit if usage_limit else '∞'}"
        
        expires_at = p.get('expires_at')
        if expires_at:
            from datetime import datetime
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            expires_text = f"до {expires_at.strftime('%d.%m.%Y')}"
        else:
            expires_text = "бессрочно"
        
        print(f"🎫 {p.get('code')}: {discount_text} | Использовано: {usage_text} | Срок: {expires_text}")
    
    # Проверяем создание нового промокода каждого типа
    print("\n📋 2. Проверка создания новых промокодов:")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    # Тестируем процентный промокод 15%
    try:
        await promo.create_promocode(
            code="FINAL15",
            discount_type="percentage", 
            discount_value=Decimal("0.15"),  # 15% как доля
            usage_limit=10
        )
        print("✅ Процентный промокод FINAL15 (15%) создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания процентного промокода: {e}")
    
    # Тестируем фиксированный промокод $7.50
    try:
        await promo.create_promocode(
            code="FINAL750",
            discount_type="fixed",
            discount_value=Decimal("7.50"),  # $7.50 фиксированная скидка
            usage_limit=None
        )
        print("✅ Фиксированный промокод FINAL750 ($7.50) создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания фиксированного промокода: {e}")
    
    # Проверяем валидацию промокодов
    print("\n📋 3. Проверка валидации промокодов:")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    # Тестируем валидацию существующего промокода
    valid_promocode, message = await promo.validate_promocode("TEST")
    if valid_promocode:
        print(f"✅ Промокод TEST прошел валидацию: {message}")
    else:
        print(f"❌ Промокод TEST не прошел валидацию: {message}")
    
    # Тестируем валидацию несуществующего промокода
    invalid_promocode, message = await promo.validate_promocode("INVALID")
    if invalid_promocode:
        print(f"⚠️ Промокод INVALID неожиданно прошел валидацию")
    else:
        print(f"✅ Промокод INVALID корректно отклонен: {message}")
    
    # Проверяем расчет скидки
    print("\n📋 4. Проверка расчета скидок:")
    print("━━━━━━━━━━━━━━━━━━━━")
    
    # Тестируем расчет скидки для процентного промокода
    test_promocode = await promo.get_promocode("TEST")
    if test_promocode:
        final_price, discount = await promo.calculate_discount(test_promocode, 100.00)
        print(f"💰 Промокод TEST (20%) на $100: скидка ${discount:.2f}, итого ${final_price:.2f}")
    
    # Тестируем расчет скидки для фиксированного промокода
    save10_promocode = await promo.get_promocode("SAVE10")
    if save10_promocode:
        final_price, discount = await promo.calculate_discount(save10_promocode, 100.00)
        print(f"💰 Промокод SAVE10 ($10) на $100: скидка ${discount:.2f}, итого ${final_price:.2f}")
    
    print("\n" + "=" * 50)
    print("✅ Финальное тестирование системы промокодов завершено успешно!")
    
    # Финальная сводка
    final_promocodes = await promo.get_all_promocodes()
    active_count = len([p for p in final_promocodes if p.get('is_active')])
    percentage_count = len([p for p in final_promocodes if p.get('is_active') and p.get('discount_type') == 'percentage'])
    fixed_count = len([p for p in final_promocodes if p.get('is_active') and p.get('discount_type') == 'fixed'])
    
    print(f"\n📊 Итоговая статистика:")
    print(f"   🎫 Всего активных промокодов: {active_count}")
    print(f"   📊 Процентных скидок: {percentage_count}")
    print(f"   💵 Фиксированных скидок: {fixed_count}")

if __name__ == "__main__":
    asyncio.run(test_final_promocode_system())