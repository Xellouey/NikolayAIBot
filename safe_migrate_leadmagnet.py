#!/usr/bin/env python3
"""
Safe migration approach: recreate table with new structure
"""

import sys
import sqlite3
import logging

sys.path.append('.')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_migrate_leadmagnet():
    """Safely migrate leadmagnet table"""
    
    db_path = 'shop_bot.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists and get its current structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leadmagnet'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Get current data
            cursor.execute("SELECT * FROM leadmagnet WHERE id = 1")
            existing_data = cursor.fetchone()
            logger.info(f"Found existing data: {existing_data}")
            
            # Drop and recreate table with new structure
            cursor.execute("DROP TABLE leadmagnet")
            logger.info("✅ Dropped old table")
        
        # Create new table with full structure
        cursor.execute("""
            CREATE TABLE leadmagnet (
                id INTEGER PRIMARY KEY DEFAULT 1,
                enabled BOOLEAN DEFAULT 0,
                greeting_text TEXT DEFAULT 'Добро пожаловать! Это вводный урок.',
                lessons_label TEXT DEFAULT 'Приветственный вводный урок',
                content_type VARCHAR(20) DEFAULT 'video',
                video_file_id TEXT,
                photo_file_id TEXT,
                document_file_id TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created new table with full structure")
        
        # Insert data (preserve existing or use defaults)
        if table_exists and existing_data:
            # Preserve existing data
            enabled = existing_data[1] if len(existing_data) > 1 else 0
            greeting_text = existing_data[2] if len(existing_data) > 2 else 'Добро пожаловать! Это вводный урок.'
            lessons_label = existing_data[3] if len(existing_data) > 3 else 'Приветственный вводный урок'
            video_file_id = existing_data[4] if len(existing_data) > 4 else None
            
            cursor.execute("""
                INSERT INTO leadmagnet 
                (id, enabled, greeting_text, lessons_label, content_type, video_file_id, photo_file_id, document_file_id, updated_at)
                VALUES (1, ?, ?, ?, 'video', ?, NULL, NULL, datetime('now'))
            """, (enabled, greeting_text, lessons_label, video_file_id))
            logger.info("✅ Preserved existing data")
        else:
            # Create default record
            cursor.execute("""
                INSERT INTO leadmagnet 
                (id, enabled, greeting_text, lessons_label, content_type, video_file_id, photo_file_id, document_file_id, updated_at)
                VALUES (1, 0, 'Добро пожаловать! Это вводный урок.', 'Приветственный вводный урок', 'video', NULL, NULL, NULL, datetime('now'))
            """)
            logger.info("✅ Created default record")
        
        # Commit changes
        conn.commit()
        
        # Verify final structure
        cursor.execute("PRAGMA table_info(leadmagnet)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Final table structure: {columns}")
        
        # Verify data
        cursor.execute("SELECT * FROM leadmagnet WHERE id = 1")
        final_data = cursor.fetchone()
        logger.info(f"Final data: {final_data}")
        
        logger.info("✅ Safe migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Safe migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    print("🔄 Starting safe LeadMagnet migration...")
    
    if safe_migrate_leadmagnet():
        print("✅ Safe migration completed")
        print("\nNow test the functionality:")
        print("python test_leadmagnet_multicontent.py")
    else:
        print("❌ Safe migration failed")
        sys.exit(1)