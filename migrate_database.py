"""
🔄 Скрипт миграции базы данных
Добавляет недостающие колонки в таблицу пользователей
"""

import sys
import os
import sqlite3
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """Миграция базы данных"""
    print("🔄 Запуск миграции базы данных...")
    
    try:
        # Подключаемся к базе данных
        db_path = 'shop_bot.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🗄️ Подключение к базе данных: {db_path}")
        
        # Проверяем существующие колонки в таблице user
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"📋 Существующие колонки: {existing_columns}")
        
        # Список новых колонок для добавления
        new_columns = [
            ('onboarding_completed', 'BOOLEAN DEFAULT 0'),
            ('last_onboarding_step', 'TEXT'),
            ('onboarding_completed_at', 'DATETIME')
        ]
        
        # Добавляем отсутствующие колонки
        added_count = 0
        for column_name, column_definition in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_definition}"
                    cursor.execute(sql)
                    print(f"✅ Добавлена колонка: {column_name}")
                    added_count += 1
                except sqlite3.Error as e:
                    print(f"❌ Ошибка добавления колонки {column_name}: {e}")
            else:
                print(f"ℹ️ Колонка {column_name} уже существует")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print(f"🎯 Миграция завершена! Добавлено колонок: {added_count}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

def verify_migration():
    """Проверка успешности миграции"""
    print("\n🔍 Проверка структуры таблицы после миграции...")
    
    try:
        conn = sqlite3.connect('shop_bot.db')
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы user
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("📊 Текущая структура таблицы user:")
        for col in columns:
            col_id, name, data_type, not_null, default_value, pk = col
            default_str = f" DEFAULT {default_value}" if default_value else ""
            null_str = " NOT NULL" if not_null else ""
            pk_str = " PRIMARY KEY" if pk else ""
            print(f"  • {name}: {data_type}{default_str}{null_str}{pk_str}")
        
        # Проверяем количество пользователей
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"👥 Количество пользователей: {user_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Миграция базы данных NikolayAI Bot")
    print("=" * 50)
    
    # Выполняем миграцию
    if migrate_database():
        # Проверяем результат
        verify_migration()
        print("\n🎉 Миграция успешно завершена!")
        print("💡 Теперь можно перезапустить бота")
    else:
        print("\n💥 Миграция завершилась с ошибками")
        sys.exit(1)