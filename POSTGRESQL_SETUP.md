# PostgreSQL Database Setup for Multi-User ChatGPT App

## Installation

### Windows (using PostgreSQL installer):
1. Download from: https://www.postgresql.org/download/windows/
2. Install PostgreSQL 15+ 
3. Remember the password you set for 'postgres' user
4. Default port: 5432

### Alternative (using Docker):
```bash
docker run --name chatgpt-postgres -e POSTGRES_PASSWORD=yourpassword -p 5432:5432 -d postgres:15
```

## Database Creation

```sql
-- Connect to PostgreSQL as postgres user
-- Create database for your app
CREATE DATABASE chatgpt_db;

-- Create app user
CREATE USER chatgpt_user WITH PASSWORD 'your_secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE chatgpt_db TO chatgpt_user;
```

## Python Dependencies

Add to requirements.txt:
```
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
alembic>=1.8.0  # For database migrations
```

Install:
```bash
pip install psycopg2-binary sqlalchemy alembic
```

## Updated Database Configuration

```python
# config.py
import os

class Config:
    # PostgreSQL connection
    DATABASE_URL = os.getenv('DATABASE_URL', 
        'postgresql://chatgpt_user:your_secure_password@localhost:5432/chatgpt_db')
    
    # For production (Heroku, AWS, etc.)
    if os.getenv('DATABASE_URL'):
        DATABASE_URL = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')
```

## Multi-User Schema Design

```sql
-- Users table (new for multi-user)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Updated conversations table
CREATE TABLE conversations (
    id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE  -- For sharing conversations
);

-- Updated messages table
CREATE TABLE messages (
    id VARCHAR(100) PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER DEFAULT 0,
    message_order INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',  -- JSONB for better performance
    user_id UUID NOT NULL REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_order ON messages(conversation_id, message_order);

-- API keys table (for OpenAI API key management per user)
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_encrypted TEXT NOT NULL,
    provider VARCHAR(50) DEFAULT 'openai',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Benefits of PostgreSQL for Your Multi-User App

### Concurrent Users:
- ✅ Multiple users can chat simultaneously
- ✅ No file locking issues
- ✅ ACID transactions ensure data consistency

### Performance:
- ✅ Connection pooling
- ✅ Optimized for concurrent reads/writes
- ✅ Efficient indexing for fast conversation loading

### Security:
- ✅ User authentication and authorization
- ✅ Row-level security (users only see their conversations)
- ✅ Encrypted API key storage

### Scalability:
- ✅ Can handle thousands of concurrent users
- ✅ Easy to add read replicas
- ✅ Horizontal scaling options

## Deployment Options

### Development:
- Local PostgreSQL installation
- Docker container

### Production:
- **Heroku Postgres** (easy, managed)
- **AWS RDS** (scalable, enterprise)
- **Google Cloud SQL** (integrated with GCP)
- **DigitalOcean Managed Databases** (cost-effective)
- **Supabase** (PostgreSQL with real-time features)
