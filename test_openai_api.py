#!/usr/bin/env python3
"""
Test script for OpenAI API compatibility
Demonstrates how to use the new OpenAI-compatible endpoints
"""

import requests
import json
import os

# Your app's base URL (adjust if different)
BASE_URL = "http://127.0.0.1:5000"

# Your OpenAI API key (replace with your actual key)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-api-key-here')

def test_create_conversation():
    """Test creating a conversation using OpenAI Conversations API format"""
    print("🧪 Testing Conversation Creation...")
    
    url = f"{BASE_URL}/v1/conversations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "metadata": {"topic": "AI Development Demo"},
        "items": [
            {
                "type": "message",
                "role": "user",
                "content": "Hello! This is a test conversation."
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Conversation created successfully!")
        print(f"   ID: {result['id']}")
        print(f"   Created: {result['created_at']}")
        print(f"   Metadata: {result['metadata']}")
        return result['id']
    else:
        print(f"❌ Failed to create conversation: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_get_conversation(conversation_id):
    """Test getting a conversation"""
    print(f"🧪 Testing Get Conversation: {conversation_id}...")
    
    url = f"{BASE_URL}/v1/conversations/{conversation_id}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Conversation retrieved successfully!")
        print(f"   ID: {result['id']}")
        print(f"   Topic: {result['metadata']['topic']}")
        return True
    else:
        print(f"❌ Failed to get conversation: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_update_conversation(conversation_id):
    """Test updating a conversation"""
    print(f"🧪 Testing Update Conversation: {conversation_id}...")
    
    url = f"{BASE_URL}/v1/conversations/{conversation_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "metadata": {"topic": "Updated AI Project Discussion"}
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Conversation updated successfully!")
        print(f"   New topic: {result['metadata']['topic']}")
        return True
    else:
        print(f"❌ Failed to update conversation: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_chat_completions():
    """Test chat completions using OpenAI API format"""
    print("🧪 Testing Chat Completions...")
    
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "Explain what AI BOOST is in one sentence."
            }
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Chat completion successful!")
        print(f"   Model used: {result['model']}")
        print(f"   Response: {result['choices'][0]['message']['content'][:100]}...")
        print(f"   Tokens used: {result['usage']['total_tokens']}")
        return True
    else:
        print(f"❌ Failed to get chat completion: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting OpenAI API Compatibility Tests")
    print("=" * 50)
    
    # Test 1: Create conversation
    conversation_id = test_create_conversation()
    print()
    
    if conversation_id:
        # Test 2: Get conversation
        test_get_conversation(conversation_id)
        print()
        
        # Test 3: Update conversation
        test_update_conversation(conversation_id)
        print()
    
    # Test 4: Chat completions
    test_chat_completions()
    print()
    
    print("=" * 50)
    print("🏁 API Tests Complete!")

if __name__ == "__main__":
    main()
