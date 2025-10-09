# Migration Guide: SQLite to PostgreSQL for Multi-User Support

## 🚨 **Critical: Multi-User Database Migration Required**

Your current SQLite setup **will not work** for multiple users. Here's your migration path:

---

## 📋 **Migration Steps**

### **Step 1: Install PostgreSQL**

**Option A: Local Installation (Recommended for Development)**
1. Download PostgreSQL: https://www.postgresql.org/download/
2. Install with default settings
3. Remember the password for 'postgres' user
4. Default port: 5432

**Option B: Docker (Quick Setup)**
```bash
docker run --name chatgpt-postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  -d postgres:15
```

### **Step 2: Install Python Dependencies**

```bash
# In your ChatGPTMock directory
pip install psycopg2-binary sqlalchemy flask-login flask-bcrypt cryptography
```

### **Step 3: Create Database and User**

Connect to PostgreSQL and run:
```sql
-- Create database
CREATE DATABASE chatgpt_multiuser;

-- Create user
CREATE USER chatgpt_app WITH PASSWORD 'secure_password_here';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE chatgpt_multiuser TO chatgpt_app;
```

### **Step 4: Environment Configuration**

Create `.env` file in your project:
```env
DATABASE_URL=postgresql://chatgpt_app:secure_password_here@localhost:5432/chatgpt_multiuser
SECRET_KEY=your-secret-key-for-sessions
FLASK_ENV=development
```

### **Step 5: Update Your App for Multi-User**

**A. Add User Authentication to app.py:**
```python
from flask_login import LoginManager, login_required, current_user
from database_multiuser import multi_user_db

# Add to your app initialization
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return multi_user_db.get_user_by_id(user_id)
```

**B. Add Authentication Routes:**
```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    # User registration logic

@app.route('/login', methods=['GET', 'POST'])
def login():
    # User login logic

@app.route('/logout')
@login_required
def logout():
    # User logout logic
```

**C. Update Chat Endpoint for Multi-User:**
```python
@app.route('/chat', methods=['POST'])
@login_required  # Require authentication
def chat():
    user_id = current_user.id
    # Use user_id in all database operations
```

---

## 🔄 **Data Migration from SQLite**

### **Migration Script:**

```python
import sqlite3
from database_multiuser import multi_user_db

def migrate_from_sqlite():
    """Migrate existing SQLite data to PostgreSQL"""
    
    # Connect to old SQLite database
    sqlite_conn = sqlite3.connect('chatgpt_conversations.db')
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Create default user for existing data
    default_user_id = multi_user_db.create_user(
        username='migrated_user',
        email='migrated@example.com',
        password='change_this_password'
    )
    
    if not default_user_id:
        print("Error: Could not create default user")
        return
    
    # Migrate conversations
    cursor.execute('SELECT * FROM conversations')
    for conv in cursor.fetchall():
        multi_user_db.create_conversation(
            user_id=default_user_id,
            conversation_id=conv['id'],
            title=conv['title'] or 'Migrated Conversation'
        )
    
    # Migrate messages
    cursor.execute('SELECT * FROM messages ORDER BY conversation_id, message_order')
    for msg in cursor.fetchall():
        metadata = {}
        if msg['metadata']:
            try:
                metadata = json.loads(msg['metadata'])
            except:
                pass
        
        multi_user_db.save_message(
            user_id=default_user_id,
            conversation_id=msg['conversation_id'],
            message_id=msg['id'],
            role=msg['role'],
            content=msg['content'],
            tokens_used=msg['tokens_used'] or 0,
            metadata=metadata
        )
    
    sqlite_conn.close()
    print(f"Migration complete! Default user ID: {default_user_id}")

# Run migration
if __name__ == "__main__":
    migrate_from_sqlite()
```

---

## 🎯 **Multi-User Features You'll Get**

### **✅ User Management:**
- Individual user accounts with secure authentication
- Personal conversation histories
- Encrypted API key storage per user
- User session management

### **✅ Data Isolation:**
- Each user only sees their own conversations
- Secure data separation
- No data leakage between users

### **✅ Scalability:**
- Support for thousands of concurrent users
- Connection pooling for performance
- Horizontal scaling capabilities

### **✅ Production Ready:**
- ACID transactions
- Backup and recovery
- Monitoring and logging
- High availability options

---

## 🚀 **Deployment Options for Multi-User**

### **Development:**
- Local PostgreSQL installation
- Docker container

### **Production:**
- **Heroku** (with Heroku Postgres)
- **AWS RDS** (managed PostgreSQL)
- **Google Cloud SQL**
- **DigitalOcean Managed Databases**
- **Railway** (simple deployment)

---

## ⚠️ **Important Notes**

1. **Backup First**: Export your current SQLite data before migration
2. **Test Thoroughly**: Run migration script on a copy first
3. **Security**: Use strong passwords and secure your database
4. **Environment Variables**: Never commit database credentials to git
5. **SSL**: Enable SSL for production database connections

---

## 📞 **Next Steps**

1. **Immediate**: Install PostgreSQL and dependencies
2. **Short-term**: Run the migration script to preserve existing data
3. **Development**: Add user authentication to your app
4. **Testing**: Test multi-user functionality thoroughly
5. **Production**: Deploy to a managed PostgreSQL service

**Would you like me to help you with any specific step of this migration?**
