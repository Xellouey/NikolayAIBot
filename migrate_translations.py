"""
Migration script to update translations table for simplified localization system
"""
import peewee
from database.core import con
from database.lesson import Translations
from datetime import datetime

def migrate_translations():
    """Migrate translations table to new structure"""
    
    print("Starting translations migration...")
    
    # Check if the old structure exists
    try:
        # Try to check if old columns exist
        cursor = con.execute_sql("PRAGMA table_info(translations)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'step_id' in column_names and 'text_field' in column_names:
            print("Old translations structure detected, migrating...")
            
            # Create new temporary table with new structure
            con.execute_sql("""
                CREATE TABLE IF NOT EXISTS translations_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_key VARCHAR(50) NOT NULL,
                    language VARCHAR(10) NOT NULL,
                    value TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(text_key, language)
                )
            """)
            
            # Copy existing data if any (mapping step_id to text_key)
            con.execute_sql("""
                INSERT OR IGNORE INTO translations_new (text_key, language, value, created_at, updated_at)
                SELECT step_id, language, value, created_at, updated_at
                FROM translations
                WHERE text_field = 'text'
            """)
            
            # Drop old table
            con.execute_sql("DROP TABLE translations")
            
            # Rename new table
            con.execute_sql("ALTER TABLE translations_new RENAME TO translations")
            
            print("Migration completed successfully!")
            
        elif 'text_key' in column_names:
            print("Table already has new structure, skipping migration")
        else:
            print("Unknown table structure, creating new table...")
            # Create new table
            con.execute_sql("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_key VARCHAR(50) NOT NULL,
                    language VARCHAR(10) NOT NULL,
                    value TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(text_key, language)
                )
            """)
            print("New translations table created!")
            
    except peewee.OperationalError as e:
        print(f"Table doesn't exist, creating new one: {e}")
        # Create new table
        con.execute_sql("""
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_key VARCHAR(50) NOT NULL,
                language VARCHAR(10) NOT NULL,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(text_key, language)
            )
        """)
        print("New translations table created!")
    
    # Add some default translations for testing
    try:
        # Example English translations
        default_translations = [
            ('welcome', 'en', '👋 Welcome to the AI School!\n\nHere you will learn to create amazing content using AI.'),
            ('btn_catalog', 'en', '📚 Lesson Catalog'),
            ('btn_my_lessons', 'en', '📝 My Lessons'),
            ('btn_support', 'en', '💬 Support'),
            ('btn_back', 'en', '⬅️ Back'),
            ('after_video', 'en', '👆 Great start! Now you can explore our lessons.'),
            
            # Example Spanish translations
            ('welcome', 'es', '👋 ¡Bienvenido a la Escuela de IA!\n\nAquí aprenderás a crear contenido increíble usando IA.'),
            ('btn_catalog', 'es', '📚 Catálogo de Lecciones'),
            ('btn_my_lessons', 'es', '📝 Mis Lecciones'),
            ('btn_support', 'es', '💬 Soporte'),
            ('btn_back', 'es', '⬅️ Atrás'),
            ('after_video', 'es', '👆 ¡Excelente comienzo! Ahora puedes explorar nuestras lecciones.'),
        ]
        
        for key, lang, value in default_translations:
            try:
                con.execute_sql(
                    "INSERT OR IGNORE INTO translations (text_key, language, value) VALUES (?, ?, ?)",
                    (key, lang, value)
                )
            except Exception as e:
                print(f"Skipping {key}/{lang}: {e}")
        
        print("Default translations added!")
        
    except Exception as e:
        print(f"Error adding default translations: {e}")
    
    print("Migration complete!")

if __name__ == "__main__":
    migrate_translations()
