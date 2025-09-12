#!/usr/bin/env python3
"""
Migration script to add multi-content support to LeadMagnet table
Adds content_type, photo_file_id, and document_file_id fields
"""

import sys
import sqlite3
import logging
from datetime import datetime

# Add project root to path
sys.path.append('.')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_lead_magnet_table():
    """Add new fields to lead_magnet table for multi-content support"""
    
    # Database path
    db_path = 'lesson.db'
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leadmagnet'")
        if not cursor.fetchone():
            logger.error("❌ LeadMagnet table does not exist. Please run main application first.")
            return False
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(leadmagnet)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('content_type', 'VARCHAR(20) DEFAULT "video"'),
            ('photo_file_id', 'TEXT'),
            ('document_file_id', 'TEXT')
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE leadmagnet ADD COLUMN {column_name} {column_def}")
                    logger.info(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    logger.error(f"❌ Error adding column {column_name}: {e}")
                    conn.rollback()
                    return False
            else:
                logger.info(f"ℹ️  Column {column_name} already exists")
        
        # Update existing records to have content_type = 'video' if they have video_file_id
        cursor.execute("""
            UPDATE leadmagnet 
            SET content_type = 'video' 
            WHERE video_file_id IS NOT NULL AND content_type IS NULL
        """)
        
        # Update records without content to have default content_type
        cursor.execute("""
            UPDATE leadmagnet 
            SET content_type = 'video' 
            WHERE content_type IS NULL OR content_type = ''
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify changes
        cursor.execute("PRAGMA table_info(leadmagnet)")
        final_columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Final columns: {final_columns}")
        
        # Show current data
        cursor.execute("SELECT * FROM leadmagnet")
        rows = cursor.fetchall()
        logger.info(f"Current data rows: {len(rows)}")
        
        logger.info("✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


def verify_migration():
    """Verify that migration was successful"""
    try:
        # Import after migration to ensure new schema is loaded
        from database.lead_magnet import LeadMagnet
        
        # Test creating/getting lead magnet
        import asyncio
        
        async def test():
            lead_magnet = await LeadMagnet.get_lead_magnet()
            if lead_magnet:
                logger.info("✅ LeadMagnet model works correctly")
                logger.info(f"   - content_type: {getattr(lead_magnet, 'content_type', 'NOT FOUND')}")
                logger.info(f"   - video_file_id: {getattr(lead_magnet, 'video_file_id', 'NOT FOUND')}")
                logger.info(f"   - photo_file_id: {getattr(lead_magnet, 'photo_file_id', 'NOT FOUND')}")
                logger.info(f"   - document_file_id: {getattr(lead_magnet, 'document_file_id', 'NOT FOUND')}")
                return True
            else:
                logger.error("❌ Failed to get LeadMagnet")
                return False
        
        return asyncio.run(test())
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Starting LeadMagnet table migration...")
    
    # Run migration
    if migrate_lead_magnet_table():
        print("✅ Database migration completed")
        
        # Verify migration
        print("🔍 Verifying migration...")
        if verify_migration():
            print("✅ Migration verification successful")
            print("\n🎉 Lead magnet multi-content support is now available!")
            print("\nNext steps:")
            print("1. Restart the bot")
            print("2. Go to admin panel (/admin)")
            print("3. Open 'Лид-магнит' section")
            print("4. Try uploading different content types")
        else:
            print("❌ Migration verification failed")
            sys.exit(1)
    else:
        print("❌ Migration failed")
        sys.exit(1)