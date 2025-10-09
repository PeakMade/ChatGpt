from database_multiuser import MultiUserDatabaseManager
import json

db = MultiUserDatabaseManager()
print('🔍 Checking conversation metadata for thread_id storage...')

# Get your user's conversation
conversation = db.get_user_conversation('a8ba4879-922d-4d5e-805b-51bd2c334b0f', 'conv_1757357158110_ziozcds50')

if conversation and conversation.get('messages'):
    print(f'📊 Found {len(conversation["messages"])} messages')
    for i, msg in enumerate(conversation['messages'][:3]):  # Check first 3 messages
        print(f'Message {i+1}:')
        print(f'  Role: {msg["role"]}')
        print(f'  Content: {msg["content"][:50]}...')
        print(f'  Metadata: {msg.get("metadata", "None")}')
        if msg.get("metadata"):
            try:
                if isinstance(msg["metadata"], str):
                    metadata = json.loads(msg["metadata"])
                    print(f'  Parsed metadata: {metadata}')
                    if "openai_thread_id" in metadata:
                        print(f'  ✅ Thread ID found: {metadata["openai_thread_id"]}')
                    else:
                        print(f'  ❌ No thread ID in metadata')
                else:
                    print(f'  Metadata type: {type(msg["metadata"])}')
            except:
                print(f'  ❌ Could not parse metadata')
        print('---')
else:
    print('❌ No conversation found or no messages')
