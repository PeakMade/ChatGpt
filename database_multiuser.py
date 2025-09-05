"""
Multi-User Database Manager for PostgreSQL
Handles user authentication, conversations, and messages for multiple users
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib
import os
from cryptography.fernet import Fernet
import base64

class MultiUserDatabaseManager:
    def __init__(self, connection_string: str = None):
        """Initialize the multi-user database manager"""
        if connection_string is None:
            connection_string = "postgresql://chatgpt_app:secure_password_123@localhost:5432/chatgpt_multiuser"
        
        self.connection_string = connection_string
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
    
    def init_database(self):
        """Initialize the database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create API keys table (encrypted storage)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_api_keys (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL DEFAULT 'openai',
                    encrypted_api_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    UNIQUE(user_id, provider)
                )
            ''')
            
            # Create conversations table (user-specific)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(255) PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create messages table (user-specific)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id VARCHAR(255) PRIMARY KEY,
                    conversation_id VARCHAR(255) REFERENCES conversations(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    message_order INTEGER NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_order ON messages(conversation_id, message_order)')
            
            conn.commit()
    
    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys"""
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage"""
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(api_key.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        """Decrypt an API key"""
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.b64decode(encrypted_api_key.encode())
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except:
            return None
    
    # User Management
    def create_user(self, username: str, email: str, password: str) -> Optional[str]:
        """Create a new user account"""
        password_hash = self._hash_password(password)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (username, email, password_hash))
                
                user_id = cursor.fetchone()['id']
                conn.commit()
                return str(user_id)
            except psycopg2.IntegrityError:
                return None  # User already exists
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user info"""
        password_hash = self._hash_password(password)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, created_at
                FROM users 
                WHERE username = %s AND password_hash = %s AND is_active = TRUE
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            if user:
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = %s
                ''', (user['id'],))
                conn.commit()
                
                return dict(user)
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user information by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, created_at, last_login
                FROM users 
                WHERE id = %s AND is_active = TRUE
            ''', (user_id,))
            
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def ensure_user_exists(self, user_id: str) -> bool:
        """Ensure a user exists in the database, create anonymous user if needed"""
        # Check if user already exists
        if self.get_user_by_id(user_id):
            return True
        
        try:
            # Create anonymous user with the specific UUID
            with self.get_connection() as conn:
                cursor = conn.cursor()
                username = f"anonymous_{user_id[:8]}"
                email = f"anonymous_{user_id[:8]}@example.com"
                password_hash = self._hash_password("anonymous_user")
                
                cursor.execute('''
                    INSERT INTO users (id, username, email, password_hash)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                ''', (user_id, username, email, password_hash))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error ensuring user exists: {e}")
            return False
    
    # API Key Management
    def store_user_api_key(self, user_id: str, api_key: str, provider: str = 'openai'):
        """Store an encrypted API key for a user"""
        encrypted_key = self._encrypt_api_key(api_key)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_api_keys (user_id, provider, encrypted_api_key)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, provider) 
                DO UPDATE SET encrypted_api_key = EXCLUDED.encrypted_api_key,
                             last_used = CURRENT_TIMESTAMP
            ''', (user_id, provider, encrypted_key))
            conn.commit()
    
    def get_user_api_key(self, user_id: str, provider: str = 'openai') -> Optional[str]:
        """Get a decrypted API key for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT encrypted_api_key 
                FROM user_api_keys 
                WHERE user_id = %s AND provider = %s
            ''', (user_id, provider))
            
            result = cursor.fetchone()
            if result:
                decrypted_key = self._decrypt_api_key(result['encrypted_api_key'])
                
                # Update last used timestamp
                cursor.execute('''
                    UPDATE user_api_keys 
                    SET last_used = CURRENT_TIMESTAMP 
                    WHERE user_id = %s AND provider = %s
                ''', (user_id, provider))
                conn.commit()
                
                return decrypted_key
        return None
    
    # Conversation Management (User-specific)
    def create_conversation(self, user_id: str, conversation_id: str = None, 
                          title: str = "New Conversation") -> str:
        """Create a new conversation for a specific user"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (id, title, user_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    updated_at = CURRENT_TIMESTAMP
            ''', (conversation_id, title, user_id))
            conn.commit()
            
        return conversation_id
    
    def save_message(self, user_id: str, conversation_id: str, message_id: str, 
                    role: str, content: str, tokens_used: int = 0, 
                    metadata: Dict = None) -> bool:
        """Save a message to the database for a specific user"""
        if metadata is None:
            metadata = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if conversation already exists - if not, we'll need to create it
            cursor.execute('''
                SELECT id FROM conversations 
                WHERE id = %s AND user_id = %s
            ''', (conversation_id, user_id))
            
            conversation_exists = cursor.fetchone()
            
            # Only create conversation if it doesn't exist, using a meaningful title
            if not conversation_exists:
                # Always use the content for title if it's a user message
                if role == "user" and content and content.strip():
                    title = content.strip()[:50] + '...' if len(content.strip()) > 50 else content.strip()
                else:
                    # If it's an assistant message first, create with generic title
                    # We'll update it later when the user responds
                    title = "New Chat"
                
                print(f"🔍 DEBUG: Creating new conversation {conversation_id} with title: {title}")
                cursor.execute('''
                    INSERT INTO conversations (id, title, user_id)
                    VALUES (%s, %s, %s)
                ''', (conversation_id, title, user_id))
            else:
                # If conversation exists and has "New Chat" as title, update it with the first user message
                cursor.execute('''
                    SELECT title FROM conversations 
                    WHERE id = %s AND user_id = %s
                ''', (conversation_id, user_id))
                
                current_conv = cursor.fetchone()
                if (current_conv and current_conv['title'] == "New Chat" and 
                    role == "user" and content and content.strip()):
                    title = content.strip()[:50] + '...' if len(content.strip()) > 50 else content.strip()
                    cursor.execute('''
                        UPDATE conversations 
                        SET title = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    ''', (title, conversation_id, user_id))
                    print(f"🔍 DEBUG: Updated conversation {conversation_id} title to: {title}")
            
            # Get the next message order number with proper null handling
            cursor.execute('''
                SELECT COALESCE(MAX(message_order), 0) + 1 as next_order
                FROM messages 
                WHERE conversation_id = %s AND user_id = %s
            ''', (conversation_id, user_id))
            
            result = cursor.fetchone()
            # Handle None result properly - the query should always return a value due to COALESCE
            if result and result['next_order'] is not None:
                message_order = result['next_order']
            else:
                message_order = 1  # Default to 1 if somehow no result
            
            # Insert the message
            cursor.execute('''
                INSERT INTO messages 
                (id, conversation_id, role, content, tokens_used, message_order, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    tokens_used = EXCLUDED.tokens_used,
                    metadata = EXCLUDED.metadata
            ''', (message_id, conversation_id, role, content, tokens_used, message_order, json.dumps(metadata), user_id))
            
            conn.commit()
            return True
    
    def update_conversation_title_from_first_message(self, user_id: str, conversation_id: str) -> bool:
        """Update conversation title based on the first user message"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get the first user message
                cursor.execute('''
                    SELECT content FROM messages 
                    WHERE conversation_id = %s AND user_id = %s AND role = 'user'
                    ORDER BY message_order ASC 
                    LIMIT 1
                ''', (conversation_id, user_id))
                
                first_message = cursor.fetchone()
                if first_message and first_message['content']:
                    content = first_message['content']
                    # Create a meaningful title from the first message
                    title = content[:50] + '...' if len(content) > 50 else content
                    
                    # Update the conversation title
                    cursor.execute('''
                        UPDATE conversations 
                        SET title = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND user_id = %s
                    ''', (title, conversation_id, user_id))
                    
                    conn.commit()
                    print(f"✅ Updated conversation {conversation_id} title to: {title}")
                    return True
                
                return False
        except Exception as e:
            print(f"❌ Error updating conversation title: {e}")
            return False

    def fix_auto_created_conversations(self, user_id: str) -> int:
        """Fix all 'Auto-created' conversations by giving them proper titles"""
        try:
            fixed_count = 0
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find all Auto-created conversations for this user
                cursor.execute('''
                    SELECT id FROM conversations 
                    WHERE user_id = %s AND title = 'Auto-created'
                ''', (user_id,))
                
                auto_created_conversations = cursor.fetchall()
                
                for conv in auto_created_conversations:
                    conversation_id = conv['id']
                    if self.update_conversation_title_from_first_message(user_id, conversation_id):
                        fixed_count += 1
                
                print(f"✅ Fixed {fixed_count} auto-created conversations for user {user_id}")
                return fixed_count
                
        except Exception as e:
            print(f"❌ Error fixing auto-created conversations: {e}")
            return 0

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get conversations for a specific user with preview"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, fix any auto-created conversations
            self.fix_auto_created_conversations(user_id)
            
            # Get conversations with preview from first user message
            cursor.execute('''
                SELECT 
                    c.id, 
                    c.title, 
                    c.created_at, 
                    c.updated_at,
                    (
                        SELECT m.content 
                        FROM messages m 
                        WHERE m.conversation_id = c.id 
                        AND m.user_id = %s 
                        AND m.role = 'user'
                        ORDER BY m.message_order ASC 
                        LIMIT 1
                    ) as preview
                FROM conversations c
                WHERE c.user_id = %s
                ORDER BY c.updated_at DESC 
                LIMIT %s
            ''', (user_id, user_id, limit))
            
            conversations = []
            for row in cursor.fetchall():
                conv_dict = dict(row)
                # Create a preview from the first user message
                if conv_dict['preview']:
                    preview = conv_dict['preview'][:100] + '...' if len(conv_dict['preview']) > 100 else conv_dict['preview']
                    conv_dict['preview'] = preview
                else:
                    conv_dict['preview'] = "No preview available"
                
                conversations.append(conv_dict)
            
            return conversations
    
    def get_user_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation with messages for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get conversation info
            cursor.execute('''
                SELECT id, title, created_at, updated_at
                FROM conversations 
                WHERE id = %s AND user_id = %s
            ''', (conversation_id, user_id))
            
            conversation = cursor.fetchone()
            if not conversation:
                return None
            
            # Get messages
            cursor.execute('''
                SELECT id, role, content, tokens_used, metadata, timestamp as created_at
                FROM messages 
                WHERE conversation_id = %s AND user_id = %s
                ORDER BY message_order ASC
            ''', (conversation_id, user_id))
            
            messages = [dict(row) for row in cursor.fetchall()]
            
            result = dict(conversation)
            result['messages'] = messages
            return result
    
    def delete_user_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Delete a conversation and all its messages for a specific user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM conversations 
                WHERE id = %s AND user_id = %s
            ''', (conversation_id, user_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def search_user_conversations(self, user_id: str, query: str, limit: int = 20) -> List[Dict]:
        """Search conversations and messages for a specific user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = %s AND (
                    c.title ILIKE %s OR 
                    m.content ILIKE %s
                )
                ORDER BY c.updated_at DESC 
                LIMIT %s
            ''', (user_id, f'%{query}%', f'%{query}%', limit))
            
            return [dict(row) for row in cursor.fetchall()]

# Create a global instance
multi_user_db = MultiUserDatabaseManager()
