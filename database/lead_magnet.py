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
    
    # Content type and file storage
    content_type = peewee.CharField(max_length=20, default='video')  # video, photo, document
    video_file_id = peewee.TextField(null=True)
    photo_file_id = peewee.TextField(null=True)
    document_file_id = peewee.TextField(null=True)
    
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
                    content_type='video',
                    video_file_id=None,
                    photo_file_id=None,
                    document_file_id=None,
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
            
            # Check if content exists before enabling
            if enabled and not cls._has_content(lead_magnet):
                logging.warning("Cannot enable lead magnet without content")
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
    async def set_content(cls, content_type: str, file_id: str):
        """Set content based on type (backward compatible). Preserves other kinds.
        - If content_type is 'video' or 'photo': sets media and clears the alternative media, keeps document
        - If content_type is 'document': sets document and keeps media
        """
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            if content_type in ('video', 'photo'):
                # Set media: clear alternative media only
                if content_type == 'video':
                    lead_magnet.video_file_id = file_id
                    lead_magnet.photo_file_id = None
                    lead_magnet.content_type = 'video'
                else:
                    lead_magnet.photo_file_id = file_id
                    lead_magnet.video_file_id = None
                    lead_magnet.content_type = 'photo'
                # keep document_file_id as is
            elif content_type == 'document':
                # Set only document
                lead_magnet.document_file_id = file_id
                # keep media and content_type as is
            else:
                return False
            
            lead_magnet.updated_at = datetime.now()
            lead_magnet.save()
            return True
            
        except Exception as e:
            logging.error(f"Error setting content: {e}")
            return False
    
    @classmethod
    async def set_media(cls, content_type: str, file_id: str):
        """Set media (video or photo), preserving document."""
        if content_type not in ('video', 'photo'):
            return False
        return await cls.set_content(content_type, file_id)
    
    @classmethod
    async def set_document(cls, file_id: str):
        """Set document, preserving media."""
        return await cls.set_content('document', file_id)
    
    @classmethod
    async def get_content_bundle(cls):
        """Get both media (type and id) and document id.
        Returns: (media_type, media_file_id, document_file_id)
        media_type can be 'video', 'photo', or None
        """
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return None, None, None
            media_type = None
            media_id = None
            if lead_magnet.video_file_id:
                media_type = 'video'
                media_id = lead_magnet.video_file_id
            elif lead_magnet.photo_file_id:
                media_type = 'photo'
                media_id = lead_magnet.photo_file_id
            return media_type, media_id, lead_magnet.document_file_id
        except Exception as e:
            logging.error(f"Error getting content bundle: {e}")
            return None, None, None
    
    @classmethod
    async def set_video(cls, file_id: str):
        """Backward compatibility method for set_video"""
        return await cls.set_content('video', file_id)
    
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
        """Check if lead magnet is ready to be shown (enabled and has content)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return False
            
            return lead_magnet.enabled and cls._has_content(lead_magnet)
            
        except Exception as e:
            logging.error(f"Error checking if lead magnet is ready: {e}")
            return False
    
    @classmethod
    def _has_content(cls, lead_magnet):
        """Check if lead magnet has any content"""
        return any([
            lead_magnet.video_file_id,
            lead_magnet.photo_file_id,
            lead_magnet.document_file_id
        ])
    
    @classmethod
    async def get_current_content(cls):
        """Get current content info (type and file_id)"""
        try:
            lead_magnet = await cls.get_lead_magnet()
            if not lead_magnet:
                return None, None
            
            content_type = lead_magnet.content_type
            file_id = None
            
            if content_type == 'video':
                file_id = lead_magnet.video_file_id
            elif content_type == 'photo':
                file_id = lead_magnet.photo_file_id
            elif content_type == 'document':
                file_id = lead_magnet.document_file_id
            
            return content_type, file_id
            
        except Exception as e:
            logging.error(f"Error getting current content: {e}")
            return None, None


# Create table if not exists
def create_table():
    """Create lead magnet table if it doesn't exist"""
    try:
        con.create_tables([LeadMagnet])
        print("✅ Lead magnet table created")
        
        # Ensure default row exists (only for basic fields first)
        existing = LeadMagnet.get_or_none(LeadMagnet.id == 1)
        if not existing:
            # Create with minimal required fields first
            import sqlite3
            cursor = con.cursor()
            cursor.execute("""
                INSERT INTO leadmagnet (id, enabled, greeting_text, lessons_label, updated_at)
                VALUES (1, 0, '\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c! \u042d\u0442\u043e \u0432\u0432\u043e\u0434\u043d\u044b\u0439 \u0443\u0440\u043e\u043a.', '\u041f\u0440\u0438\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439 \u0432\u0432\u043e\u0434\u043d\u044b\u0439 \u0443\u0440\u043e\u043a', datetime('now'))
            """)
            con.commit()
            print("✅ Default lead magnet configuration created")
            
    except Exception as e:
        logging.error(f"Error creating lead magnet table: {e}")
        print(f"❌ Error: {e}")
