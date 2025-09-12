#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_promocode_table_structure():
    """Check actual promocode table structure"""
    db_path = 'shop_bot.db'
    
    try:
        con = sqlite3.connect(db_path)
        cursor = con.cursor()
        
        # Получаем структуру таблицы promocode
        cursor.execute("PRAGMA table_info(promocode)")
        columns = cursor.fetchall()
        
        print("📋 Структура таблицы promocode:")
        print("━━━━━━━━━━━━━━━━━━━━")
        for col in columns:
            print(f"{col[1]} ({col[2]}) - NULL={col[3]==0} - DEFAULT={col[4]}")
        
        print("\n📊 Данные в таблице promocode:")
        print("━━━━━━━━━━━━━━━━━━━━")
        cursor.execute("SELECT * FROM promocode")
        rows = cursor.fetchall()
        
        # Получаем названия колонок
        column_names = [description[0] for description in cursor.description]
        print("Колонки:", column_names)
        
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        con.close()

if __name__ == "__main__":
    check_promocode_table_structure()