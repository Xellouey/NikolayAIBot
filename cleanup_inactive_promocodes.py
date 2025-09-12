#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Одноразовая очистка: удаляет все промокоды, ранее помеченные как неактивные (is_active = 0).
Запуск: python cleanup_inactive_promocodes.py
"""

from database.lesson import Promocode, con


def main():
    try:
        con.connect()
        # Создаём таблицу, если её нет (на всякий случай)
        Promocode.create_table(safe=True)

        before_total = Promocode.select().count()
        before_inactive = Promocode.select().where(Promocode.is_active == False).count()

        deleted = Promocode.delete().where(Promocode.is_active == False).execute()

        after_total = Promocode.select().count()
        print("🧹 Очистка завершена")
        print(f"   Было записей: {before_total}")
        print(f"   Неактивных до очистки: {before_inactive}")
        print(f"   Удалено: {deleted}")
        print(f"   Осталось записей: {after_total}")
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
    finally:
        try:
            con.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

