# OpenAI API Integration & Database Documentation

## 📊 **Database Overview**

Your app uses **SQLite** as the primary database for persistent storage of conversations and messages.

### **Database Structure**

#### **Database Type**: SQLite
- **File**: `chatgpt_conversations.db`
- **Location**: Root directory of your application
- **Management**: Custom `DatabaseManager` class in `database.py`

#### **Tables**

**1. conversations**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,                    -- Format: conv_YYYYMMDD_HHMMSS_uniqueid
    title TEXT NOT NULL,                    -- Conversation title/topic
    preview TEXT,                          -- Preview of first user message
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT DEFAULT 'default_user',   -- User identifier
    is_deleted BOOLEAN DEFAULT FALSE       -- Soft delete flag
)
```

**2. messages**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,                    -- Format: msg_YYYYMMDD_HHMMSS_uniqueid
    conversation_id TEXT NOT NULL,          -- Foreign key to conversations
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,                  -- Message content
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER DEFAULT 0,         -- Token consumption tracking
    message_order INTEGER NOT NULL,        -- Order within conversation
    metadata TEXT DEFAULT '{}',            -- JSON metadata (model_used, etc.)
    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
)
```

#### **Indexes for Performance**
- `idx_conversations_user_id` - Fast user conversation lookup
- `idx_conversations_updated_at` - Recent conversations sorting
- `idx_messages_conversation_id` - Message retrieval by conversation
- `idx_messages_timestamp` - Chronological message ordering
- `idx_messages_order` - Message sequence within conversations

---

## 🔗 **OpenAI API Compatible Endpoints**

Your app now implements **OpenAI Conversations API** and **Chat Completions API** compatible endpoints:

### **1. Create Conversation**
```bash
POST /v1/conversations
Authorization: Bearer YOUR_OPENAI_API_KEY
Content-Type: application/json

{
    "metadata": {"topic": "demo"},
    "items": [
        {
            "type": "message",
            "role": "user",
            "content": "Hello!"
        }
    ]
}
```

**Response:**
```json
{
    "id": "conv_20250905_143022_a1b2c3d4",
    "object": "conversation",
    "created_at": 1741900000,
    "metadata": {"topic": "demo"}
}
```

### **2. Get Conversation**
```bash
GET /v1/conversations/conv_123
Authorization: Bearer YOUR_OPENAI_API_KEY
```

**Response:**
```json
{
    "id": "conv_123",
    "object": "conversation", 
    "created_at": 1741900000,
    "metadata": {"topic": "demo"}
}
```

### **3. Update Conversation**
```bash
PATCH /v1/conversations/conv_123
Authorization: Bearer YOUR_OPENAI_API_KEY
Content-Type: application/json

{
    "metadata": {"topic": "project-x"}
}
```

**Response:**
```json
{
    "id": "conv_123",
    "object": "conversation",
    "created_at": 1741900000,
    "metadata": {"topic": "project-x"}
}
```

### **4. Chat Completions**
```bash
POST /v1/chat/completions
Authorization: Bearer YOUR_OPENAI_API_KEY
Content-Type: application/json

{
    "model": "gpt-4o",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "max_tokens": 150,
    "temperature": 0.7
}
```

**Response:**
```json
{
    "id": "chatcmpl-a1b2c3d4e5",
    "object": "chat.completion",
    "created": 1741900000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 15,
        "total_tokens": 27
    }
}
```

---

## 🔧 **How Your App Uses the Database**

### **Message ID System**
- **Format**: `msg_YYYYMMDD_HHMMSS_uniqueid`
- **Purpose**: Unique identification for each message
- **Usage**: Thread management, conversation recall, message tracking

### **Conversation Management**
- **Creation**: Automatic when first message is sent
- **Persistence**: All conversations saved to SQLite
- **Recall**: Load conversations with complete message history
- **Thread Continuity**: Messages maintain order through `message_order`

### **Multi-Model Tracking**
- **Model Selection**: User preference or auto-fallback
- **Model Used**: Tracked in message metadata
- **Fallback History**: Records which model actually responded
- **Performance**: Token usage and response tracking

### **Data Flow**
1. **User Message** → Database (with message ID)
2. **AI Processing** → Multi-model fallback system
3. **AI Response** → Database (with model used)
4. **UI Update** → Real-time display with persistence
5. **Session Management** → localStorage + Database sync

---

## 🧪 **Testing Your Implementation**

Run the test script to verify OpenAI API compatibility:

```bash
python test_openai_api.py
```

This will test:
- ✅ Conversation creation
- ✅ Conversation retrieval  
- ✅ Conversation updates
- ✅ Chat completions with multi-model fallback

---

## 🔄 **Migration & Compatibility**

### **Legacy Support**
Your existing `/api/conversations` endpoints remain functional for backward compatibility.

### **New Features**
- ✅ OpenAI API format compatibility
- ✅ Bearer token authentication
- ✅ Standard error response formats
- ✅ Token usage tracking
- ✅ Multi-model integration

### **Database Schema**
No migration needed - existing data remains fully compatible.

---

## 🎯 **Key Benefits**

1. **OpenAI API Compatibility**: Drop-in replacement for OpenAI API calls
2. **Persistent Storage**: SQLite ensures conversation continuity
3. **Multi-Model Support**: Automatic fallback across 5 GPT models
4. **Message ID System**: Complete thread management
5. **Real-time Sync**: Frontend/backend synchronization
6. **Performance Optimized**: Indexed database queries
7. **Backward Compatible**: Existing functionality preserved
