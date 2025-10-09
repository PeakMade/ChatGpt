#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

def check_database():
    try:
        # Connect to database using the same connection as the app
        conn = psycopg2.connect(
            dbname="chatgpt_multiuser",
            user="chatgpt_app",
            password="secure_password_123",
            host="localhost",
            port="5432"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check all conversations
        cursor.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
        conversations = cursor.fetchall()
        
        print(f"📊 Total conversations in database: {len(conversations)}")
        
        for conv in conversations:
            print(f"  ID: {conv['id']}")
            print(f"  Title: {conv['title']}")
            print(f"  User ID: {conv['user_id']}")
            print(f"  Created: {conv['created_at']}")
            print("  ---")
        
        # Check all users
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        
        print(f"👥 Total users in database: {len(users)}")
        
        for user in users:
            print(f"  ID: {user['id']}")
            print(f"  Username: {user['username']}")
            print("  ---")
        
        # Check messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        message_count = cursor.fetchone()
        print(f"💬 Total messages in database: {message_count['count']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()
