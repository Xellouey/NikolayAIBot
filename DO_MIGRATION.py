#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
АВТОМАТИЧЕСКАЯ МИГРАЦИЯ БАЗЫ ДАННЫХ
Запустите этот файл двойным кликом или командой: python DO_MIGRATION.py
"""

import sqlite3
import os
from datetime import datetime
import shutil
import sys

print("=" * 70)
print("     МИГРАЦИЯ БАЗЫ ДАННЫХ ДЛЯ ИСПРАВЛЕНИЯ ТАБЛИЦЫ PROMOCODE")
print("=" * 70)
print()

db_path = 'database/school.db'

# Создаём резервную копию
if os.path.exists(db_path):
    backup_name = f'database/school.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    print(f"[1/4] Creating backup: {backup_name}")
    shutil.copy2(db_path, backup_name)
    print("      ✓ Backup created successfully")
else:
    print(f"[1/4] Database not found at {db_path}, will create new")
    os.makedirs('database', exist_ok=True)

print()

# Подключаемся к БД
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("[2/4] Checking and updating promocode table...")

try:
    # Проверяем таблицу promocode
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promocode'")
    if cursor.fetchone() is None:
        # Создаём таблицу
        cursor.execute("""
            CREATE TABLE promocode (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(50) UNIQUE NOT NULL,
                discount_type VARCHAR(20) DEFAULT 'percentage',
                discount_value DECIMAL(10,2) DEFAULT 0,
                usage_limit INTEGER,
                usage_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("      ✓ Table promocode created")
    else:
        # Проверяем колонки
        cursor.execute("PRAGMA table_info(promocode)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        changes = []
        
        if 'discount_type' not in columns:
            cursor.execute("ALTER TABLE promocode ADD COLUMN discount_type VARCHAR(20) DEFAULT 'percentage'")
            changes.append("discount_type")
            
        if 'discount_value' not in columns:
            cursor.execute("ALTER TABLE promocode ADD COLUMN discount_value DECIMAL(10,2) DEFAULT 0")
            changes.append("discount_value")
            
        if 'usage_count' not in columns and 'used_count' in columns:
            cursor.execute("ALTER TABLE promocode ADD COLUMN usage_count INTEGER DEFAULT 0")
            cursor.execute("UPDATE promocode SET usage_count = used_count")
            changes.append("usage_count")
        
        if changes:
            print(f"      ✓ Added columns: {', '.join(changes)}")
        else:
            print("      ✓ Table structure is already correct")
    
    conn.commit()
    
    print()
    print("[3/4] Checking and updating systemsettings table...")
    
    # Проверяем таблицу systemsettings
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='systemsettings'")
    if cursor.fetchone() is None:
        cursor.execute("""
            CREATE TABLE systemsettings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO systemsettings (setting_key, setting_value) 
            VALUES ('usd_to_stars_rate', '200')
        """)
        print("      ✓ Table systemsettings created with default values")
    else:
        print("      ✓ Table systemsettings already exists")
    
    conn.commit()
    
    print()
    print("[4/4] Verifying final structure...")
    
    # Показываем финальную структуру
    cursor.execute("PRAGMA table_info(promocode)")
    columns = cursor.fetchall()
    print("      Final promocode table structure:")
    for col in columns:
        print(f"        - {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':8} default={col[4] or 'None'}")
    
    cursor.execute("SELECT COUNT(*) FROM promocode")
    count = cursor.fetchone()[0]
    print(f"\n      Total promocodes in database: {count}")
    
    print()
    print("=" * 70)
    print("                  ✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    
except Exception as e:
    print(f"\n❌ ERROR during migration: {e}")
    conn.rollback()
    print("\nPlease contact support if the problem persists.")
    sys.exit(1)
finally:
    conn.close()

input("Press Enter to close...")
