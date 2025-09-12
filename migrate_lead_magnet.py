#!/usr/bin/env python3
"""Migration script to create lead magnet table"""
import sys
import logging
from database.lead_magnet import LeadMagnet, create_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    """Run migration"""
    try:
        print("🔧 Creating lead magnet table...")
        create_table()
        
        # Verify table exists
        lead_magnet = LeadMagnet.get_or_none(LeadMagnet.id == 1)
        if lead_magnet:
            print(f"✅ Lead magnet table created successfully")
            print(f"   - Enabled: {lead_magnet.enabled}")
            print(f"   - Video: {'Set' if lead_magnet.video_file_id else 'Not set'}")
        else:
            print("❌ Failed to create lead magnet table")
            return 1
        
        print("\n✅ Migration complete!")
        return 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logging.error(f"Migration error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
