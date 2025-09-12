#!/usr/bin/env python3
"""
Initialize LeadMagnet table with basic structure
"""

import sys
import sqlite3
import logging
from datetime import datetime

# Add project root to path
sys.path.append('.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_leadmagnet_table():
    """Create leadmagnet table with basic structure"""
    
    # Database path
    db_path = 'lesson.db'
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table with basic structure first (without new fields)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leadmagnet (
                id INTEGER PRIMARY KEY DEFAULT 1,
                enabled BOOLEAN DEFAULT 0,
                greeting_text TEXT DEFAULT 'Добро пожаловать! Это вводный урок.',
                lessons_label TEXT DEFAULT 'Приветственный вводный урок',
                video_file_id TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default row if not exists
        cursor.execute("SELECT COUNT(*) FROM leadmagnet WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO leadmagnet (id, enabled, greeting_text, lessons_label, video_file_id, updated_at)
                VALUES (1, 0, 'Добро пожаловать! Это вводный урок.', 'Приветственный вводный урок', NULL, datetime('now'))
            """)
            logger.info("✅ Default lead magnet record created")
        
        # Now add new columns
        try:
            cursor.execute("ALTER TABLE leadmagnet ADD COLUMN content_type VARCHAR(20) DEFAULT 'video'")
            logger.info("✅ Added content_type column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️  content_type column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE leadmagnet ADD COLUMN photo_file_id TEXT")
            logger.info("✅ Added photo_file_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️  photo_file_id column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE leadmagnet ADD COLUMN document_file_id TEXT")
            logger.info("✅ Added document_file_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info("ℹ️  document_file_id column already exists")
            else:
                raise
        
        # Update existing records to have content_type = 'video' if they have video_file_id
        cursor.execute("""
            UPDATE leadmagnet 
            SET content_type = 'video' 
            WHERE video_file_id IS NOT NULL AND (content_type IS NULL OR content_type = '')
        """)
        
        # Update records without content to have default content_type
        cursor.execute("""
            UPDATE leadmagnet 
            SET content_type = 'video' 
            WHERE content_type IS NULL OR content_type = ''
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify final structure
        cursor.execute("PRAGMA table_info(leadmagnet)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Final table structure: {columns}")
        
        logger.info("✅ LeadMagnet table setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table setup failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    print("🔄 Setting up LeadMagnet table...")
    
    if create_leadmagnet_table():
        print("✅ LeadMagnet table setup completed")
        print("\n🎉 Lead magnet multi-content support is now available!")
        print("\nNext steps:")
        print("1. Restart the bot")
        print("2. Go to admin panel (/admin)")
        print("3. Open 'Лид-магнит' section")
        print("4. Try uploading different content types")
    else:
        print("❌ Table setup failed")
        sys.exit(1)