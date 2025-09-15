import config
import peewee
from datetime import datetime
from .core import con, orm
import logging


class User(peewee.Model):
    """Class for Telegram user"""

    user_id = peewee.BigIntegerField(unique=True)
    date_registered = peewee.DateTimeField(default=datetime.now)
    username = peewee.TextField(null=True)
    full_name = peewee.TextField()
    phone = peewee.TextField(null=True)
    lang = peewee.CharField(default='ru')  # Language code
    # Onboarding tracking fields
    onboarding_completed = peewee.BooleanField(default=False)
    last_onboarding_step = peewee.TextField(null=True)
    onboarding_completed_at = peewee.DateTimeField(null=True)
    # Extended onboarding data
    onboarding_goal = peewee.TextField(null=True)
    onboarding_level = peewee.TextField(null=True)
    consent_newsletter = peewee.BooleanField(default=False)
    
    class Meta:
        database = con   
        
    async def create_user(self, user_id, username, full_name):
        """Create user"""
        try:
            user = User.create(user_id=user_id, username=username, full_name=full_name)
            print(f"✅ Пользователь создан: {full_name} (ID: {user_id})")
            return user.id
        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            raise
    
    
    async def get_user(self, id):
        """Get user data"""
        try:
            users = list(User.select().where(User.user_id == id).dicts())
            
            if users:
                user = users[0]
                return user
            else:
                return None
        except Exception as e:
            print(f"❌ Ошибка получения пользователя {id}: {e}")
            return None
    
    
    async def update_user(self, user_id, key, value):
        """Update user"""
        try:
            User.update({key: value}).where(User.user_id == user_id).execute()
        except Exception as e:
            print(f"❌ Ошибка обновления пользователя {user_id}: {e}")
        
        
    async def delete_user(self, user_id):
        """Delete user"""
                
        await orm.execute(User.delete().where(User.user_id == user_id))
        
        
    async def get_all_users(self):
        """Load all users"""
        
        try:
            users = await orm.execute(User.select().dicts())
            users = list(users) if users else []
            return users
        except Exception as e:
            logging.error(f"Ошибка в get_all_users: {e}")
            return []
    
    
    async def mark_onboarding_complete(self, user_id):
        """Mark user onboarding as completed"""
        try:
            User.update({
                'onboarding_completed': True,
                'onboarding_completed_at': datetime.now()
            }).where(User.user_id == user_id).execute()
            print(f"✅ Onboarding завершен для пользователя {user_id}")
        except Exception as e:
            print(f"❌ Ошибка отметки onboarding: {e}")
        
        
    async def update_onboarding_step(self, user_id, step_key):
        """Update user's current onboarding step"""
        try:
            User.update({
                'last_onboarding_step': step_key
            }).where(User.user_id == user_id).execute()
        except Exception as e:
            print(f"❌ Ошибка обновления onboarding step: {e}")
        
        
    async def check_onboarding_status(self, user_id):
        """Check if user has completed onboarding"""
        try:
            user = await self.get_user(user_id)
            if user is None:
                return False
                
            return user.get('onboarding_completed', False)
        except Exception as e:
            print(f"❌ Ошибка проверки onboarding статуса: {e}")
            return False


    async def update_user_lang(self, user_id, lang):
        """Update user language"""
        try:
            User.update({'lang': lang}).where(User.user_id == user_id).execute()
            print(f"✅ Language updated for user {user_id} to {lang}")
        except Exception as e:
            print(f"❌ Error updating language for user {user_id}: {e}")
    
    async def get_total_users(self):
        """Get total number of users"""
        try:
            count = User.select().count()
            return count
        except Exception as e:
            logging.error(f"Error getting total users: {e}")
            return 0
    
    async def get_users_count_since(self, since_date):
        """Get number of users registered since date"""
        try:
            count = User.select().where(User.date_registered >= since_date).count()
            return count
        except Exception as e:
            logging.error(f"Error getting users since {since_date}: {e}")
            return 0
