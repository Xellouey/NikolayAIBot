#!/usr/bin/env python
"""
Скрипт для запуска тестов
"""
import sys
import pytest

def run_tests():
    """Запуск всех тестов"""
    
    # Аргументы для pytest
    args = [
        'tests/',  # Папка с тестами
        '-v',      # Подробный вывод
        '--tb=short',  # Короткий формат traceback
        '-x',      # Остановка при первой ошибке
        '--color=yes',  # Цветной вывод
    ]
    
    # Добавляем переданные аргументы
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # Запускаем pytest
    exit_code = pytest.main(args)
    
    # Выводим результат
    if exit_code == 0:
        print("\n✅ Все тесты пройдены успешно!")
    else:
        print(f"\n❌ Тесты завершились с ошибкой (код: {exit_code})")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(run_tests())
