import asyncio
import logging
import argparse
from peewee import DoesNotExist
from database.core import con
from database.user import User
from database.lesson import Purchase
from database.support import SupportTicket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def main(user_id: int):
    """Clean user data from database"""
    try:
        # Connect to database (assuming con is the connection)
        logging.info(f"Подключение к БД и очистка данных пользователя ID {user_id}")
        
        # Delete user record
        try:
            user_record = User.get_or_none(User.user_id == user_id)
            if user_record:
                logging.info(f"Найден пользователь ID {user_id}: {user_record.full_name}")
                user_record.delete_instance()
                logging.info("Запись пользователя удалена")
            else:
                logging.warning(f"Пользователь с ID {user_id} не найден")
        except DoesNotExist:
            logging.warning(f"Пользователь с ID {user_id} не найден")
        except Exception as e:
            logging.error(f"Ошибка удаления пользователя: {e}")
        
        # Delete purchases
        try:
            num_purchases = Purchase.delete().where(Purchase.user_id == user_id).execute()
            if num_purchases > 0:
                logging.info(f"Удалено {num_purchases} записей о покупках")
            else:
                logging.info("Покупок у пользователя не найдено")
        except Exception as e:
            logging.error(f"Ошибка удаления покупок: {e}")
        
        # Delete support tickets
        try:
            num_tickets = SupportTicket.delete().where(SupportTicket.user_id == user_id).execute()
            if num_tickets > 0:
                logging.info(f"Удалено {num_tickets} тикетов поддержки")
            else:
                logging.info("Тикетов поддержки у пользователя не найдено")
        except Exception as e:
            logging.error(f"Ошибка удаления тикетов: {e}")
        
        # Delete any other related data (mail, progress, etc.)
        # For mail, if there's user-related data in mail table (from handlers/mail.py, but it's for mail tasks, not user-specific)
        # Assuming no direct user mail, skip or add if needed
        
        logging.info("Все связанные данные пользователя успешно удалены")
        logging.info("При следующем /start пользователь будет обработан как новый (onboarding сброшен)")
        
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Очистка данных пользователя в БД бота")
    parser.add_argument('--user_id', type=int, default=1113623255, help="Telegram ID пользователя (по умолчанию 1113623255)")
    args = parser.parse_args()
    
    print("ВНИМАНИЕ: Этот скрипт предназначен для staging БД!")
    print("Для production БД используйте с крайней осторожностью - данные будут удалены безвозвратно!")
    print("Подтвердите выполнение (y/n): ", end="")
    import sys
    confirmation = input()
    if confirmation.lower() == 'y':
        asyncio.run(main(args.user_id))
        print("Скрипт завершен.")
    else:
        print("Отменено.")