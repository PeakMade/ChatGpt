"""
Health check endpoint for deployment platforms
"""
import requests
import sys

def health_check():
    """Simple health check function"""
    try:
        response = requests.get("http://localhost:8501/healthz")
        if response.status_code == 200:
            print("Health check passed")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)
