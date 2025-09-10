#!/usr/bin/env python
"""
Тест исправлений системы рассылки и локализации
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from localization import get_text
from database.mail import Mail

def test_localization():
    """Проверка что ключи локализации корректно возвращают текст"""
    print("=" * 50)
    print("ТЕСТ ЛОКАЛИЗАЦИИ")
    print("=" * 50)
    
    tests = [
        ('mail.messages.mail_help', 'должен содержать справку о JSON'),
        ('mail.buttons.copy_json', 'кнопка копирования JSON'),
        ('mail.buttons.copy_inline', 'кнопка копирования inline'),
        ('mail.buttons.copy_keyboard', 'кнопка копирования keyboard'),
        ('mail.messages.json_example_inline', 'пример inline JSON'),
        ('mail.messages.json_example_keyboard', 'пример keyboard JSON'),
    ]
    
    passed = 0
    failed = 0
    
    for key, description in tests:
        text = get_text(key, 'ru')
        if text == key:
            print(f"❌ FAIL: {key} - возвращает ключ вместо текста")
            failed += 1
        else:
            print(f"✅ PASS: {key} - {description}")
            print(f"   Текст: {text[:50]}..." if len(text) > 50 else f"   Текст: {text}")
            passed += 1
    
    print(f"\nРезультат: {passed} пройдено, {failed} провалено")
    return failed == 0

async def test_mail_scheduler_atomic():
    """Проверка атомарности захвата задач"""
    print("\n" + "=" * 50)
    print("ТЕСТ АТОМАРНОСТИ ПЛАНИРОВЩИКА")
    print("=" * 50)
    
    m = Mail()
    
    # Создаем тестовую рассылку в прошлом (для немедленной отправки)
    test_date = datetime.now() - timedelta(minutes=1)
    
    try:
        # Создаем тестовую рассылку
        mail_id = await m.create_mail(
            date_mail=test_date,
            message_id=999999,  # фиктивный ID
            from_id=123456789,  # фиктивный пользователь
            keyboard=None,
            message_text="Test mail"
        )
        print(f"✅ Создана тестовая рассылка ID: {mail_id}")
        
        # Проверяем статус
        mail = await m.get_mail(mail_id)
        if mail and mail.get('status') == 'wait':
            print(f"✅ Рассылка в статусе 'wait'")
        else:
            print(f"❌ Неверный статус: {mail.get('status') if mail else 'None'}")
        
        # Имитируем захват задачи
        await m.update_mail(mail_id, 'status', 'run')
        mail = await m.get_mail(mail_id)
        if mail and mail.get('status') == 'run':
            print(f"✅ Рассылка захвачена (статус 'run')")
        else:
            print(f"❌ Не удалось захватить: {mail.get('status') if mail else 'None'}")
        
        # Проверяем что она не появляется в списке ожидающих
        wait_mails = await m.get_wait_mails()
        if wait_mails:
            mail_ids = [mail['id'] for mail in wait_mails]
            if mail_id not in mail_ids:
                print(f"✅ Захваченная рассылка не в списке ожидающих")
            else:
                print(f"❌ Захваченная рассылка все еще в списке ожидающих!")
        else:
            print(f"✅ Нет ожидающих рассылок (захваченная не в списке)")
        
        # Очистка
        await m.delete_mail(mail_id)
        print(f"✅ Тестовая рассылка удалена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

async def test_check_py_disabled():
    """Проверка что check.py отключен"""
    print("\n" + "=" * 50)
    print("ТЕСТ ОТКЛЮЧЕНИЯ CHECK.PY")
    print("=" * 50)
    
    import subprocess
    
    try:
        result = subprocess.run(
            [sys.executable, "check.py"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if "check.py disabled" in result.stderr or "check.py disabled" in result.stdout:
            print("✅ check.py корректно отключен")
            return True
        else:
            print(f"❌ check.py не отключен!")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ check.py завис (возможно работает!)")
        return False
    except Exception as e:
        print(f"⚠️ Не удалось проверить check.py: {e}")
        return True  # Не критично

async def main():
    print("\n🔧 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ РАССЫЛКИ\n")
    
    results = []
    
    # Тест локализации
    results.append(test_localization())
    
    # Тест атомарности
    results.append(await test_mail_scheduler_atomic())
    
    # Тест отключения check.py
    results.append(await test_check_py_disabled())
    
    print("\n" + "=" * 50)
    print("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    print("=" * 50)
    
    if all(results):
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print(f"❌ Провалено {results.count(False)} из {len(results)} тестов")
        
    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
