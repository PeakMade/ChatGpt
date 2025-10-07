"""
Configuration settings for AI BOOST Flask Application
"""
import os
import configparser
from pathlib import Path

# Azure Key Vault Configuration
# Update this to match your Key Vault name
KEYVAULT_NAME = os.environ.get('KEYVAULT_NAME', 'peakmade-ai-keyvault')
KEYVAULT_URL = f"https://{KEYVAULT_NAME}.vault.azure.net/"

# Secret names in Key Vault
OPENAI_SECRET_NAME = "openai-api-key"

# Application settings
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-12345')

# ============================================================================
# EXTERNAL MODEL CONFIGURATION LOADER (INI FORMAT)
# ============================================================================

def load_model_config():
    """Load model configuration from external INI file"""
    config_file = Path(__file__).parent / 'model_config.ini'
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        return config
    except FileNotFoundError:
        print(f"⚠️ Warning: {config_file} not found. Creating default configuration...")
        create_default_config(config_file)
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        return config
    except Exception as e:
        print(f"❌ Error parsing {config_file}: {e}")
        print("Using fallback default configuration...")
        return get_fallback_config()

def create_default_config(config_file):
    """Create default model configuration INI file"""
    config = configparser.ConfigParser()
    
    # Add sections and default values
    config.add_section('models')
    config.set('models', 'simple_model', 'gpt-4o-mini')
    config.set('models', 'complex_model', 'gpt-4o')
    config.set('models', 'web_search_model', 'gpt-4o')
    config.set('models', 'fallback_model', 'gpt-4')
    
    config.add_section('settings')
    config.set('settings', 'max_tokens', '350')
    config.set('settings', 'temperature', '0.2')
    config.set('settings', 'enable_intelligent_model_selection', 'true')
    config.set('settings', 'complexity_threshold', '150')
    
    config.add_section('api_keys')
    config.set('api_keys', 'openai_api_key', 'your-api-key-here')
    
    config.add_section('model_descriptions')
    config.set('model_descriptions', 'simple_description', 'Cost-effective model for basic queries')
    config.set('model_descriptions', 'complex_description', 'Advanced model for complex analysis')
    config.set('model_descriptions', 'web_search_description', 'Model with web search capabilities')
    config.set('model_descriptions', 'fallback_description', 'Compatibility fallback model')
    
    config.add_section('complex_keywords')
    config.set('complex_keywords', 'high_complex', 'analyze, analysis, compare, comparison, evaluate, assessment, research, investigate, examine, study, review, critique, strategy, plan, design, architect, structure, framework')
    
    config.add_section('web_search_keywords')
    config.set('web_search_keywords', 'current_info', 'current, latest, recent, today, now, this week, this month, this year, up to date, breaking, news, 2025, market trends, current prices, recent data, latest stats')
    
    with open(config_file, 'w', encoding='utf-8') as f:
        config.write(f)
    print(f"✅ Created default configuration: {config_file}")

def get_fallback_config():
    """Fallback configuration if file loading fails"""
    config = configparser.ConfigParser()
    
    config.add_section('models')
    config.set('models', 'simple_model', 'gpt-4o-mini')
    config.set('models', 'complex_model', 'gpt-4o')
    config.set('models', 'web_search_model', 'gpt-4o')
    config.set('models', 'fallback_model', 'gpt-4')
    
    config.add_section('settings')
    config.set('settings', 'max_tokens', '350')
    config.set('settings', 'temperature', '0.2')
    config.set('settings', 'enable_intelligent_model_selection', 'true')
    config.set('settings', 'complexity_threshold', '150')
    
    return config

# Load configuration at module import
_MODEL_CONFIG = load_model_config()

# ============================================================================
# CONFIGURATION ACCESS FUNCTIONS (INI FORMAT)
# ============================================================================

def get_model_for_task(task_type):
    """Get the appropriate model for a specific task type"""
    model_map = {
        'simple': 'simple_model',
        'complex': 'complex_model', 
        'web_search': 'web_search_model',
        'fallback': 'fallback_model'
    }
    key = model_map.get(task_type, 'fallback_model')
    return _MODEL_CONFIG.get('models', key, fallback='gpt-4o-mini')

def get_model_description(model_type):
    """Get description for a model type"""
    desc_map = {
        'simple': 'simple_description',
        'complex': 'complex_description',
        'web_search': 'web_search_description', 
        'fallback': 'fallback_description'
    }
    key = desc_map.get(model_type, 'simple_description')
    return _MODEL_CONFIG.get('model_descriptions', key, fallback='General purpose AI model')

def is_intelligent_selection_enabled():
    """Check if intelligent model selection is enabled"""
    return _MODEL_CONFIG.getboolean('settings', 'enable_intelligent_model_selection', fallback=True)

def get_complexity_threshold():
    """Get the complexity threshold for model selection"""
    return _MODEL_CONFIG.getint('settings', 'complexity_threshold', fallback=150)

def get_max_tokens():
    """Get the maximum tokens setting"""
    return _MODEL_CONFIG.getint('settings', 'max_tokens', fallback=350)

def get_temperature():
    """Get the temperature setting"""
    return _MODEL_CONFIG.getfloat('settings', 'temperature', fallback=0.2)

def get_complex_keywords():
    """Get complex query detection keywords"""
    keywords = []
    if _MODEL_CONFIG.has_section('complex_keywords'):
        for key in _MODEL_CONFIG['complex_keywords']:
            keyword_string = _MODEL_CONFIG.get('complex_keywords', key, fallback='')
            keywords.extend([kw.strip() for kw in keyword_string.split(',') if kw.strip()])
    return keywords

def get_web_search_keywords():
    """Get web search detection keywords"""
    keywords = []
    if _MODEL_CONFIG.has_section('web_search_keywords'):
        for key in _MODEL_CONFIG['web_search_keywords']:
            keyword_string = _MODEL_CONFIG.get('web_search_keywords', key, fallback='')
            keywords.extend([kw.strip() for kw in keyword_string.split(',') if kw.strip()])
    return keywords

def get_all_models():
    """Get all configured models"""
    if _MODEL_CONFIG.has_section('models'):
        return dict(_MODEL_CONFIG['models'])
    return {}

def get_all_settings():
    """Get all settings"""
    if _MODEL_CONFIG.has_section('settings'):
        return dict(_MODEL_CONFIG['settings'])
    return {}

def get_openai_api_key():
    """Get OpenAI API key from configuration"""
    if _MODEL_CONFIG.has_section('api_keys'):
        api_key = _MODEL_CONFIG.get('api_keys', 'openai_api_key', fallback='')
        if api_key and api_key != 'your-api-key-here':
            return api_key
    
    # Fallback to environment variable
    return os.environ.get('OPENAI_API_KEY', '')

def reload_config():
    """Reload configuration from file (useful for development)"""
    global _MODEL_CONFIG
    _MODEL_CONFIG = load_model_config()
    return _MODEL_CONFIG
