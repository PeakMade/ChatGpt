# PostgreSQL Setup Guide

## 🔐 Setting Up PostgreSQL Password & Database

You have **3 options** to set up PostgreSQL:

### Option 1: Use pgAdmin (Easiest) 🎯

1. **Open pgAdmin** (search for "pgAdmin" in Start menu)
2. **First time setup**: pgAdmin will ask you to create a master password
3. **Connect to server**: 
   - Right-click "Servers" → "Create" → "Server"
   - Name: "Local PostgreSQL"
   - Host: localhost
   - Port: 5432
   - Username: postgres
   - Password: (if it asks, try leaving blank or use "postgres")

4. **Create database**:
   - Right-click "Databases" → "Create" → "Database"
   - Database name: `chatgpt_multiuser`
   - Owner: postgres

5. **Create user**:
   - Right-click "Login/Group Roles" → "Create" → "Login/Group Role"
   - General tab: Name = `chatgpt_app`
   - Definition tab: Password = `secure_password_123`
   - Privileges tab: Check "Can login?" and "Create databases?"

### Option 2: Command Line (Advanced) 💻

If PostgreSQL didn't set a password during installation:

```cmd
# Try connecting without password
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres

# If that works, run these commands:
CREATE DATABASE chatgpt_multiuser;
CREATE USER chatgpt_app WITH PASSWORD 'secure_password_123';
GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;
ALTER USER chatgpt_app CREATEDB;
\q
```

### Option 3: Reset postgres password 🔄

If you need to set/reset the postgres password:

1. **Stop PostgreSQL service**:
   - Services → Find "postgresql-x64-16" → Stop

2. **Edit pg_hba.conf**:
   - File location: `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`
   - Change line: `host all all 127.0.0.1/32 md5`
   - To: `host all all 127.0.0.1/32 trust`

3. **Restart service** and connect without password

4. **Set new password**:
   ```sql
   ALTER USER postgres PASSWORD 'your_new_password';
   ```

5. **Change pg_hba.conf back** to `md5` and restart

## 🚀 After Setup

Once database is created, run:
```cmd
py migrate_database.py
```

## ❓ Need Help?

Try the simple setup script:
```cmd
setup_database_simple.bat
```
