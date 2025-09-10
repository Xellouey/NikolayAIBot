"""
Add lang column to user table for storing user language preference
"""
from database.core import con
import logging

def add_lang_column():
    """Add lang column to user table if it doesn't exist"""
    
    try:
        # Check if column already exists
        cursor = con.execute_sql("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'lang' in column_names:
            print("✅ Column 'lang' already exists in user table")
            return
        
        # Add lang column
        print("Adding 'lang' column to user table...")
        con.execute_sql("""
            ALTER TABLE user 
            ADD COLUMN lang VARCHAR(10) DEFAULT 'ru'
        """)
        print("✅ Successfully added 'lang' column to user table")
        
        # Set default language for existing users
        con.execute_sql("""
            UPDATE user 
            SET lang = 'ru' 
            WHERE lang IS NULL
        """)
        print("✅ Set default language 'ru' for existing users")
        
    except Exception as e:
        print(f"❌ Error adding lang column: {e}")
        logging.error(f"Error adding lang column: {e}")

if __name__ == "__main__":
    add_lang_column()
