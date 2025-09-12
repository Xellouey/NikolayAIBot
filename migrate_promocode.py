#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Миграция для обновления таблицы promocode
Добавляет новые поля discount_type и discount_value
Мигрирует данные из старых полей (если они есть)
"""

import sqlite3
import os
from datetime import datetime

def migrate_promocode_table():
    """Выполняет миграцию таблицы promocode"""
    
    db_path = 'database/school.db'
    
    # Создаём резервную копию базы данных
    backup_path = f'database/school.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    if os.path.exists(db_path):
        print(f"📁 Создаём резервную копию базы данных: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✅ Резервная копия создана")
    else:
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем существование таблицы promocode
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promocode'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("📝 Таблица promocode не существует. Создаём новую таблицу...")
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
            conn.commit()
            print("✅ Таблица promocode создана")
        else:
            print("📝 Таблица promocode существует. Проверяем структуру...")
            
            # Получаем информацию о колонках
            cursor.execute("PRAGMA table_info(promocode)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"   Существующие колонки: {column_names}")
            
            # Проверяем и добавляем новые колонки
            changes_made = False
            
            if 'discount_type' not in column_names:
                print("   ➕ Добавляем колонку discount_type...")
                cursor.execute("ALTER TABLE promocode ADD COLUMN discount_type VARCHAR(20) DEFAULT 'percentage'")
                changes_made = True
            
            if 'discount_value' not in column_names:
                print("   ➕ Добавляем колонку discount_value...")
                cursor.execute("ALTER TABLE promocode ADD COLUMN discount_value DECIMAL(10,2) DEFAULT 0")
                changes_made = True
            
            # Мигрируем данные из старых полей (если они существуют)
            if 'discount_percent' in column_names or 'discount_amount_usd' in column_names:
                print("   📋 Мигрируем данные из старых полей...")
                
                # Получаем все записи
                cursor.execute("SELECT * FROM promocode")
                rows = cursor.fetchall()
                
                # Находим индексы колонок
                col_indices = {col[1]: idx for idx, col in enumerate(columns)}
                
                for row in rows:
                    row_id = row[0]  # id всегда первый
                    updates = []
                    
                    # Проверяем discount_percent
                    if 'discount_percent' in col_indices:
                        percent_value = row[col_indices['discount_percent']]
                        if percent_value is not None and percent_value > 0:
                            updates.append(f"discount_type='percentage', discount_value={percent_value}")
                    
                    # Проверяем discount_amount_usd
                    if 'discount_amount_usd' in col_indices:
                        amount_value = row[col_indices['discount_amount_usd']]
                        if amount_value is not None and amount_value > 0:
                            # Если уже есть процент, то фиксированная сумма имеет приоритет
                            updates.append(f"discount_type='fixed', discount_value={amount_value}")
                    
                    if updates:
                        update_sql = f"UPDATE promocode SET {updates[-1]} WHERE id={row_id}"
                        cursor.execute(update_sql)
                        print(f"      Обновлена запись ID={row_id}")
                
                changes_made = True
            
            # Исправляем usage_count вместо used_count (если нужно)
            if 'used_count' in column_names and 'usage_count' not in column_names:
                print("   ➕ Добавляем колонку usage_count...")
                cursor.execute("ALTER TABLE promocode ADD COLUMN usage_count INTEGER DEFAULT 0")
                cursor.execute("UPDATE promocode SET usage_count = used_count")
                print("   📋 Данные скопированы из used_count в usage_count")
                changes_made = True
            
            if changes_made:
                conn.commit()
                print("✅ Миграция выполнена успешно")
            else:
                print("ℹ️ Миграция не требуется, таблица уже имеет нужную структуру")
        
        # Проверяем таблицу systemsettings
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='systemsettings'")
        settings_exists = cursor.fetchone() is not None
        
        if not settings_exists:
            print("\n📝 Таблица systemsettings не существует. Создаём новую таблицу...")
            cursor.execute("""
                CREATE TABLE systemsettings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Добавляем начальное значение для курса валют
            cursor.execute("""
                INSERT INTO systemsettings (setting_key, setting_value) 
                VALUES ('usd_to_stars_rate', '200')
            """)
            
            conn.commit()
            print("✅ Таблица systemsettings создана")
        
        # Выводим финальную структуру
        print("\n📊 Финальная структура таблицы promocode:")
        cursor.execute("PRAGMA table_info(promocode)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} default={col[4]}")
        
        # Показываем количество записей
        cursor.execute("SELECT COUNT(*) FROM promocode")
        count = cursor.fetchone()[0]
        print(f"\n📈 Количество промокодов в базе: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Запуск миграции базы данных для таблицы promocode")
    print("=" * 60)
    
    success = migrate_promocode_table()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Миграция завершена успешно!")
        print("\n⚠️ ВАЖНО: Необходимо перезапустить бота для применения изменений!")
    else:
        print("❌ Миграция завершилась с ошибками!")
        print("Проверьте логи выше для деталей")
    print("=" * 60)
