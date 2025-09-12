#!/usr/bin/env python3
"""Test database directly"""

import sqlite3

def test_direct():
    """Test database directly"""
    try:
        conn = sqlite3.connect('lesson.db')
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(leadmagnet)")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check data
        cursor.execute("SELECT * FROM leadmagnet WHERE id = 1")
        data = cursor.fetchone()
        print(f"\nData: {data}")
        
        # Test setting photo content
        cursor.execute("""
            UPDATE leadmagnet 
            SET content_type = 'photo', photo_file_id = 'test_photo_123', video_file_id = NULL
            WHERE id = 1
        """)
        conn.commit()
        
        # Verify update
        cursor.execute("SELECT id, content_type, video_file_id, photo_file_id, document_file_id FROM leadmagnet WHERE id = 1")
        updated_data = cursor.fetchone()
        print(f"Updated data: {updated_data}")
        
        conn.close()
        print("✅ Direct database test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False

if __name__ == "__main__":
    test_direct()