import psycopg2
import sys

def test_postgres_connection():
    """Test PostgreSQL connection with common passwords"""
    
    passwords_to_try = [
        "postgres123",  # Our reset password
        "",             # No password
        "postgres",     # Default
        "admin"         # Common default
    ]
    
    print("🔍 Testing PostgreSQL Connection...")
    print("=" * 40)
    
    for i, password in enumerate(passwords_to_try, 1):
        try:
            print(f"Test {i}: Trying password: {'(empty)' if password == '' else password}")
            
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                database="postgres",
                user="postgres",
                password=password
            )
            
            print(f"✅ SUCCESS! Password is: {'(empty)' if password == '' else password}")
            
            # Test creating database
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'chatgpt_multiuser'")
            db_exists = cursor.fetchone()
            
            if not db_exists:
                print("Creating chatgpt_multiuser database...")
                cursor.execute("CREATE DATABASE chatgpt_multiuser")
                print("✅ Database created!")
            else:
                print("✅ Database already exists!")
            
            # Check if user exists
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'chatgpt_app'")
            user_exists = cursor.fetchone()
            
            if not user_exists:
                print("Creating chatgpt_app user...")
                cursor.execute("CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123'")
                cursor.execute("GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app")
                cursor.execute("ALTER USER chatgpt_app CREATEDB")
                print("✅ User created!")
            else:
                print("✅ User already exists!")
            
            cursor.close()
            conn.close()
            
            print("\n🎉 PostgreSQL Setup Complete!")
            print("Ready for migration!")
            return True
            
        except psycopg2.OperationalError as e:
            if "password authentication failed" in str(e):
                print(f"❌ Wrong password")
            elif "does not exist" in str(e):
                print(f"❌ Database/user issue: {e}")
            else:
                print(f"❌ Connection failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("❌ All password attempts failed")
    print("Manual setup needed")
    return False

if __name__ == "__main__":
    test_postgres_connection()
