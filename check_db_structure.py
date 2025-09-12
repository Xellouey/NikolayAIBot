#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для проверки структуры таблиц в базе данных
"""

import sqlite3
import os

def check_db_structure():
    """Проверяет структуру базы данных"""
    db_path = 'database/school.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем таблицу promocode
    print("=" * 60)
    print("Проверка таблицы 'promocode':")
    print("=" * 60)
    
    try:
        cursor.execute("PRAGMA table_info(promocode)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Таблица 'promocode' не найдена")
        else:
            print("✅ Таблица 'promocode' найдена")
            print("\nСтолбцы таблицы:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} default={col[4]}")
            
            # Проверяем наличие данных
            cursor.execute("SELECT COUNT(*) FROM promocode")
            count = cursor.fetchone()[0]
            print(f"\nКоличество записей: {count}")
            
            # Показываем первые несколько записей
            if count > 0:
                cursor.execute("SELECT * FROM promocode LIMIT 3")
                rows = cursor.fetchall()
                print("\nПримеры записей:")
                for row in rows:
                    print(f"  {row}")
    except Exception as e:
        print(f"❌ Ошибка при проверке таблицы promocode: {e}")
    
    # Проверяем таблицу systemsettings
    print("\n" + "=" * 60)
    print("Проверка таблицы 'systemsettings':")
    print("=" * 60)
    
    try:
        cursor.execute("PRAGMA table_info(systemsettings)")
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Таблица 'systemsettings' не найдена")
        else:
            print("✅ Таблица 'systemsettings' найдена")
            print("\nСтолбцы таблицы:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} default={col[4]}")
    except Exception as e:
        print(f"❌ Ошибка при проверке таблицы systemsettings: {e}")
    
    conn.close()
    print("\n" + "=" * 60)
    print("Проверка завершена")
    print("=" * 60)

if __name__ == "__main__":
    check_db_structure()
