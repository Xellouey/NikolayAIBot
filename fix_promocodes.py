#!/usr/bin/env python
# -*- coding: utf-8 -*-

from database.lesson import Promocode, con
from decimal import Decimal

def fix_promocodes():
    """Fix existing promocodes with correct discount values"""
    try:
        con.connect()
        print("✅ Подключение к базе данных успешно")
        
        # Исправляем TEST промокод - допустим, это должно быть 20%
        test_promocode = Promocode.get(Promocode.code == 'TEST')
        test_promocode.discount_value = Decimal('0.20')  # 20% сохраняем как долю
        test_promocode.save()
        print("✅ TEST промокод исправлен на 20%")
        
        # Исправляем SALE20 промокод - судя по названию, это должно быть 20%
        sale_promocode = Promocode.get(Promocode.code == 'SALE20')
        sale_promocode.discount_value = Decimal('0.20')  # 20% сохраняем как долю
        sale_promocode.save()
        print("✅ SALE20 промокод исправлен на 20%")
        
        # Проверяем результат
        promocodes = list(Promocode.select().dicts())
        print(f"\n📋 Обновленная информация о промокодах:")
        for p in promocodes:
            discount_value = float(p.get('discount_value', 0))
            if p.get('discount_type') == 'percentage':
                discount_percent = discount_value * 100 if discount_value <= 1 else discount_value
                discount_text = f"{int(discount_percent)}%" if discount_percent.is_integer() else f"{discount_percent:.1f}%"
            else:
                discount_text = f"${discount_value:.2f}"
            
            print(f"  - {p.get('code')}: {discount_text} (активен={p.get('is_active')})")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not con.is_closed():
            con.close()
        print("🔒 Соединение закрыто")

if __name__ == "__main__":
    fix_promocodes()