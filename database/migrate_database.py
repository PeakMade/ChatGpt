#!/usr/bin/env python3
"""
Migration Script: SQLite to PostgreSQL
Migrates existing conversation data from SQLite to PostgreSQL for multi-user support
"""

import sqlite3
import json
import os
from datetime import datetime
from database_multiuser import MultiUserDatabaseManager

def backup_sqlite_data():
    """Create a backup of SQLite data before migration"""
    if os.path.exists('chatgpt_conversations.db'):
        backup_name = f"chatgpt_conversations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        import shutil
        shutil.copy2('chatgpt_conversations.db', backup_name)
        print(f"✅ SQLite backup created: {backup_name}")
        return True
    else:
        print("ℹ️  No existing SQLite database found")
        return False

def migrate_sqlite_to_postgresql():
    """Migrate data from SQLite to PostgreSQL"""
    
    print("🚀 Starting SQLite to PostgreSQL Migration...")
    
    # Create backup first
    has_sqlite = backup_sqlite_data()
    
    # Initialize PostgreSQL database
    try:
        pg_db = MultiUserDatabaseManager()
        print("✅ PostgreSQL connection established")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        print("\n📋 Please ensure PostgreSQL is installed and running:")
        print("   1. Install PostgreSQL from: https://www.postgresql.org/download/")
        print("   2. Create database: CREATE DATABASE chatgpt_multiuser;")
        print("   3. Create user: CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';")
        print("   4. Grant permissions: GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;")
        return False
    
    if not has_sqlite:
        print("✅ PostgreSQL database initialized (no SQLite data to migrate)")
        return True
    
    try:
        # Connect to SQLite database
        sqlite_conn = sqlite3.connect('chatgpt_conversations.db')
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        
        # Create default user for migrated data
        print("👤 Creating default user for migrated data...")
        default_user_id = pg_db.create_user(
            username='migrated_user',
            email='migrated@localhost.com',
            password='changeme123'
        )
        
        if not default_user_id:
            print("❌ Could not create default user (may already exist)")
            # Try to find existing user
            user = pg_db.authenticate_user('migrated_user', 'changeme123')
            if user:
                default_user_id = user['id']
                print("✅ Using existing migrated_user account")
            else:
                print("❌ Migration failed - could not create or find default user")
                return False
        else:
            print(f"✅ Default user created with ID: {default_user_id}")
        
        # Count existing data
        cursor.execute('SELECT COUNT(*) FROM conversations')
        conv_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM messages')
        msg_count = cursor.fetchone()[0]
        
        print(f"📊 Found {conv_count} conversations and {msg_count} messages to migrate")
        
        if conv_count == 0:
            print("ℹ️  No data to migrate")
            sqlite_conn.close()
            return True
        
        # Migrate conversations
        print("📁 Migrating conversations...")
        cursor.execute('SELECT * FROM conversations WHERE is_deleted = FALSE OR is_deleted IS NULL')
        migrated_convs = 0
        
        for conv in cursor.fetchall():
            try:
                pg_db.create_conversation(
                    user_id=default_user_id,
                    conversation_id=conv['id'],
                    title=conv['title'] or 'Migrated Conversation'
                )
                migrated_convs += 1
            except Exception as e:
                print(f"⚠️  Warning: Could not migrate conversation {conv['id']}: {e}")
        
        print(f"✅ Migrated {migrated_convs}/{conv_count} conversations")
        
        # Migrate messages
        print("💬 Migrating messages...")
        cursor.execute('''
            SELECT * FROM messages 
            ORDER BY conversation_id, message_order ASC, timestamp ASC
        ''')
        migrated_msgs = 0
        
        for msg in cursor.fetchall():
            try:
                metadata = {}
                if msg['metadata']:
                    try:
                        metadata = json.loads(msg['metadata'])
                    except:
                        metadata = {'original_metadata': msg['metadata']}
                
                pg_db.save_message(
                    user_id=default_user_id,
                    conversation_id=msg['conversation_id'],
                    message_id=msg['id'],
                    role=msg['role'],
                    content=msg['content'],
                    tokens_used=msg['tokens_used'] or 0,
                    metadata=metadata
                )
                migrated_msgs += 1
            except Exception as e:
                print(f"⚠️  Warning: Could not migrate message {msg['id']}: {e}")
        
        print(f"✅ Migrated {migrated_msgs}/{msg_count} messages")
        
        sqlite_conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print(f"👤 Default user credentials:")
        print(f"   Username: migrated_user")
        print(f"   Password: changeme123")
        print(f"   User ID: {default_user_id}")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def cleanup_old_files():
    """Remove old SQLite database files"""
    files_to_remove = [
        'chatgpt_conversations.db',
        'database.py'
    ]
    
    print("\n🧹 Cleaning up old database files...")
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Removed: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not remove {file_path}: {e}")
        else:
            print(f"ℹ️  File not found: {file_path}")

def main():
    """Main migration process"""
    print("=" * 60)
    print("🔄 SQLite to PostgreSQL Migration Tool")
    print("=" * 60)
    
    # Step 1: Migrate data
    success = migrate_sqlite_to_postgresql()
    
    if not success:
        print("\n❌ Migration failed. Please check the errors above.")
        return
    
    # Step 2: Ask user about cleanup
    print("\n" + "=" * 60)
    cleanup_choice = input("🗑️  Remove old SQLite files? (y/N): ").lower().strip()
    
    if cleanup_choice in ['y', 'yes']:
        cleanup_old_files()
        print("✅ Cleanup completed")
    else:
        print("ℹ️  Old files kept for safety")
    
    print("\n" + "=" * 60)
    print("🎉 Migration Process Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Update your app.py to use database_multiuser.py")
    print("2. Add user authentication routes")
    print("3. Test the multi-user functionality")
    print("4. Change the default user password")
    print("\n🔗 See MIGRATION_GUIDE.md for detailed next steps")

if __name__ == "__main__":
    main()
