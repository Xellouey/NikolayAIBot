"""
Интеграционные тесты для системы рассылок
Тестирует немедленную и запланированную отправку рассылок
"""
import asyncio
import logging
from datetime import datetime, timedelta
from database.mail import Mail
from database.core import con
import json
from unittest.mock import patch, AsyncMock
from database import sql

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class TestMailSystem:
    """Тесты системы рассылок"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        from database import sql
        sql.configure_database()
        self.mail_model = Mail()
        
    async def test_immediate_mail_creation(self):
        """Тест создания рассылки для немедленной отправки"""
        print("\nТест: Создание немедленной рассылки")
        
        # Создаем рассылку с временем в прошлом (как при пропуске времени)
        date_mail = datetime.now() - timedelta(seconds=10)
        test_message_id = 12345
        test_from_id = 67890
        test_keyboard = None
        
        # Создаем рассылку
        mail_id = await self.mail_model.create_mail(
            date_mail=date_mail,
            message_id=test_message_id,
            from_id=test_from_id,
            keyboard=test_keyboard
        )
        
        print(f"Рассылка создана с ID: {mail_id}")
        print(f"Время отправки: {date_mail.strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Проверяем, что рассылка найдена планировщиком
        wait_mails = await self.mail_model.get_wait_mails()
        
        assert len(wait_mails) > 0, "Должна быть найдена минимум одна рассылка"
        assert any(mail['id'] == mail_id for mail in wait_mails), f"Рассылка {mail_id} должна быть в списке ожидающих"
        
        print(f"Рассылка {mail_id} найдена планировщиком")
        
        # Очистка
        await self.cleanup_test_mail(mail_id)
        return True
    
    async def test_scheduled_mail_creation(self):
        """Тест создания запланированной рассылки"""
        print("\nТест: Создание запланированной рассылки")
        
        # Создаем рассылку на будущее время
        date_mail = datetime.now() + timedelta(minutes=5)
        test_message_id = 54321
        test_from_id = 98765
        test_keyboard = {"inline_keyboard": [[]]}
        
        # Создаем рассылку
        mail_id = await self.mail_model.create_mail(
            date_mail=date_mail,
            message_id=test_message_id,
            from_id=test_from_id,
            keyboard=test_keyboard
        )
        
        print(f"Запланированная рассылка создана с ID: {mail_id}")
        print(f"Время отправки: {date_mail.strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Проверяем, что рассылка НЕ найдена планировщиком (еще рано)
        wait_mails = await self.mail_model.get_wait_mails()
        
        assert not any(mail['id'] == mail_id for mail in wait_mails), f"Рассылка {mail_id} НЕ должна быть в списке ожидающих"
        
        print(f"Запланированная рассылка {mail_id} корректно не найдена планировщиком")
        
        # Очистка
        await self.cleanup_test_mail(mail_id)
        return True
    
    async def test_timing_precision(self):
        """Тест точности времени для немедленной отправки"""
        print("\nТест: Точность времени немедленной отправки")
        
        # Тест различных временных интервалов
        test_cases = [
            -15,  # 15 секунд назад
            -10,  # 10 секунд назад (как в коде)
            -5,   # 5 секунд назад
            -1,   # 1 секунда назад
        ]
        
        created_mails = []
        
        for seconds_offset in test_cases:
            date_mail = datetime.now() + timedelta(seconds=seconds_offset)
            
            mail_id = await self.mail_model.create_mail(
                date_mail=date_mail,
                message_id=11111,
                from_id=22222,
                keyboard=None
            )
            
            created_mails.append(mail_id)
            print(f"Создана рассылка {mail_id} с отступом {seconds_offset}с")
        
        # Проверяем, какие рассылки найдены планировщиком
        wait_mails = await self.mail_model.get_wait_mails()
        found_mail_ids = [mail['id'] for mail in wait_mails]
        
        for mail_id in created_mails:
            if mail_id in found_mail_ids:
                print(f"Рассылка {mail_id} найдена планировщиком")
            else:
                print(f"Рассылка {mail_id} НЕ найдена планировщиком")
        
        # Все рассылки с отрицательным временем должны быть найдены
        assert len([mail_id for mail_id in created_mails if mail_id in found_mail_ids]) == len(created_mails), \
            "Все рассылки с временем в прошлом должны быть найдены"
        
        # Очистка
        for mail_id in created_mails:
            await self.cleanup_test_mail(mail_id)
        
        return True
    
    async def test_mail_retrieval_and_data_integrity(self):
        """Тест получения данных рассылки и целостности данных"""
        print("\nТест: Получение данных рассылки")
        
        test_keyboard = {
            "inline_keyboard": [
                [{"text": "Кнопка 1", "callback_data": "btn1"}],
                [{"text": "Кнопка 2", "url": "https://example.com"}]
            ]
        }
        
        date_mail = datetime.now() - timedelta(seconds=5)
        test_message_id = 99999
        test_from_id = 11111
        
        # Создаем рассылку с клавиатурой
        mail_id = await self.mail_model.create_mail(
            date_mail=date_mail,
            message_id=test_message_id,
            from_id=test_from_id,
            keyboard=test_keyboard
        )
        
        # Получаем данные рассылки
        mail_data = await self.mail_model.get_mail(mail_id)
        
        assert mail_data is not None, "Данные рассылки должны быть получены"
        assert mail_data['message_id'] == test_message_id, "ID сообщения должен совпадать"
        assert mail_data['from_id'] == test_from_id, "ID отправителя должен совпадать"
        assert mail_data['keyboard'] == test_keyboard, "Клавиатура должна совпадать"
        
        print(f"Данные рассылки {mail_id} получены корректно")
        print(f"Клавиатура: {mail_data['keyboard']}")
        
        # Очистка
        await self.cleanup_test_mail(mail_id)
        return True
    
    async def test_scheduler_immediate_send(self):
        """Тест scheduler'а для мгновенной отправки"""
        print("\nТест: Scheduler для немедленной отправки")
        
        # Создаём мгновенную рассылку
        date_mail = datetime.now() - timedelta(seconds=10)
        test_message_id = 88888
        test_from_id = 99999
        test_keyboard = {"inline_keyboard": [[{"text": "Test Button", "callback_data": "test"}]]}
        
        mail_id = await self.mail_model.create_mail(
            date_mail=date_mail,
            message_id=test_message_id,
            from_id=test_from_id,
            keyboard=test_keyboard
        )
        
        print(f"Мгновенная рассылка создана с ID: {mail_id}")
        
        m = self.mail_model
        # Патчим mailing
        with patch('mail.mailing', new_callable=AsyncMock) as mock_mailing:
            
            # Вызываем логику scheduler'а напрямую для одного цикла
            wait_mails = await m.get_wait_mails()
            for mail_data in wait_mails:
                mail_id_loop = mail_data['id']
                message_id_loop = mail_data['message_id']
                from_id_loop = mail_data['from_id']
                keyboard_str = mail_data.get('keyboard')
                keyboard = json.loads(keyboard_str) if keyboard_str else None
                
                logging.info(f"Запуск рассылки ID {mail_id_loop}")
                await mock_mailing(message_id_loop, from_id_loop, keyboard)
                
                # Обновляем статус на 'sent'
                await m.update_mail(mail_id_loop, 'status', 'sent')
                logging.info(f"Рассылка ID {mail_id_loop} завершена")
        
        # Проверяем, что mailing был вызван
        mock_mailing.assert_called_once_with(test_message_id, test_from_id, test_keyboard)
        print("mailing вызван для мгновенной рассылки")
        
        # Проверяем обновление status
        mail_data = await self.mail_model.get_mail(mail_id)
        if mail_data is None:
            print("mail_data is None")
            assert False, "mail_data не должен быть None"
        assert mail_data['status'] == 'sent', "Status должен быть 'sent' после отправки"
        print("Status обновлён на 'sent'")
        
        # Очистка
        await self.cleanup_test_mail(mail_id)
        return True
    
    async def cleanup_test_mail(self, mail_id):
        """Очистка тестовой рассылки"""
        try:
            # Удаляем рассылку из базы данных
            await self.mail_model.update_mail(mail_id, 'status', 'deleted')
            print(f"Тестовая рассылка {mail_id} помечена как удаленная")
        except Exception as e:
            print(f"Ошибка при очистке рассылки {mail_id}: {e}")

