import config
import peewee
from peewee import *
from .core import con
from .user import User
from .lesson import Lesson
from datetime import datetime

class Support(peewee.Model):
    id = peewee.AutoField()
    user_id = peewee.BigIntegerField()
    subject = peewee.CharField()
    description = peewee.TextField()
    status = peewee.CharField(default='new')
    admin_response = peewee.TextField(null=True)
    created_at = peewee.DateTimeField(default=datetime.now)
    
    class Meta:
        database = con

class Mail(peewee.Model):
    id = peewee.AutoField()
    date_mail = peewee.DateTimeField()
    message_id = peewee.IntegerField()
    from_id = peewee.BigIntegerField()
    message_text = peewee.TextField(null=True)
    keyboard = peewee.TextField(null=True)
    status = peewee.CharField(default='wait')
    
    class Meta:
        database = con

def configure_database():
    """Настройка базы данных"""
    con.create_tables([User, Lesson, Support, Mail], safe=True)
    
    # Миграция для добавления message_text в Mail
    try:
        con.execute_sql('ALTER TABLE mail ADD COLUMN message_text TEXT')
        print("Колонка message_text добавлена в таблицу Mail")
    except:
        pass  # Колонка уже существует или ошибка - безопасно
        
    print("База данных настроена")