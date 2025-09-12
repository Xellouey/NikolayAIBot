import config
import peewee
import logging
from datetime import datetime, timedelta
from .core import con, orm
from decimal import Decimal


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
    
    async def ensure_lead_magnet(self):
        """Ensure lead magnet lesson exists"""
        try:
            # Find or create free lesson
            lead_lesson = Lesson.select().where(
                (Lesson.is_free == True) & 
                (Lesson.is_active == True)
            ).first()
            
            if lead_lesson:
                return lead_lesson.id
            
            # Create default lead lesson if not exists
            lead_lesson = Lesson.create(
                title="Бесплатный вводный урок",
                description="Узнайте основы работы с нейросетями",
                price_usd=0,
                is_free=True,
                is_active=True,
                content_type='video'
            )
            return lead_lesson.id
            
        except Exception as e:
            print(f"❌ Ошибка создания лид-магнита: {e}")
            return None
    
    async def increment_views(self, lesson_id):
        """Increment lesson views count"""
        try:
            Lesson.update(
                views_count=Lesson.views_count + 1
            ).where(Lesson.id == lesson_id).execute()
            return True
        except Exception as e:
            print(f"❌ Ошибка увеличения просмотров: {e}")
            return False
    
    async def increment_purchases(self, lesson_id):
        """Increment lesson purchases count"""
        try:
            Lesson.update(
                purchases_count=Lesson.purchases_count + 1
            ).where(Lesson.id == lesson_id).execute()
            return True
        except Exception as e:
            print(f"❌ Ошибка увеличения покупок: {e}")
            return False
    
    async def create_lesson(self, title, description, price_usd, 
                           is_free=False, is_active=True, 
                           content_type='video', video_file_id=None,
                           preview_video_file_id=None, preview_text=None,
                           text_content=None, document_file_id=None, **kwargs):
        """Create new lesson"""
        try:
            lesson = Lesson.create(
                title=title,
                description=description,
                price_usd=price_usd,
                is_free=is_free,
                is_active=is_active,
                content_type=content_type,
                video_file_id=video_file_id,
                preview_video_file_id=preview_video_file_id,
                preview_text=preview_text,
                text_content=text_content,
                document_file_id=document_file_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **kwargs
            )
            print(f"✅ Урок '{title}' успешно создан с ID {lesson.id}")
            return lesson.id
        except Exception as e:
            print(f"❌ Ошибка создания урока: {e}")
            raise
    
    async def update_lesson(self, lesson_id, **fields):
        """Update lesson fields"""
        try:
            # Проверяем существование урока
            lesson = Lesson.get_or_none(Lesson.id == lesson_id)
            if not lesson:
                print(f"❌ Урок с ID {lesson_id} не найден")
                return False
            
            # Обновляем поля
            fields['updated_at'] = datetime.now()
            
            query = Lesson.update(**fields).where(Lesson.id == lesson_id)
            rows_updated = query.execute()
            
            if rows_updated > 0:
                print(f"✅ Урок ID {lesson_id} обновлен")
                return True
            else:
                print(f"⚠️ Урок ID {lesson_id} не был обновлен")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка обновления урока {lesson_id}: {e}")
            return False
    
    async def delete_lesson(self, lesson_id):
        """Delete lesson"""
        try:
            # Проверяем существование урока
            lesson = Lesson.get_or_none(Lesson.id == lesson_id)
            if not lesson:
                print(f"❌ Урок с ID {lesson_id} не найден")
                return False
            
            # Удаляем связанные покупки
            Purchase.delete().where(Purchase.lesson_id == lesson_id).execute()
            
            # Удаляем урок
            rows_deleted = Lesson.delete().where(Lesson.id == lesson_id).execute()
            
            if rows_deleted > 0:
                print(f"✅ Урок ID {lesson_id} удален")
                return True
            else:
                print(f"⚠️ Урок ID {lesson_id} не был удален")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка удаления урока {lesson_id}: {e}")
            return False


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
    
    async def get_sales_stats(self):
        """Get total sales statistics"""
        try:
            purchases = await orm.execute(Purchase.select().dicts())
            purchases_list = list(purchases)
            
            total_count = len(purchases_list)
            total_usd = sum(float(p['price_paid_usd']) for p in purchases_list)
            
            return {
                'count': total_count,
                'total': total_usd
            }
        except Exception as e:
            logging.error(f"Error getting sales stats: {e}")
            return {'count': 0, 'total': 0}
    
    async def get_sales_stats_period(self, days):
        """Get sales statistics for specific period in days"""
        from datetime import timedelta
        try:
            date_from = datetime.now() - timedelta(days=days)
            query = Purchase.select().where(Purchase.purchase_date >= date_from)
            purchases = await orm.execute(query.dicts())
            purchases_list = list(purchases)
            
            total_count = len(purchases_list)
            total_usd = sum(float(p['price_paid_usd']) for p in purchases_list)
            
            return {
                'count': total_count,
                'total': total_usd
            }
        except Exception as e:
            logging.error(f"Error getting sales stats for {days} days: {e}")
            return {'count': 0, 'total': 0}

    async def get_usd_to_stars_rate(self):
        """Get USD to Stars exchange rate"""
        rate = await self.get_setting('usd_to_stars_rate', '200')
        # Convert string to float first, then to int to handle decimal values like '77.0'
        return int(float(rate or 200))

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
    
    async def get_usd_to_stars_rate(self):
        """Get USD to Stars exchange rate"""
        rate = await self.get_setting('usd_to_stars_rate', '200')
        # Convert string to float first, then to int to handle decimal values like '77.0'
        return int(float(rate or 200))
    
    async def set_usd_to_stars_rate(self, rate):
        """Set USD to Stars exchange rate"""
        await self.set_setting('usd_to_stars_rate', str(rate))


