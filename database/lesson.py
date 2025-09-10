import config
import peewee
from datetime import datetime
from peewee import DoesNotExist
from .core import con, orm


class Lesson(peewee.Model):
    """Model for lesson with text grammar"""

    id = peewee.PrimaryKeyField()
    title = peewee.TextField()
    description = peewee.TextField()
    preview_text = peewee.TextField(null=True)  # Текст для превью/подробнее
    price_usd = peewee.DecimalField(max_digits=10, decimal_places=2)  # Цена в долларах
    content_type = peewee.CharField(max_length=20, default='video')  # video, text, document
    video_file_id = peewee.TextField(null=True)  # File ID основного видео
    preview_video_file_id = peewee.TextField(null=True)  # File ID превью видео (трейлер)
    text_content = peewee.TextField(null=True)  # Текстовое содержимое урока
    document_file_id = peewee.TextField(null=True)  # File ID документа (если есть)
    is_active = peewee.BooleanField(default=True)
    is_free = peewee.BooleanField(default=False)  # Бесплатный урок (лид-магнит)
    category = peewee.TextField(null=True)  # Категория урока
    views_count = peewee.IntegerField(default=0)  # Количество просмотров
    purchases_count = peewee.IntegerField(default=0)  # Количество покупок
    created_at = peewee.DateTimeField(default=datetime.now)
    updated_at = peewee.DateTimeField(default=datetime.now())

    class Meta:
        database = con

    async def get_all_lessons(self, active_only=True) :
        """Get all lessons"""
        try:
            query = Lesson.select()
            if active_only:
                query = query.where(Lesson.is_active == True)

            lessons = list(query.dicts())
            return lessons
        except Exception as e:
            print(f"❌ Ошибка получения списка уроков: {e}")
            return []


    async def get_lesson(self, lesson_id) :
        """Get lesson by ID"""
        try:
            # Синхронный запрос в async обертке
            lesson = Lesson.get(Lesson.id == lesson_id)


            return lesson
        except DoesNotExist:
            return None
        except Exception as e:
            print(f"❌ Ошибка получения урока {lesson_id}: {e}")
            return None


class Purchase(peewee.Model):
    """Model for lesson purchases"""

    user_id = peewee.BigIntegerField()
    lesson_id = peewee.ForeignKeyField(Lesson, backref='purchases')
    price_paid_usd = peewee.DecimalField(max_digits=10, decimal_places=2)  # Цена которую заплатил
    price_paid_stars = peewee.IntegerField()  # Цена в звездах
    payment_id = peewee.TextField(null=True)  # ID платежа от Telegram
    promocode_used = peewee.TextField(null=True)  # Промокод если использовался
    purchase_date = peewee.DateTimeField(default=datetime.now)
    status = peewee.CharField(max_length=20, default='completed')  # completed, refunded, etc

    class Meta:
        database = con
        indexes = (
            (('user_id', 'lesson_id'), True),  # Unique constraint - один урок один раз на пользователя
        )

    async def create_purchase(self, user_id, lesson_id, price_paid_usd,
                          price_paid_stars, **kwargs):
        """Create purchase"""
        purchase = await orm.create(Purchase,
                                  user_id=user_id,
                                  lesson_id=lesson_id,
                                  price_paid_usd=price_paid_usd,
                                  price_paid_stars=price_paid_stars,
                                  **kwargs)
        return purchase

    async def get_user_purchases(self, user_id) :
        """Get all purchases by user"""
        purchases = await orm.execute(
            Purchase.select(Purchase, Lesson)
            .join(Lesson)
            .where(Purchase.user_id == user_id)
            .dicts() \
        )
        return list(purchases)

    async def check_user_has_lesson(self, user_id, lesson_id) :
        """Check if user already bought this lesson"""
        try:
            Purchase.get(
                (Purchase.user_id == user_id) & 
                (Purchase.lesson_id == lesson_id) & 
                (Purchase.status == 'completed'))
            return True
        except Purchase.DoesNotExist:
            return False
        except Exception as e:
            print(f"❌ Ошибка проверки владения уроком: {e}")
            return False

    async def get_all_purchases(self, limit=None) :
        """Get all purchases for admin statistics"""
        query = (Purchase.select(Purchase, Lesson)
                .join(Lesson)
                .order_by(Purchase.purchase_date.desc()))

        if limit:
            query = query.limit(limit)

        purchases = await orm.execute(query.dicts())
        return list(purchases)

    async def get_purchases_stats(self, days=None):
        """Get purchase statistics for period"""
        from datetime import timedelta
    
        query = Purchase.select()
        if days:
            date_from = datetime.now() - timedelta(days=days)
            query = query.where(Purchase.purchase_date >= date_from)
    
        purchases = await orm.execute(query.dicts())
        purchases_list = list(purchases)
    
        total_count = len(purchases_list)
        total_usd = sum(float(p['price_paid_usd']) for p in purchases_list)
    
        return {
            'count': total_count,
            'total_usd': total_usd
        }

    async def get_usd_to_stars_rate(self):
        """Get USD to Stars exchange rate"""
        rate = await self.get_setting('usd_to_stars_rate', '200')
        return int(rate or 200)

    async def set_usd_to_stars_rate(self, rate) :
        """Set USD to Stars exchange rate"""
        await self.set_setting('usd_to_stars_rate', str(rate))


