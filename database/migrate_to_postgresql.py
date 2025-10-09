"""
SQLite to PostgreSQL Migration Script
Migrates existing conversations and messages to multi-user PostgreSQL database
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our new multi-user database manager
try:
    from database_multiuser import MultiUserDatabaseManager
except ImportError:
    print("❌ Error: Could not import MultiUserDatabaseManager")
    print("Make sure you have installed the required packages:")
    print("pip install psycopg2-binary sqlalchemy flask-login flask-bcrypt cryptography")
    sys.exit(1)

def backup_sqlite_data():
    """Create a backup of existing SQLite database"""
    if os.path.exists('chatgpt_conversations.db'):
        backup_name = f'chatgpt_conversations_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        import shutil
        shutil.copy2('chatgpt_conversations.db', backup_name)
        print(f"✅ SQLite database backed up as: {backup_name}")
        return True
    else:
        print("ℹ️  No existing SQLite database found to backup")
        return False

def check_postgresql_connection():
    """Test PostgreSQL connection"""
    try:
        db = MultiUserDatabaseManager()
        # Try to connect
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL connection successful: {version}")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n📋 To fix this:")
        print("1. Install PostgreSQL: https://www.postgresql.org/download/")
        print("2. Create database and user:")
        print("   CREATE DATABASE chatgpt_multiuser;")
        print("   CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';")
        print("   GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;")
        print("3. Update .env file with correct database credentials")
        return False

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Check if SQLite database exists
    if not os.path.exists('chatgpt_conversations.db'):
        print("ℹ️  No SQLite database found. Creating fresh PostgreSQL database...")
        db = MultiUserDatabaseManager()
        print("✅ Fresh PostgreSQL database initialized")
        return True
    
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    
    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect('chatgpt_conversations.db')
        sqlite_conn.row_factory = sqlite3.Row
        cursor = sqlite_conn.cursor()
        print("✅ Connected to SQLite database")
    except Exception as e:
        print(f"❌ Error connecting to SQLite: {e}")
        return False
    
    # Connect to PostgreSQL
    try:
        db = MultiUserDatabaseManager()
        print("✅ Connected to PostgreSQL database")
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        sqlite_conn.close()
        return False
    
    # Create default user for migrated data
    try:
        default_user_id = db.create_user(
            username='migrated_user',
            email='migrated@example.com',
            password='change_this_password_123'
        )
        
        if not default_user_id:
            print("⚠️  Default user already exists, using existing user")
            # Try to authenticate to get user ID
            user = db.authenticate_user('migrated_user', 'change_this_password_123')
            if user:
                default_user_id = user['id']
            else:
                print("❌ Could not create or find default user")
                return False
        
        print(f"✅ Default user created/found: {default_user_id}")
    except Exception as e:
        print(f"❌ Error creating default user: {e}")
        return False
    
    # Migrate conversations
    try:
        cursor.execute('SELECT * FROM conversations WHERE is_deleted = FALSE OR is_deleted IS NULL')
        conversations = cursor.fetchall()
        print(f"📁 Found {len(conversations)} conversations to migrate")
        
        migrated_conversations = 0
        for conv in conversations:
            try:
                db.create_conversation(
                    user_id=default_user_id,
                    conversation_id=conv['id'],
                    title=conv['title'] or 'Migrated Conversation'
                )
                migrated_conversations += 1
            except Exception as e:
                print(f"⚠️  Warning: Could not migrate conversation {conv['id']}: {e}")
        
        print(f"✅ Migrated {migrated_conversations} conversations")
    except Exception as e:
        print(f"❌ Error migrating conversations: {e}")
        return False
    
    # Migrate messages
    try:
        cursor.execute('SELECT * FROM messages ORDER BY conversation_id, message_order')
        messages = cursor.fetchall()
        print(f"💬 Found {len(messages)} messages to migrate")
        
        migrated_messages = 0
        for msg in messages:
            try:
                metadata = {}
                if msg['metadata']:
                    try:
                        metadata = json.loads(msg['metadata'])
                    except:
                        metadata = {'original_metadata': msg['metadata']}
                
                db.save_message(
                    user_id=default_user_id,
                    conversation_id=msg['conversation_id'],
                    message_id=msg['id'],
                    role=msg['role'],
                    content=msg['content'],
                    tokens_used=msg['tokens_used'] or 0,
                    metadata=metadata
                )
                migrated_messages += 1
            except Exception as e:
                print(f"⚠️  Warning: Could not migrate message {msg['id']}: {e}")
        
        print(f"✅ Migrated {migrated_messages} messages")
    except Exception as e:
        print(f"❌ Error migrating messages: {e}")
        return False
    
    sqlite_conn.close()
    
    print("\n🎉 Migration completed successfully!")
    print(f"📊 Summary:")
    print(f"   - Default user ID: {default_user_id}")
    print(f"   - Conversations migrated: {migrated_conversations}")
    print(f"   - Messages migrated: {migrated_messages}")
    print(f"\n🔐 Default login credentials:")
    print(f"   Username: migrated_user")
    print(f"   Password: change_this_password_123")
    print(f"   ⚠️  IMPORTANT: Change this password after first login!")
    
    return True

def cleanup_old_files():
    """Remove old SQLite database files"""
    files_to_remove = [
        'chatgpt_conversations.db',
        'chatgpt_conversations.db-journal',
        'database.py'  # Old single-user database manager
    ]
    
    removed_files = []
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"🗑️  Removed: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not remove {file_path}: {e}")
    
    if removed_files:
        print(f"✅ Cleaned up {len(removed_files)} old database files")
    else:
        print("ℹ️  No old database files to clean up")

def main():
    """Main migration process"""
    print("🔄 ChatGPT App: SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Step 1: Backup existing data
    print("\n📋 Step 1: Backing up existing data...")
    backup_sqlite_data()
    
    # Step 2: Check PostgreSQL connection
    print("\n📋 Step 2: Testing PostgreSQL connection...")
    if not check_postgresql_connection():
        print("\n❌ Migration aborted: PostgreSQL connection failed")
        print("Please set up PostgreSQL and try again")
        return False
    
    # Step 3: Migrate data
    print("\n📋 Step 3: Migrating data...")
    if not migrate_data():
        print("\n❌ Migration failed")
        return False
    
    # Step 4: Clean up old files
    print("\n📋 Step 4: Cleaning up old database files...")
    cleanup_old_files()
    
    print("\n" + "=" * 50)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print("📝 Next steps:")
    print("1. Update your app.py to use database_multiuser.py")
    print("2. Add user authentication routes")
    print("3. Test the multi-user functionality")
    print("4. Change the default user password")
    
    return True

if __name__ == "__main__":
    main()
