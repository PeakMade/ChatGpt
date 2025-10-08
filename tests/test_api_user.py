#!/usr/bin/env python3

import requests
import json

def test_api_with_user():
    base_url = "http://127.0.0.1:5000"
    user_id = "3d261fbb-1066-4db2-8339-00c287325f6b"
    
    try:
        # Test conversations endpoint with specific user
        print(f"🔍 Testing /api/conversations with user_id={user_id}...")
        response = requests.get(f"{base_url}/api/conversations?user_id={user_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('conversations', []))} conversations")
            
            # Show first conversation if any
            if data.get('conversations'):
                for i, conv in enumerate(data['conversations']):
                    print(f"Conversation {i+1}: {conv.get('title', 'No title')} - Preview: {conv.get('preview', 'No preview')}")
            else:
                print("No conversations found")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")

if __name__ == "__main__":
    test_api_with_user()
