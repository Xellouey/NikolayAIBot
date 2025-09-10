"""
Update back button icon from 🔙 to ⬅️ in database
"""
from database.core import con

def update_back_icon():
    """Update all back button icons in translations table"""
    
    try:
        # Update btn_back translations
        cursor = con.execute_sql(
            "UPDATE translations SET value = REPLACE(value, '🔙', '⬅️') WHERE text_key = 'btn_back'"
        )
        rows_updated = cursor.rowcount
        print(f"✅ Updated {rows_updated} translations for btn_back")
        
        # Also update any other texts that might contain the old icon
        cursor = con.execute_sql(
            "UPDATE translations SET value = REPLACE(value, '🔙', '⬅️') WHERE value LIKE '%🔙%'"
        )
        rows_updated = cursor.rowcount
        print(f"✅ Updated {rows_updated} other translations containing 🔙")
        
        print("\n✅ Successfully updated all back button icons from 🔙 to ⬅️")
        
    except Exception as e:
        print(f"❌ Error updating icons: {e}")

if __name__ == "__main__":
    update_back_icon()