async def run_all_tests():
    """Запуск всех тестов"""
    print("Запуск интеграционных тестов системы рассылок")
    print("=" * 60)
    
    test_suite = TestMailSystem()
    tests = [
        ("Немедленная отправка", test_suite.test_immediate_mail_creation),
        ("Запланированная отправка", test_suite.test_scheduled_mail_creation),
        ("Точность времени", test_suite.test_timing_precision),
        ("Целостность данных", test_suite.test_mail_retrieval_and_data_integrity),
        ("Scheduler мгновенная отправка", test_suite.test_scheduler_immediate_send),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nЗапуск теста: {test_name}")
            setup_method = getattr(test_suite, 'setup_method', None)
            if setup_method:
                setup_method()
                
            result = await test_func()
            if result:
                print(f"ПРОЙДЕН: {test_name}")
                passed += 1
            else:
                print(f"ПРОВАЛЕН: {test_name}")
                failed += 1
        except Exception as e:
            print(f"ОШИБКА в тесте {test_name}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Результаты тестирования:")
    print(f"Пройдено: {passed}")
    print(f"Провалено: {failed}")
    print(f"Общий результат: {passed}/{passed + failed}")
    
    if failed == 0:
        print("Все тесты пройдены успешно!")
        return True
    else:
        print("Некоторые тесты провалены. Требуется дополнительная отладка.")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())
