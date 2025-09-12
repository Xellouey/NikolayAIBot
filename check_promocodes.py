#!/usr/bin/env python
# -*- coding: utf-8 -*-

from database.lesson import Promocode, con

def check_promocodes():
    """Check promocodes table and data"""
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
            print("\n📋 Список промокодов:")
            for p in promocodes:
                print(f"  - {p.get('code')}: {p.get('discount_value')}% активен={p.get('is_active')}")
        else:
            print("ℹ️ Промокодов пока нет в базе данных")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        con.close()
        print("🔒 Соединение закрыто")

if __name__ == "__main__":
    check_promocodes()
