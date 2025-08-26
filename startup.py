"""
Azure App Service startup script for Streamlit ChatGPT Clone
"""
import os
import sys
import subprocess

def main():
    """Main startup function for Azure App Service"""
    
    # Get the port from environment variable (set by Azure)
    port = os.environ.get('SERVER_PORT', '8000')
    
    # Set environment variables for Streamlit
    os.environ['STREAMLIT_SERVER_PORT'] = port
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Start Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--browser.gatherUsageStats', 'false'
    ]
    
    print(f"Starting Streamlit on port {port}")
    print(f"Command: {' '.join(cmd)}")
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
