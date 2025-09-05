#!/usr/bin/env python3
"""
Quick PostgreSQL Integration Test
Checks if PostgreSQL is installed and accessible
"""

import os
import subprocess
import sys

def check_postgresql_installation():
    print("🔍 Checking PostgreSQL Integration...")
    print("=" * 50)
    
    # Check common PostgreSQL installation paths
    possible_paths = [
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\16\bin\psql.exe",
        r"C:\PostgreSQL\16\bin\psql.exe"
    ]
    
    psql_path = None
    for path in possible_paths:
        if os.path.exists(path):
            psql_path = path
            break
    
    if psql_path:
        print(f"✅ PostgreSQL found at: {psql_path}")
        
        # Test version
        try:
            result = subprocess.run([psql_path, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Version: {result.stdout.strip()}")
            else:
                print(f"⚠️  Version check failed: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Could not check version: {e}")
    else:
        print("❌ PostgreSQL executable not found")
        print("   Please check if PostgreSQL installed correctly")
        return False
    
    # Check if Python can import psycopg2
    try:
        import psycopg2
        print("✅ Python PostgreSQL driver (psycopg2) available")
    except ImportError:
        print("❌ Python PostgreSQL driver missing")
        print("   Run: pip install psycopg2-binary")
        return False
    
    # Check Windows services
    try:
        result = subprocess.run(["sc", "query", "postgresql-x64-16"], 
                              capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            print("✅ PostgreSQL service is running")
        elif "STOPPED" in result.stdout:
            print("⚠️  PostgreSQL service is stopped")
            print("   Starting service...")
            subprocess.run(["net", "start", "postgresql-x64-16"])
        else:
            print("⚠️  PostgreSQL service status unknown")
    except Exception as e:
        print(f"⚠️  Could not check service status: {e}")
    
    # Test database connection
    try:
        connection_string = "postgresql://chatgpt_app:secure_password_123@localhost:5432/chatgpt_multiuser"
        conn = psycopg2.connect(connection_string)
        conn.close()
        print("✅ Database connection successful!")
        print("✅ PostgreSQL is fully integrated!")
        return True
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            print("⚠️  Database 'chatgpt_multiuser' not created yet")
            print("   Run: setup_database.bat")
        elif "authentication failed" in str(e):
            print("⚠️  User 'chatgpt_app' not created yet")
            print("   Run: setup_database.bat")
        else:
            print(f"⚠️  Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    success = check_postgresql_installation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 PostgreSQL is fully integrated!")
        print("✅ Ready to run migration: python migrate_database.py")
    else:
        print("⚠️  PostgreSQL needs setup")
        print("📋 Next steps:")
        print("   1. Run: setup_database.bat")
        print("   2. Then: python migrate_database.py")
    print("=" * 50)

if __name__ == "__main__":
    main()
