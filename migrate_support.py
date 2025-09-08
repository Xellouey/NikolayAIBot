#!/usr/bin/env python3
"""
Database migration script for adding support ticket system to existing NikolayAI installations.

This script creates the necessary tables for the support ticket system:
- support_ticket: Main ticket table
- ticket_message: Messages within tickets

Usage:
    python migrate_support.py

The script will:
1. Check if the tables already exist
2. Create them if they don't exist
3. Provide feedback on the migration status
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.core import con
from database.support import SupportTicket, TicketMessage
import logging

def run_migration():
    """Run the support ticket system migration"""
    
    print("🚀 Starting Support Ticket System Migration...")
    print("-" * 50)
    
    try:
        # Check if tables already exist
        existing_tables = con.get_tables()
        
        tables_to_create = []
        if 'supportticket' not in existing_tables:
            tables_to_create.append(SupportTicket)
        else:
            print("✅ Table 'supportticket' already exists")
            
        if 'ticketmessage' not in existing_tables:
            tables_to_create.append(TicketMessage)
        else:
            print("✅ Table 'ticketmessage' already exists")
        
        if tables_to_create:
            print(f"📦 Creating {len(tables_to_create)} new table(s)...")
            
            # Create the tables
            con.create_tables(tables_to_create)
            
            for table in tables_to_create:
                table_name = table._meta.table_name
                print(f"✅ Created table: {table_name}")
            
            print("\n🎉 Migration completed successfully!")
            print("📋 Support ticket system is now ready to use")
            
        else:
            print("\n📋 All support ticket tables already exist")
            print("✅ No migration needed")
        
        # Verify tables were created successfully
        print("\n🔍 Verifying table structure...")
        
        final_tables = con.get_tables()
        if 'supportticket' in final_tables and 'ticketmessage' in final_tables:
            print("✅ All support ticket tables verified successfully")
            
            # Show table info
            print("\n📊 Table Information:")
            print("  - supportticket: Stores main ticket information")
            print("  - ticketmessage: Stores messages within tickets")
            
        else:
            print("❌ Verification failed - some tables are missing")
            return False
            
        print("\n🚀 Support ticket system is ready!")
        print("Users can now create tickets via the 'Поддержка' button")
        print("Admins can manage tickets via the admin panel")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        logging.error(f"Migration error: {e}")
        return False
    
    finally:
        print("\n" + "-" * 50)


def rollback_migration():
    """Rollback the migration (remove support ticket tables)"""
    
    print("⚠️  Starting Support Ticket System Rollback...")
    print("-" * 50)
    
    try:
        existing_tables = con.get_tables()
        
        tables_to_drop = []
        if 'ticketmessage' in existing_tables:
            tables_to_drop.append(TicketMessage)
        if 'supportticket' in existing_tables:
            tables_to_drop.append(SupportTicket)
        
        if tables_to_drop:
            print(f"🗑️  Dropping {len(tables_to_drop)} table(s)...")
            
            con.drop_tables(tables_to_drop)
            
            for table in tables_to_drop:
                table_name = table._meta.table_name
                print(f"✅ Dropped table: {table_name}")
            
            print("\n✅ Rollback completed successfully!")
            
        else:
            print("📋 No support ticket tables found to remove")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        logging.error(f"Rollback error: {e}")
        return False
    
    finally:
        print("\n" + "-" * 50)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Support Ticket System Migration')
    parser.add_argument('--rollback', action='store_true', 
                       help='Rollback the migration (remove support ticket tables)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    if args.rollback:
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)