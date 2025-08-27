"""
Azure App Service startup script for Flask AI BOOST App
"""
import os
import sys
import subprocess

def main():
    """Main startup function for Azure App Service"""
    
    # Get the port from environment variable (set by Azure)
    port = os.environ.get('SERVER_PORT', '8000')
    
    # Start Flask app with Gunicorn
    cmd = [
        sys.executable, '-m', 'gunicorn', 
        'app_flask:app',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--timeout', '120'
    ]
    
    print(f"Starting Flask app on port {port}")
    print(f"Command: {' '.join(cmd)}")
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
