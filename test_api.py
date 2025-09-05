#!/usr/bin/env python3

import requests
import json

def test_api():
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Test conversations endpoint
        print("🔍 Testing /api/conversations...")
        response = requests.get(f"{base_url}/api/conversations")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('conversations', []))} conversations")
            
            # Show first conversation if any
            if data.get('conversations'):
                conv = data['conversations'][0]
                print(f"First conversation: {conv.get('title', 'No title')} - {conv.get('preview', 'No preview')}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")

if __name__ == "__main__":
    test_api()
