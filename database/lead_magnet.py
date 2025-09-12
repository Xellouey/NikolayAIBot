"""Lead magnet database model and management functions"""
import json
import logging
from datetime import datetime
import peewee
from .core import con

class LeadMagnet(peewee.Model):
    """Model for lead magnet configuration (single row table)"""
    
    id = peewee.IntegerField(primary_key=True, default=1)  # Always 1 for single row
    enabled = peewee.BooleanField(default=False)
    greeting_text = peewee.TextField(default='Добро пожаловать! Это вводный урок.')
    lessons_label = peewee.TextField(default='Приветственный вводный урок')
    video_file_id = peewee.TextField(null=True)
    updated_at = peewee.DateTimeField(default=datetime.now)
    
    class Meta:
        database = con
    
    @classmethod
    async def get_lead_magnet(cls):
        """Get lead magnet configuration"""
        try:
            lead_magnet = cls.get_or_none(cls.id == 1)
            if not lead_magnet:
                # Create default if doesn't exist
                lead_magnet = cls.create(
                    id=1,
                    enabled=False,
                    greeting_text='Добро пожаловать! Это вводный урок.',
                    lessons_label='Приветственный вводный урок',
                    video_file_id=None,
                    updated_at=datetime.now()
                )
            return lead_magnet
        except Exception as e:
            logging.error(f"Error getting lead magnet: {e}")
            return None
    
    @classmethod
    async def set_enabled(cls, enabled: bool):
        """Enable or disable lead magnet"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            # Check if video exists before enabling
            if enabled and not lead_magnet.video_file_id:
                logging.warning("Cannot enable lead magnet without video")
                return False
            
            lead_magnet.enabled = enabled
            lead_magnet.updated_at = datetime.now()
            lead_magnet.save()
            return True
            
        except Exception as e:
            logging.error(f"Error setting lead magnet enabled status: {e}")
            return False
    
    @classmethod
    async def set_greeting_text(cls, locale: str, text: str):
        """Set greeting text (locale param ignored for simplicity)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            # Просто сохраняем текст напрямую без JSON
            lead_magnet.greeting_text = text
            lead_magnet.updated_at = datetime.now()
            lead_magnet.save()
            return True
            
        except Exception as e:
            logging.error(f"Error setting greeting text: {e}")
            return False
    
    @classmethod
    async def set_lessons_label(cls, locale: str, text: str):
        """Set lessons label (locale param ignored for simplicity)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            # Просто сохраняем текст напрямую без JSON
            lead_magnet.lessons_label = text
            lead_magnet.updated_at = datetime.now()
            lead_magnet.save()
            return True
            
        except Exception as e:
            logging.error(f"Error setting lessons label: {e}")
            return False
    
    @classmethod
    async def set_video(cls, file_id: str):
        """Set video file ID"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            lead_magnet.video_file_id = file_id
            lead_magnet.updated_at = datetime.now()
            lead_magnet.save()
            return True
            
        except Exception as e:
            logging.error(f"Error setting video: {e}")
            return False
    
    @classmethod
    async def get_text_for_locale(cls, field: str, locale: str):
        """Get text (locale param ignored for simplicity)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return None
            
            # Просто возвращаем текст напрямую без JSON
            if field == 'greeting_text':
                return lead_magnet.greeting_text or "Добро пожаловать! Это вводный урок."
            elif field == 'lessons_label':
                return lead_magnet.lessons_label or "Приветственный вводный урок"
            else:
                return None
            
        except Exception as e:
            logging.error(f"Error getting text: {e}")
            return None
    
    @classmethod
    async def is_ready(cls):
        """Check if lead magnet is ready to be shown (enabled and has video)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            return lead_magnet.enabled and lead_magnet.video_file_id is not None
            
        except Exception as e:
            logging.error(f"Error checking if lead magnet is ready: {e}")
            return False


# Create table if not exists
def create_table():
    """Create lead magnet table if it doesn't exist"""
    try:
        con.create_tables([LeadMagnet])
        print("✅ Lead magnet table created")
        
        # Ensure default row exists
        if not LeadMagnet.get_or_none(LeadMagnet.id == 1):
            LeadMagnet.create(
                id=1,
                enabled=False,
                greeting_text='Добро пожаловать! Это вводный урок.',
                lessons_label='Приветственный вводный урок',
                video_file_id=None
            )
            print("✅ Default lead magnet configuration created")
            
    except Exception as e:
        logging.error(f"Error creating lead magnet table: {e}")
