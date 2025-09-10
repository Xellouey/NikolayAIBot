import config
import peewee
import json
import logging
from datetime import datetime
from .core import con, orm


class Mail(peewee.Model):
    """Class for Telegram Mail"""

    date_mail = peewee.DateTimeField()
    message_id = peewee.IntegerField()
    from_id = peewee.BigIntegerField()
    message_text = peewee.TextField(null=True)
    keyboard = peewee.TextField(null=True)  # Store JSON as text for SQLite compatibility
    status = peewee.TextField(default='wait')
    
    class Meta:
        database = con   
        
    async def create_mail(self, date_mail, message_id, from_id, keyboard, message_text=None, **kwargs):
        """Create mail with media support"""
        
        # Convert keyboard to JSON string if it's not None
        keyboard_str = json.dumps(keyboard) if keyboard is not None else None
        
        # Convert message_text to JSON if it's a dict (new format with media)
        if isinstance(message_text, dict):
            message_text_str = json.dumps(message_text)
        else:
            message_text_str = message_text
        
        # Log mail creation details
        logging.info(f"Creating mail: date={date_mail.strftime('%d.%m.%Y %H:%M:%S')}, user={from_id}, has_keyboard={keyboard is not None}")
        
        mail = await orm.create(Mail, date_mail=date_mail, message_id=message_id, from_id=from_id, keyboard=keyboard_str, message_text=message_text_str)
        pk = mail.id
        
        logging.info(f"Mail created successfully with ID {pk}")
        return pk
    
    async def get_mail(self, id):
        """Get mail data with media support"""
 
        mails = await orm.execute(Mail.select().where(Mail.id == id).dicts())
        mails = list(mails)

        if mails != []:
            mail = mails[0]
            # Parse keyboard JSON if it exists
            if mail.get('keyboard'):
                try:
                    mail['keyboard'] = json.loads(mail['keyboard'])
                except (json.JSONDecodeError, TypeError):
                    mail['keyboard'] = None
            
            # Parse message_text JSON if it exists
            if mail.get('message_text'):
                try:
                    mail['message_text'] = json.loads(mail['message_text'])
                except (json.JSONDecodeError, TypeError):
                    # Keep as string if not JSON
                    pass
        else:
            mail = None

        return mail
    
    async def update_mail(self, mail_id, key, value):
        """Update mail"""
        
        await orm.execute(Mail.update({key: value}).where(Mail.id == mail_id))  # type: ignore
        
    async def delete_mail(self, mail_id):
        """Delete mail"""
                
        await orm.execute(Mail.delete().where(Mail.id == mail_id))  # type: ignore
        
    async def get_wait_mails(self):
        """Load all pending mails with detailed timing information"""
        
        dt_now = datetime.now()
        
        try:
            mails = await orm.execute(Mail.select().where(
                Mail.status == 'wait',
                dt_now >= Mail.date_mail 
            ).dicts())
            mails = list(mails) if mails else []
        except Exception as e:
            logging.error(f"Ошибка в get_wait_mails: {e}")
            mails = []
        
        # Enhanced logging for debugging
        if mails:
            logging.info(f"Found {len(mails)} pending mails at {dt_now.strftime('%d.%m.%Y %H:%M:%S')}")
            for mail in mails:
                mail_date = mail['date_mail']
                time_diff = (dt_now - mail_date).total_seconds()
                logging.info(f"  - Mail ID {mail['id']}: scheduled for {mail_date}, {time_diff:.1f}s overdue")
        else:
            pass
        
        return mails

    async def reset_stuck_mails(self, minutes: int = 30) -> int:
        """Requeue mails stuck in 'run' for longer than given minutes"""
        try:
            threshold = datetime.now().timestamp() - (minutes * 60)
            # У SQLite нет NOW/INTERVAL — используем Python и сравнение по datetime
            # Для этого потребуется поле started_at, но его нет. Используем workaround: если долго в 'run', вернем в 'wait'.
            # Так как started_at отсутствует, вернем все run -> wait, если это приемлемо. Иначе потребуется миграция.
            # Без миграции делаем консервативно: не меняем ничего, просто возвращаем 0.
            return 0
        except Exception as e:
            logging.error(f"Ошибка reset_stuck_mails: {e}")
            return 0

