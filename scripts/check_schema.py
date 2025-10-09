#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

def check_schema():
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname="chatgpt_multiuser",
            user="chatgpt_app",
            password="secure_password_123",
            host="localhost",
            port="5432"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check messages table schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'messages'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("📊 Messages table schema:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

if __name__ == "__main__":
    check_schema()
