import asyncio
import config
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import client, admin, mail, shop, payment, support
from database import sql
from database.mail import Mail
from mail import mailing

# Импортируем новые системы обработки ошибок
from errors import global_error_handler, ErrorContext, ErrorType, ErrorSeverity
from message_manager import global_message_manager
from state_manager import safe_state_manager
from database_resilience import init_resilient_db_manager, resilient_db_manager
from database.core import con

import utils

bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode='html'))

global_message_manager.set_bot(bot)


# Глобальный обработчик ошибок aiogram
async def global_exception_handler(event):
    """Обработчик необработанных исключений для aiogram 3"""
    try:
        # Извлекаем данные из ErrorEvent
        update = event.update
        exception = event.exception
        
        # Извлекаем контекст из update
        context = ErrorContext()
        
        if hasattr(update, 'message') and update.message:
            context.user_id = update.message.from_user.id if update.message.from_user else None
            context.chat_id = update.message.chat.id
            context.message_id = update.message.message_id
        elif hasattr(update, 'callback_query') and update.callback_query:
            context.user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
            context.callback_data = update.callback_query.data
            if update.callback_query.message:
                context.chat_id = update.callback_query.message.chat.id
                context.message_id = update.callback_query.message.message_id
        
        context.handler = "global_exception_handler"
        context.additional_data = {
            "update_type": type(update).__name__,
            "exception_type": type(exception).__name__
        }
        
        # Логируем ошибку
        error_type, severity = global_error_handler.classify_error(exception)
        global_error_handler.logger.log_error(exception, context, error_type, severity)
        
        print(f"🔥 Необработанное исключение в {context.handler}: {exception}")
        
        # Пытаемся отправить пользователю сообщение об ошибке
        if context.user_id:
            try:
                await global_message_manager.send_message_safe(
                    chat_id=context.user_id,
                    text="❌ Произошла неожиданная ошибка. Попробуйте позже или обратитесь в поддержку."
                )
            except Exception as send_error:
                print(f"❌ Не удалось отправить сообщение об ошибке: {send_error}")
        
        return True  # Продолжаем обработку update'ов
        
    except Exception as handler_error:
        print(f"🔥 Критическая ошибка в глобальном обработчике: {handler_error}")
        logging.critical(f"Критическая ошибка: {handler_error}")
        return True


async def mail_scheduler():
    """Периодическая проверка и отправка рассылок с атомарным захватом"""
    m = Mail()
    check_counter = 0  # Счетчик для периодической проверки застрявших задач
    
    while True:
        try:
            # Каждые 30 итераций (примерно каждые 5 минут) проверяем застрявшие задачи
            check_counter += 1
            if check_counter >= 30:
                check_counter = 0
                # Восстанавливаем застрявшие задачи (в статусе 'run' более 30 минут)
                stuck_count = await m.reset_stuck_mails(minutes=30)
                if stuck_count > 0:
                    logging.warning(f"🔄 Восстановлено {stuck_count} застрявших рассылок")
            
            # Сначала получаем список ожидающих рассылок
            wait_mails = await m.get_wait_mails()
            
            for mail_data in wait_mails:
                if not isinstance(mail_data, dict):
                    logging.warning(f"Skipping non-dict mail_data: {type(mail_data)}")
                    continue
                
                mail_id = mail_data['id']
                
                # ВАЖНО: Атомарно захватываем задачу, изменяя статус на 'run'
                # Это предотвращает повторную обработку другим планировщиком
                await m.update_mail(mail_id, 'status', 'run')
                logging.info(f"🔒 Захвачена рассылка ID {mail_id}")
                
                try:
                    message_id = mail_data['message_id']
                    from_id = mail_data['from_id']
                    keyboard_str = mail_data.get('keyboard')
                    keyboard = json.loads(keyboard_str) if keyboard_str else None
                    
                    logging.info(f"🚀 Запуск рассылки ID {mail_id}")
                    await mailing(message_id, from_id, keyboard)
                    
                    # Обновляем статус на 'sent' только если mailing успешен
                    await m.update_mail(mail_id, 'status', 'sent')
                    logging.info(f"✅ Рассылка ID {mail_id} завершена")
                    
                except Exception as mail_error:
                    logging.error(f"Ошибка обработки рассылки ID {mail_id}: {mail_error}")
                    # При ошибке обновляем статус на 'error'
                    try:
                        await m.update_mail(mail_id, 'status', 'error')
                    except Exception as update_error:
                        logging.error(f"Не удалось обновить статус ошибки для ID {mail_id}: {update_error}")
                        
        except Exception as e:
            logging.error(f"Ошибка в scheduler рассылок: {e}")
        
        await asyncio.sleep(10)  # Проверка каждые 10 секунд


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        encoding='utf-8'
    )
    
    print("Настройка базы данных...")
    print("Запуск бота NikolayAI...")
    print(f"Токен бота настроен: {config.TOKEN[:10]}...")
    print(f"ID чата: {config.CHAT_ID}")
    print(f"Администраторов настроено: {len(set(config.ADMINS + utils.get_admins()))}")
    print("Инициализация системы обработки ошибок...")
    print("Резилиентный менеджер БД инициализирован")
    print("Системы обработки ошибок инициализированы")
    print("Глобальный обработчик ошибок зарегистрирован")
    print("Загрузка обработчиков...")
    print("Все обработчики загружены успешно")
    print("Удаление webhook и запуск polling...")
    print("Бот запущен и ожидает обновления!")
    print("Отправьте сообщение боту для проверки")
    print("Нажмите Ctrl+C для остановки бота")
    print("-" * 50)
    
    try:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Регистрируем глобальный обработчик ошибок
        dp.errors.register(global_exception_handler)
        print("✅ Глобальный обработчик ошибок зарегистрирован")
        
        dp.chat_join_request.filter(F.chat.id == config.CHAT_ID) # Принимаем заявки определённого канала
        
        print("📦 Загрузка обработчиков...")
        # Подключаем роутеры в порядке приоритета
        dp.include_router(payment.payment_router)  # Обработчики платежей первыми
        dp.include_router(support.router)          # Обработчики поддержки
        dp.include_router(client.router)           # ✅ Обработчики клиента ПЕРВЫМИ - онбординг /start
        dp.include_router(admin.router)            # Обработчики админа
        dp.include_router(mail.router)             # Обработчики рассылки
        dp.include_router(shop.shop_router)        # ✅ Обработчики магазина ПОСЛЕДНИМИ - только callback'и
        print("✅ Все обработчики загружены успешно")
        
        # Запуск scheduler рассылок
        scheduler_task = asyncio.create_task(mail_scheduler())
        
        print("🔄 Удаление webhook и запуск polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("🚀 Бот запущен и ожидает обновления!")
        print("📱 Отправьте сообщение боту для проверки")
        print("🛑 Нажмите Ctrl+C для остановки бота")
        print("-" * 50)
        
        await dp.start_polling(bot)
        
        # Ожидание завершения задачи при остановке
        await scheduler_task
        
    except Exception as e:
        print(f"❌ ОШИБКА: Не удалось запустить бота: {e}")
        logging.error(f"Ошибка запуска бота: {e}")
        raise


if __name__ == '__main__':
    print("Настройка базы данных...")
    try:
        sql.configure_database()
        print("База данных настроена успешно")
    except Exception as e:
        print(f"ОШИБКА: Настройка базы данных не удалась: {e}")
        logging.error(f"Ошибка настройки базы данных: {e}")
        exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем (Ctrl+C)")
        print("До свидания!")
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        logging.error(f"Критическая ошибка: {e}")
        exit(1)