class SystemSettings(peewee.Model):
    """Model for system settings"""

    setting_key = peewee.CharField(max_length=100, unique=True)
    setting_value = peewee.TextField()
    updated_at = peewee.DateTimeField(default=datetime.now())

    class Meta:
        database = con

    async def get_setting(self, key, default_value=None) :
        """Get setting by key"""
        try: 
            settings = SystemSettings.select().where(SystemSettings.setting_key == key)
            setting_list = list(settings)
            if setting_list: 
                return setting_list[0].setting_value
            else:
                return default_value
        except Exception as e:
            print(f"⚠️ Ошибка при получении настройки '{key}': {e}")
            return default_value

    async def set_setting(self, key, value) :
        """Set setting value using upsert pattern."""
        try: 
            # Пытаемся обновить существующую запись
            query = SystemSettings.update(
                setting_value=str(value),
                updated_at=datetime.now(),
            ).where(SystemSettings.setting_key == key)

            rows_updated = query.execute() 

            if rows_updated > 0: 
                print(f"✅ Настройка '{key}' обновлена на значение '{value}'")
            else: 
                # Если записи не существует, создаем новую
                await orm.create(SystemSettings,
                               setting_key=key,
                               setting_value=str(value),
                               updated_at=datetime.now())
                print(f"✅ Создана новая настройка '{key}' со значением '{value}'")
        except Exception as e: 
            print(f"❌ Ошибка при установке настройки '{key}': {e}")
            # Если произошла ошибка UNIQUE constraint из-за race condition, пытаемся только обновить
            if "UNIQUE constraint failed" in str(e):
                try:
                    query = SystemSettings.update(
                        setting_value=str(value),
                        updated_at=datetime.now()
                    ).where(SystemSettings.setting_key == key)
                    query.execute()
                    print(f"✅ Настройка '{key}' обновлена после конфликта уникальности")
                except Exception as update_error:
                    print(f"❌ Критическая ошибка при обновлении '{key}': {update_error}")
                    raise
            else:
                raise


