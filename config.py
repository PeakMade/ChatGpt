"""
Configuration settings for AI BOOST Flask Application
"""
import os

# Azure Key Vault Configuration
# Update this to match your Key Vault name
KEYVAULT_NAME = os.environ.get('KEYVAULT_NAME', 'peakmade-ai-keyvault')
KEYVAULT_URL = f"https://{KEYVAULT_NAME}.vault.azure.net/"

# Secret names in Key Vault
OPENAI_SECRET_NAME = "openai-api-key"

# Application settings
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
