#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Отладка проблемы с кнопкой отмены
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_cancel_button():
    """Отладка кнопки отмены"""
    print("=" * 60)
    print("ОТЛАДКА КНОПКИ ОТМЕНЫ")
    print("=" * 60)
    
    # Проверяем импорты
    try:
        from handlers import mail
        print("✅ Модуль mail импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта mail: {e}")
        return False
    
    # Проверяем регистрацию обработчиков
    print("\n📝 Зарегистрированные обработчики в mail.router:")
    
    handlers = []
    for key in dir(mail.router):
        if key.startswith('_'):
            continue
        attr = getattr(mail.router, key)
        if callable(attr):
            handlers.append(key)
    
    for h in sorted(handlers):
        print(f"  • {h}")
    
    # Проверяем FSM состояния
    from states import FSMMail
    print("\n📋 FSM состояния для рассылки:")
    states = []
    for attr_name in dir(FSMMail):
        if not attr_name.startswith('_'):
            attr = getattr(FSMMail, attr_name)
            if hasattr(attr, '_state'):
                states.append((attr_name, attr._state))
    
    for name, state in states:
        print(f"  • {name}: {state}")
    
    # Проверка текстов кнопок
    print("\n🔍 Проверка сравнения текстов:")
    test_text = "❌ Отмена"
    
    # Различные варианты текста
    variants = [
        "❌ Отмена",
        "❌ отмена",
        "❌  Отмена",  # с двумя пробелами
        " ❌ Отмена",  # с пробелом в начале
        "❌ Отмена ",  # с пробелом в конце
    ]
    
    for var in variants:
        result = var == test_text
        print(f"  '{var}' == '{test_text}': {result}")
        if not result:
            print(f"     Bytes сравнение: {var.encode('utf-8')} vs {test_text.encode('utf-8')}")
    
    # Инструкции для отладки
    print("\n" + "=" * 60)
    print("ИНСТРУКЦИИ ДЛЯ ОТЛАДКИ")
    print("=" * 60)
    print("\n1. Перезапустите бота")
    print("2. Начните создание рассылки")
    print("3. Нажмите кнопку '❌ Отмена'")
    print("4. Проверьте логи на наличие сообщений:")
    print("   - '📨 FSMMail.date_mail: получено сообщение: ...'")
    print("   - '✅ Кнопка отмены нажата в ...'")
    print("\nЕсли логи не появляются, проблема в том, что:")
    print("  • Обработчик не вызывается вообще")
    print("  • Состояние FSM не соответствует ожидаемому")
    print("  • Другой обработчик перехватывает сообщение")
    
    return True


if __name__ == "__main__":
    success = debug_cancel_button()
    sys.exit(0 if success else 1)
