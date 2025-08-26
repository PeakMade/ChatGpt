#!/bin/bash

# Azure App Service startup script for Streamlit
echo "Starting ChatGPT Clone on Azure App Service..."

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p .streamlit

# Start the application
python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false
