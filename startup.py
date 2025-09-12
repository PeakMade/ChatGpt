"""
Azure App Service startup script for Flask AI BOOST App
Main application: app_flask.py
"""
import os
import sys
import subprocess
import time

def main():
    """Main startup function for Azure App Service"""
    
    print("=== STARTING FLASK AI BOOST APP ===", flush=True)
    print(f"Python version: {sys.version}", flush=True)
    print(f"Current directory: {os.getcwd()}", flush=True)
    
    # Get the port from environment variable (set by Azure)
    port = os.environ.get('SERVER_PORT', os.environ.get('HTTP_PLATFORM_PORT', '8000'))
    print(f"Using port: {port}", flush=True)
    
    # Check if app_flask.py exists
    if not os.path.exists('app_flask.py'):
        print("❌ ERROR: app_flask.py not found!", flush=True)
        sys.exit(1)
    
    # Start Flask app with Gunicorn
    cmd = [
        sys.executable, '-m', 'gunicorn', 
        'app_flask:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--timeout', '120',
        '--preload',
        '--log-level', 'info'
    ]
    
    print(f"Starting command: {' '.join(cmd)}", flush=True)
    
    # Add a small delay to ensure everything is ready
    time.sleep(2)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Gunicorn failed with exit code: {e.returncode}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