class Promocode(peewee.Model):
    """Model for promocodes"""

    code = peewee.CharField(max_length=50, unique=True)
    # Новые поля
    discount_type = peewee.CharField(max_length=20, default='percentage')  # 'percentage' or 'fixed'
    discount_value = peewee.DecimalField(max_digits=10, decimal_places=2, default=0)  # Either percent or fixed USD amount
    # Старые поля для совместимости
    discount_percent = peewee.IntegerField(default=0)  # Legacy field
    discount_amount_usd = peewee.DecimalField(max_digits=10, decimal_places=2, null=True)  # Legacy field
    used_count = peewee.IntegerField(default=0)  # Legacy field
    
    usage_limit = peewee.IntegerField(null=True)  # Usage limit (None = unlimited)
    usage_count = peewee.IntegerField(default=0)  # Times used
    is_active = peewee.BooleanField(default=True)  # Is active
    expires_at = peewee.DateTimeField(null=True)  # Expiry date (None = never expires)
    created_at = peewee.DateTimeField(default=datetime.now)

    class Meta:
        database = con

    async def create_promocode(self, code, discount_type='percentage', discount_value=0, **kwargs):  # Fixed parameters
        """Create promocode"""
        
        # Подготавливаем данные для создания промокода
        promocode_data = {
            'code': code.upper(),
            'discount_type': discount_type,
            'discount_value': discount_value,
            **kwargs
        }
        
        # Заполняем старые поля для совместимости с существующей структурой БД
        if discount_type == 'percentage':
            # Для процентных скидок заполняем discount_percent
            percent_value = float(discount_value) * 100 if float(discount_value) <= 1 else float(discount_value)
            promocode_data['discount_percent'] = int(percent_value)
            promocode_data['discount_amount_usd'] = None
        else:  # fixed
            # Для фиксированных скидок заполняем discount_amount_usd
            promocode_data['discount_percent'] = 0  # Заполняем 0 для NOT NULL поля
            promocode_data['discount_amount_usd'] = discount_value
        
        # Заполняем used_count для совместимости
        promocode_data['used_count'] = 0

        promocode = await orm.create(Promocode, **promocode_data)
        return promocode

    async def get_promocode(self, code) :  # Added leading slash
        """Get ACTIVE promocode by code (for applying)"""
        try:
            query = Promocode.select().where(
                (Promocode.code == code.upper()) & (Promocode.is_active == True)
            )
            promocode = query.dicts().first()
            return promocode
        except Exception:
            return None

    async def get_promocode_any(self, code):
        """Get promocode by code regardless of is_active (for uniqueness checks)"""
        try:
            query = Promocode.select().where(Promocode.code == code.upper())
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
        if promocode.get('usage_limit') and promocode.get('usage_count', 0) >= promocode['usage_limit']:
            return None, "Промокод исчерпан"

        # Check expiry
        if promocode.get('expires_at'):
            from datetime import datetime
            expires_at = promocode['expires_at']
            if isinstance(expires_at, str):
                # Пытаемся распарсить несколько форматов времени
                parsed = None
                try:
                    parsed = datetime.fromisoformat(expires_at)  # поддерживает 'YYYY-MM-DD HH:MM[:SS]'
                except Exception:
                    try:
                        parsed = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        try:
                            parsed = datetime.strptime(expires_at, '%d.%m.%Y %H:%M')
                        except Exception:
                            parsed = None
                expires_at = parsed or None
            if expires_at and datetime.now() > expires_at:
                return None, "Промокод истек"

        return promocode, "OK"

    async def use_promocode(self, code):  # Removed a leading slash as it's a method
        """Mark promocode as used"""
        await orm.execute(
            Promocode.update(usage_count=Promocode.usage_count + 1).where(Promocode.code == code.upper())
        )

    async def calculate_discount(self, promocode, original_price_usd):  # Removed a leading slash as it's a method
        """Calculate discounted price"""
        
        # Handle both dict and object access
        if isinstance(promocode, dict):
            discount_type = promocode.get('discount_type', 'percentage')
            discount_value = float(promocode.get('discount_value', 0))
        else:
            discount_type = getattr(promocode, 'discount_type', 'percentage')
            discount_value = float(getattr(promocode, 'discount_value', 0))
        
        if discount_type == 'fixed':
            # Fixed discount in USD
            discount = discount_value
        else:  # percentage
            # Percentage discount - исправляем логику для правильного расчета
            # Если значение <= 1, считаем что это доля (0.20 = 20%)
            if discount_value <= 1:
                discount = float(original_price_usd) * discount_value
            else:
                # Если > 1, считаем что это уже проценты (20 = 20%)
                discount = float(original_price_usd) * discount_value / 100

        final_price = max(0, float(original_price_usd) - discount)
        return final_price, discount

    async def get_all_promocodes(self, only_active=False):  # Removed a leading slash as it's a method
        """Get all promocodes for admin"""
        try:
            # Используем синхронный метод list() для получения всех записей
            query = Promocode.select()
            if only_active:
                query = query.where(Promocode.is_active == True)
            promocodes = list(query.dicts())
            return promocodes
        except Exception as e:
            print(f"❌ Ошибка получения списка промокодов: {e}")
            return []
    
    async def get_promocode_by_id(self, promo_id):
        """Get promocode by ID"""
        try:
            promocode = Promocode.get_by_id(promo_id)
            return promocode
        except:
            return None
    
    async def delete_promocode(self, promo_id):
        """Physically delete promocode (hard delete)"""
        try:
            rows = Promocode.delete().where(Promocode.id == promo_id).execute()
            if rows > 0:
                print(f"✅ Промокод ID {promo_id} удалён (hard delete)")
                return True
            else:
                print(f"⚠️ Промокод ID {promo_id} не найден для удаления")
                return False
        except Exception as e:
            print(f"❌ Ошибка удаления промокода {promo_id}: {e}")
            return False
    
    async def purge_inactive_promocodes(self):
        """Delete all previously soft-deleted promocodes (is_active = False)"""
        try:
            rows = Promocode.delete().where(Promocode.is_active == False).execute()
            print(f"🧹 Удалено неактивных промокодов: {rows}")
            return rows
        except Exception as e:
            print(f"❌ Ошибка при очистке неактивных промокодов: {e}")
            return 0
    
    def format_discount(self, discount_type, discount_value):
        """Format discount for display"""
        if discount_type in ('percent', 'percentage', '%'):
            # Если значение <= 1, считаем что это доля (0.15 = 15%)
            # Если > 1, считаем что это уже проценты (15 = 15%)
            val = float(discount_value)
            if val <= 1:
                val = val * 100
            
            if val.is_integer():
                return f"{int(val)}%"
            else:
                return f"{val:.1f}%"
        else:  # fixed
            val = float(discount_value)
            if val.is_integer():
                return f"${int(val)}"
            else:
                return f"${val:.2f}"

class Translations(peewee.Model):
    """Model for text translations (simplified)"""

    text_key = peewee.CharField(max_length=50)  # e.g. 'welcome', 'btn_catalog', 'lesson_price'
    language = peewee.CharField(max_length=10)  # e.g. 'en', 'es', 'de'
    value = peewee.TextField()  # Translated text
    created_at = peewee.DateTimeField(default=datetime.now())
    updated_at = peewee.DateTimeField(default=datetime.now())

    class Meta:
        database = con
        indexes = (
            (('text_key', 'language'), True),  # Unique per key-lang
        )

    # Note: Methods removed - we use static access through localization.py instead
