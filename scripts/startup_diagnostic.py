#!/usr/bin/env python3
"""
Diagnostic startup script to help debug Azure deployment issues
"""
import os
import sys
import traceback
from datetime import datetime

def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def main():
    """Main diagnostic function"""
    log_message("=== AZURE DEPLOYMENT DIAGNOSTIC START ===")
    
    # Check Python version
    log_message(f"Python version: {sys.version}")
    log_message(f"Python executable: {sys.executable}")
    
    # Check working directory
    log_message(f"Current working directory: {os.getcwd()}")
    log_message(f"Files in directory: {os.listdir('.')}")
    
    # Check environment variables
    log_message("=== ENVIRONMENT VARIABLES ===")
    important_vars = ['SERVER_PORT', 'HTTP_PLATFORM_PORT', 'OPENAI_API_KEY', 'PYTHONPATH']
    for var in important_vars:
        value = os.environ.get(var, 'NOT SET')
        if var == 'OPENAI_API_KEY' and value != 'NOT SET':
            log_message(f"{var}: {'*' * 10} (length: {len(value)})")
        else:
            log_message(f"{var}: {value}")
    
    # Try importing Flask
    try:
        import flask
        log_message(f"✅ Flask version: {flask.__version__}")
    except ImportError as e:
        log_message(f"❌ Flask import failed: {e}")
        return False
    
    # Try importing OpenAI
    try:
        import openai
        log_message(f"✅ OpenAI version: {openai.__version__}")
    except ImportError as e:
        log_message(f"❌ OpenAI import failed: {e}")
        return False
    
    # Try importing app_flask
    try:
        log_message("Attempting to import app_flask...")
        import app_flask
        log_message("✅ app_flask imported successfully")
        
        # Check if app object exists
        if hasattr(app_flask, 'app'):
            log_message("✅ Flask app object found")
        else:
            log_message("❌ Flask app object not found")
            return False
            
    except Exception as e:
        log_message(f"❌ app_flask import failed: {e}")
        log_message(f"Traceback: {traceback.format_exc()}")
        return False
    
    log_message("=== DIAGNOSTIC COMPLETE - ALL CHECKS PASSED ===")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    
    # If diagnostic passes, start the actual app
    log_message("Starting actual Flask application...")
    try:
        import app_flask
        port = int(os.environ.get('SERVER_PORT', os.environ.get('HTTP_PLATFORM_PORT', '8000')))
        log_message(f"Starting Flask app on port {port}")
        app_flask.app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        log_message(f"❌ Failed to start Flask app: {e}")
        log_message(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)