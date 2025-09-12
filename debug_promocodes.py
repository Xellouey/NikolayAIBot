#!/usr/bin/env python
# -*- coding: utf-8 -*-

from database.lesson import Promocode, con
import json

def debug_promocodes():
    """Debug promocodes data structure"""
    try:
        con.connect()
        print("✅ Подключение к базе данных успешно")
        
        # Создаем таблицу если её нет
        Promocode.create_table(safe=True)
        print("✅ Таблица promocode существует или создана")
        
        # Получаем все промокоды
        promocodes = list(Promocode.select().dicts())
        print(f"📊 Найдено промокодов: {len(promocodes)}")
        
        if promocodes:
            print("\n📋 Подробная информация о промокодах:")
            for p in promocodes:
                print(f"━━━━━━━━━━━━━━━━━━━━")
                print(f"Код: {p.get('code')}")
                print(f"Тип скидки: {p.get('discount_type')}")
                print(f"Значение скидки: {p.get('discount_value')} (тип: {type(p.get('discount_value'))})")
                print(f"Лимит использований: {p.get('usage_limit')}")
                print(f"Использовано: {p.get('used_count')}")
                print(f"Активен: {p.get('is_active')}")
                print(f"Срок действия: {p.get('expires_at')}")
                print(f"Создан: {p.get('created_at')}")
                print(f"\nВсе поля в JSON:")
                print(json.dumps(p, indent=2, default=str, ensure_ascii=False))
                print(f"━━━━━━━━━━━━━━━━━━━━\n")
        else:
            print("ℹ️ Промокодов пока нет в базе данных")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not con.is_closed():
            con.close()
        print("🔒 Соединение закрыто")

if __name__ == "__main__":
    debug_promocodes()