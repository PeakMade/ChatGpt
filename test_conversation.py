#!/usr/bin/env python3

import requests
import json

def test_conversation_loading():
    base_url = "http://127.0.0.1:5000"
    user_id = "3d261fbb-1066-4db2-8339-00c287325f6b"
    conversation_id = "conv_1757091824070_2il0terva"  # Football conversation
    
    try:
        # Test specific conversation loading
        print(f"🔍 Testing /api/conversations/{conversation_id} with user_id={user_id}...")
        response = requests.get(f"{base_url}/api/conversations/{conversation_id}?user_id={user_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                conversation = data.get('conversation')
                print(f"✅ Success! Loaded conversation: {conversation.get('title')}")
                print(f"📊 Messages: {len(conversation.get('messages', []))}")
                
                for i, msg in enumerate(conversation.get('messages', [])):
                    print(f"Message {i+1} ({msg['role']}): {msg['content'][:50]}...")
            else:
                print(f"❌ Error: {data.get('error')}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")

if __name__ == "__main__":
    test_conversation_loading()