class Promocode(peewee.Model):
    """Model for promocodes"""

    code = peewee.CharField(max_length=50, unique=True)
    discount_percent = peewee.IntegerField()  # Скидка в процентах
    discount_amount_usd = peewee.DecimalField(max_digits=10, decimal_places=2, null=True)  # Фиксированная скидка в USD
    usage_limit = peewee.IntegerField(null=True)  # Лимит использований (None = без лимита)
    used_count = peewee.IntegerField(default=0)  # Сколько раз использован
    is_active = peewee.BooleanField(default=True)  # Активен ли промокод
    expires_at = peewee.DateTimeField(null=True)  # Дата истечения (None = не истекает)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = con

    async def create_promocode(self, code, discount_percent=0, discount_amount_usd=None, **kwargs):  # Added leading slash
        """Create promocode"""

        promocode = await orm.create(Promocode,
                                   code=code.upper(),
                                   discount_percent=discount_percent,
                                   discount_amount_usd=discount_amount_usd,
                                   **kwargs)
        return promocode

    async def get_promocode(self, code) :  # Added leading slash
        """Get promocode by code"""
        try:
            query = Promocode.select().where(
                (Promocode.code == code.upper()) & (Promocode.is_active == True)
            )
            promocode = query.dicts().first()
            return promocode
        except Exception: 
            return None

    async def validate_promocode(self, code) :
        """Validate promocode"""
        promocode = await self.get_promocode(code)
        if not promocode: 
            return None, "Промокод не найден"

        # Check usage limit
        if promocode.usage_limit and promocode.used_count >= promocode.usage_limit:
            return None, "Промокод исчерпан"

        # Check expiry
        if promocode.expires_at and datetime.now() > promocode.expires_at:
            return None, "Промокод истек"

        return promocode, "OK"

    async def use_promocode(self, code):  # Removed a leading slash as it's a method
        """Mark promocode as used"""
        await orm.execute(
            Promocode.update(used_count=Promocode.used_count + 1).where(Promocode.code == code.upper())
        )

    async def calculate_discount(self, promocode, original_price_usd):  # Removed a leading slash as it's a method
        """Calculate discounted price"""


        if promocode.discount_amount_usd:
            # Fixed discount
            discount = float(promocode.discount_amount_usd) / 100

        else:
            # Percentage discount
            discount = float(original_price_usd) * promocode.discount_percent / 100 / 100

        final_price = max(0, float(original_price_usd) - discount)
        return final_price, discount

    async def get_all_promocodes(self):  # Removed a leading slash as it's a method
        """Get all promocodes for admin"""

        promocodes = await orm.execute(Promocode.select().dicts()())
        return list(promocodes)

class Translations(peewee.Model):
    """Model for translations of steps"""

    step_id = peewee.CharField(max_length=50)  # e.g. 'welcome', 'video_caption', 'catalog_menu'
    language = peewee.CharField(max_length=10)  # e.g. 'en', 'es', 'ru'
    text_field = peewee.CharField(max_length=50)  # e.g. 'text', 'caption', 'button_label'
    value = peewee.TextField()  # Translated text or caption
    created_at = peewee.DateTimeField(default=datetime.now())
    updated_at = peewee.DateTimeField(default=datetime.now())

    class Meta:
        database = con
        indexes = (
            (('step_id', 'language', 'text_field'), True),  # Unique per step-lang-field
        )

    async def create_translation(self, step_id, language, text_field, value) :
        """Create translation"""

        translation = await orm.create(Translations,
                                     step_id=step_id,
                                     language=language,
                                     text_field=text_field,
                                     value=value)
        return translation

    async def get_translation(self, step_id, language, text_field) :
        """Get translation by step, lang, field"""        
        try:
            query = Translations.select().where(
                (Translations.step_id == step_id) & 
                (Translations.language == language) & 
                (Translations.text_field == text_field)
            )
            translation = query.dicts().first()
            return translation['value'] if translation else None
        except Exception: 
            return None

    async def update_translation(self, step_id, language, text_field, value) :
        """Update translation"""
        await orm.execute(
            Translations.update(value=value, updated_at=datetime.now()).where(
                (Translations.step_id == step_id) &
                (Translations.language == language) &
                (Translations.text_field == text_field))
        )
