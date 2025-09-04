"""
Database module for AI BOOST ChatGPT application
Handles persistent storage of conversations, messages, and threads
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

class DatabaseManager:
    def __init__(self, db_path: str = "chatgpt_conversations.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    preview TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT DEFAULT 'default_user',
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tokens_used INTEGER DEFAULT 0,
                    message_order INTEGER NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_order ON messages(conversation_id, message_order)')
            
            conn.commit()
    
    def create_conversation(self, conversation_id: str = None, title: str = "New Conversation", 
                          user_id: str = "default_user") -> str:
        """Create a new conversation and return its ID"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO conversations (id, title, user_id, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (conversation_id, title, user_id))
            conn.commit()
        
        return conversation_id
    
    def save_message(self, conversation_id: str, message_id: str, role: str, content: str,
                    tokens_used: int = 0, metadata: Dict = None) -> bool:
        """Save a message to the database"""
        if metadata is None:
            metadata = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get the next message order number
            cursor.execute('''
                SELECT COALESCE(MAX(message_order), 0) + 1 
                FROM messages 
                WHERE conversation_id = ?
            ''', (conversation_id,))
            message_order = cursor.fetchone()[0]
            
            # Insert the message
            cursor.execute('''
                INSERT OR REPLACE INTO messages 
                (id, conversation_id, role, content, tokens_used, message_order, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (message_id, conversation_id, role, content, tokens_used, message_order, json.dumps(metadata)))
            
            # Update conversation preview and timestamp
            if role == 'user':
                preview = content[:100] + '...' if len(content) > 100 else content
                cursor.execute('''
                    UPDATE conversations 
                    SET preview = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (preview, conversation_id))
            
            conn.commit()
        
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation with all its messages"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get conversation details
            cursor.execute('''
                SELECT * FROM conversations 
                WHERE id = ? AND is_deleted = FALSE
            ''', (conversation_id,))
            conversation = cursor.fetchone()
            
            if not conversation:
                return None
            
            # Get messages for this conversation
            cursor.execute('''
                SELECT * FROM messages 
                WHERE conversation_id = ? 
                ORDER BY message_order ASC
            ''', (conversation_id,))
            messages = cursor.fetchall()
            
            return {
                'id': conversation['id'],
                'title': conversation['title'],
                'preview': conversation['preview'],
                'created_at': conversation['created_at'],
                'updated_at': conversation['updated_at'],
                'user_id': conversation['user_id'],
                'messages': [{
                    'id': msg['id'],
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'tokens_used': msg['tokens_used'],
                    'message_order': msg['message_order'],
                    'metadata': json.loads(msg['metadata']) if msg['metadata'] else {}
                } for msg in messages]
            }
    
    def get_conversations(self, user_id: str = "default_user", limit: int = 50) -> List[Dict]:
        """Get all conversations for a user, ordered by most recent"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ? AND c.is_deleted = FALSE
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            conversations = cursor.fetchall()
            
            return [{
                'id': conv['id'],
                'title': conv['title'],
                'preview': conv['preview'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'message_count': conv['message_count']
            } for conv in conversations]
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET title = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (title, conversation_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Soft delete a conversation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (conversation_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def search_conversations(self, query: str, user_id: str = "default_user") -> List[Dict]:
        """Search conversations by title, preview, or message content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT DISTINCT c.id, c.title, c.preview, c.updated_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = ? AND c.is_deleted = FALSE
                  AND (c.title LIKE ? OR c.preview LIKE ? OR m.content LIKE ?)
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT 20
            ''', (user_id, search_term, search_term, search_term))
            
            results = cursor.fetchall()
            
            return [{
                'id': conv['id'],
                'title': conv['title'],
                'preview': conv['preview'],
                'updated_at': conv['updated_at'],
                'message_count': conv['message_count']
            } for conv in results]
    
    def get_conversation_stats(self, user_id: str = "default_user") -> Dict:
        """Get statistics about conversations and messages"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('''
                SELECT COUNT(*) FROM conversations 
                WHERE user_id = ? AND is_deleted = FALSE
            ''', (user_id,))
            total_conversations = cursor.fetchone()[0]
            
            # Total messages
            cursor.execute('''
                SELECT COUNT(*) FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = ? AND c.is_deleted = FALSE
            ''', (user_id,))
            total_messages = cursor.fetchone()[0]
            
            # Total tokens used
            cursor.execute('''
                SELECT COALESCE(SUM(tokens_used), 0) FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.user_id = ? AND c.is_deleted = FALSE
            ''', (user_id,))
            total_tokens = cursor.fetchone()[0]
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'total_tokens': total_tokens
            }
    
    def cleanup_old_conversations(self, days_old: int = 30, user_id: str = "default_user") -> int:
        """Delete conversations older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? 
                  AND datetime(updated_at) < datetime('now', '-{} days')
                  AND is_deleted = FALSE
            '''.format(days_old), (user_id,))
            conn.commit()
            
            return cursor.rowcount
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Export conversation data in a portable format"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        return {
            'export_version': '1.0',
            'export_date': datetime.now().isoformat(),
            'conversation': conversation
        }
    
    def import_conversation(self, export_data: Dict, new_conversation_id: str = None) -> Optional[str]:
        """Import a conversation from exported data"""
        if 'conversation' not in export_data:
            return None
        
        conv_data = export_data['conversation']
        conversation_id = new_conversation_id or self.create_conversation(
            title=conv_data['title'] + ' (Imported)'
        )
        
        # Import messages
        for msg in conv_data['messages']:
            self.save_message(
                conversation_id=conversation_id,
                message_id=msg['id'],
                role=msg['role'],
                content=msg['content'],
                tokens_used=msg.get('tokens_used', 0),
                metadata=msg.get('metadata', {})
            )
        
        return conversation_id

# Global database instance
db_manager = DatabaseManager()
