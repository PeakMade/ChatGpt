#!/bin/bash
# Startup script for ChatGPT Clone

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
