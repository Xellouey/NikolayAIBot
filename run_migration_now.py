#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Выполнение миграции базы данных
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем и запускаем миграцию
from migrate_promocode import migrate_promocode_table

if __name__ == "__main__":
    print("Запуск миграции базы данных...")
    success = migrate_promocode_table()
    
    if success:
        print("\n✅ Миграция выполнена успешно!")
        print("⚠️ Не забудьте перезапустить бота для применения изменений!")
    else:
        print("\n❌ Миграция завершилась с ошибками!")
        sys.exit(1)
