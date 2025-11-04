import os
import sys

print("=== Azure Environment Test ===")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

# Test environment variable
api_key = os.environ.get('OPENAI_API_KEY', 'NOT_FOUND')
print(f"OPENAI_API_KEY: {'FOUND' if api_key != 'NOT_FOUND' else 'NOT_FOUND'}")
print(f"API Key length: {len(api_key) if api_key != 'NOT_FOUND' else 0}")

# Test config import
try:
    from config.config import get_openai_api_key
    test_key = get_openai_api_key()
    print(f"Config function works: {'YES' if test_key else 'NO'}")
    print(f"Config key length: {len(test_key) if test_key else 0}")
except Exception as e:
    print(f"Config import error: {e}")

print("=== Test Complete ===")