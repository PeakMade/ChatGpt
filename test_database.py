import traceback
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and test the database
try:
    from database_multiuser import MultiUserDatabaseManager
    print("✅ Database import successful")
    
    # Test database connection
    db = MultiUserDatabaseManager()
    print("✅ Database manager created")
    
    # Test user ID generation
    import uuid
    user_id = str(uuid.uuid4())
    print(f"✅ Generated user_id: {user_id}")
    
    # Test conversation creation
    try:
        conversation_id = db.create_conversation(
            user_id=user_id,
            title="Test Conversation"
        )
        print(f"✅ Conversation created: {conversation_id}")
    except Exception as e:
        print(f"❌ Conversation creation failed: {e}")
        traceback.print_exc()
    
    # Test message saving
    try:
        db.save_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id="test_msg_123",
            role="user",
            content="Hello test",
            tokens_used=0,
            metadata={}
        )
        print("✅ Message saved successfully")
    except Exception as e:
        print(f"❌ Message saving failed: {e}")
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Import or setup failed: {e}")
    traceback.print_exc()
