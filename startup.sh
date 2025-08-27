#!/bin/bash

# Azure App Service startup script for Flask AI BOOST
echo "Starting AI BOOST Flask application..."

# Install dependencies
pip install -r requirements.txt

# Start the application with Gunicorn
exec gunicorn --bind=0.0.0.0:$PORT --timeout=600 --workers=1 app_flask:app
