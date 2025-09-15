import config
import peewee
from peewee import *
from .core import con
from .user import User
from .lesson import Lesson, Promocode, SystemSettings
from .onboarding import OnboardingStep, OnboardingOption, OnboardingEvent, ensure_default_flow
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
    """Настройка базы данных и безопасные миграции"""
    # Создание основных таблиц, если их нет
    con.create_tables([User, Lesson, Support, Mail, Promocode, SystemSettings, OnboardingStep, OnboardingOption, OnboardingEvent], safe=True)

    # Безопасные ALTER для расширенных полей пользователя
    try:
        con.execute_sql("ALTER TABLE user ADD COLUMN onboarding_goal TEXT")
    except Exception:
        pass
    try:
        con.execute_sql("ALTER TABLE user ADD COLUMN onboarding_level TEXT")
    except Exception:
        pass
    try:
        con.execute_sql("ALTER TABLE user ADD COLUMN consent_newsletter BOOLEAN DEFAULT 0")
    except Exception:
        pass

    # Миграция для добавления message_text в Mail (идемпотентно)
    try:
        con.execute_sql('ALTER TABLE mail ADD COLUMN message_text TEXT')
        print("Колонка message_text добавлена в таблицу Mail")
    except Exception:
        pass  # Колонка уже существует или другая безопасная ошибка

    # Безопасные миграции для таблицы promocode
    # Добавляем недостающие колонки, если их нет
    try:
        con.execute_sql("ALTER TABLE promocode ADD COLUMN discount_type VARCHAR(20) DEFAULT 'percentage'")
        print("Колонка discount_type добавлена в таблицу promocode")
    except Exception:
        pass

    try:
        con.execute_sql("ALTER TABLE promocode ADD COLUMN discount_value DECIMAL(10,2) DEFAULT 0")
        print("Колонка discount_value добавлена в таблицу promocode")
    except Exception:
        pass

    # Переезд used_count -> usage_count (если требуется)
    try:
        con.execute_sql("ALTER TABLE promocode ADD COLUMN usage_count INTEGER DEFAULT 0")
        print("Колонка usage_count добавлена в таблицу promocode")
    except Exception:
        pass

    try:
        # Скопируем данные, если старое поле существовало
        con.execute_sql("UPDATE promocode SET usage_count = used_count WHERE usage_count = 0")
        print("Данные usage_count скопированы из used_count")
    except Exception:
        pass

    # Ensure default onboarding flow exists
    try:
        ensure_default_flow()
    except Exception:
        pass

    print("База данных настроена и миграции применены (если требовалось)")
