#!/usr/bin/env python3
"""Test Flask app configuration endpoints"""

import requests
import json
import time

def test_flask_endpoints():
    print("Testing Flask Application with External Configuration")
    print("=" * 60)
    
    base_url = "http://localhost:5001"
    
    endpoints = [
        ("/api/settings", "Settings API"),
        ("/api/models", "Models API"),
    ]
    
    for endpoint, name in endpoints:
        try:
            print(f"\nTesting {name}: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {name} responded successfully")
                
                if endpoint == "/api/models":
                    print(f"  Current Simple Model: {data.get('current_simple_model', 'N/A')}")
                    print(f"  Current Complex Model: {data.get('current_complex_model', 'N/A')}")
                    print(f"  Config Source: {data.get('config_source', 'N/A')}")
                    print(f"  Intelligent Selection: {data.get('intelligent_selection_enabled', 'N/A')}")
                    
                elif endpoint == "/api/settings":
                    print(f"  Model: {data.get('model', 'N/A')}")
                    print(f"  Temperature: {data.get('temperature', 'N/A')}")
                    print(f"  Max Tokens: {data.get('max_tokens', 'N/A')}")
                    print(f"  Config Source: {data.get('config_source', 'N/A')}")
                    
            else:
                print(f"✗ {name} failed with status {response.status_code}")
                print(f"  Response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ {name} - Connection failed (is Flask app running?)")
        except requests.exceptions.Timeout:
            print(f"✗ {name} - Request timed out")
        except Exception as e:
            print(f"✗ {name} - Error: {e}")
    
    print(f"\nFlask Configuration Test Complete")

if __name__ == "__main__":
    test_flask_endpoints()