import psycopg2

def fix_permissions():
    """Fix PostgreSQL permissions for chatgpt_app user"""
    
    print("🔧 Fixing PostgreSQL permissions...")
    
    try:
        # Connect as postgres (superuser)
        conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="chatgpt_multiuser",
            user="postgres",
            password="postgres123"
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected as postgres")
        
        # Grant all necessary permissions
        permissions = [
            "GRANT ALL ON SCHEMA public TO chatgpt_app;",
            "GRANT CREATE ON SCHEMA public TO chatgpt_app;",
            "GRANT USAGE ON SCHEMA public TO chatgpt_app;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chatgpt_app;",
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO chatgpt_app;",
            "GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;",
            "ALTER USER chatgpt_app CREATEDB;"
        ]
        
        for permission in permissions:
            try:
                cursor.execute(permission)
                print(f"✅ {permission}")
            except Exception as e:
                print(f"⚠️  {permission} - {e}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Permissions fixed!")
        print("Now the app should work properly.")
        
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")

if __name__ == "__main__":
    fix_permissions()
