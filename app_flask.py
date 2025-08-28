"""
AI BOOST - Flask Application
A modern, responsive web application that replicates ChatGPT functionality using Flask
"""

from flask import Flask, render_template, request, jsonify, session
import openai
from datetime import datetime
import uuid
import os
from typing import List, Dict, Any
import PyPDF2
import io
import json

# Azure Key Vault imports
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

# Configuration
import config

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading
    pass

app = Flask(__name__)
# Use a consistent secret key for development, secure random for production
app.secret_key = config.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

def get_api_key_from_keyvault():
    """Get OpenAI API key from Azure Key Vault"""
    if not AZURE_AVAILABLE:
        return None
    
    try:
        # Use managed identity for authentication
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=config.KEYVAULT_URL, credential=credential)
        
        # Retrieve the secret
        secret = client.get_secret(config.OPENAI_SECRET_NAME)
        return secret.value
    except Exception as e:
        # Key Vault not available or configured, fall back to environment variables
        return None

def get_api_key():
    """Get API key from Key Vault, environment variables, or return None for user input"""
    # Try Azure Key Vault first (production)
    keyvault_key = get_api_key_from_keyvault()
    if keyvault_key and keyvault_key.startswith('sk-') and len(keyvault_key) > 20:
        return keyvault_key
    
    # Fall back to environment variable (local development)
    env_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if env_key and env_key.startswith('sk-') and len(env_key) > 20:
        return env_key
    
    # No valid key found, require user input
    return None

def get_openai_client(api_key):
    """Initialize OpenAI client with API key"""
    if not api_key:
        return None
    try:
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        return None

def get_chat_response(api_key, messages, uploaded_content=""):
    """Get response from OpenAI API"""
    if not api_key:
        return "Error: No OpenAI API key provided."
        
    try:
        # Clean the API key of any whitespace
        api_key = api_key.strip()
        try:
            # Method 1: Basic client creation
            client = openai.OpenAI(api_key=api_key)
        except Exception:
            try:
                # Method 2: Set API key globally (fallback for older versions)
                openai.api_key = api_key
                client = openai.OpenAI()
            except Exception:
                # Method 3: Use simplified approach
                return get_chat_response_legacy(api_key, messages, uploaded_content)
        
        # Prepare messages for OpenAI
        openai_messages = []
        
        # Add system prompt with 2025 knowledge context
        system_prompt = """You are AI BOOST, an advanced AI assistant with knowledge updated through 2025. 
        
Key information about your knowledge:
- Current date: August 27, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

Please provide helpful, accurate, and up-to-date responses based on your 2025 knowledge base."""

        openai_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions."
            })
        
        # Add conversation history
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Get response from OpenAI using GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Reliable model that works with all API keys
            messages=openai_messages,
            max_tokens=1500,  # Increased for more detailed responses
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except openai.AuthenticationError as e:
        return f"Error: Authentication failed - {str(e)}. Please verify your OpenAI API key is correct and active."
    except openai.RateLimitError:
        return "Error: Rate limit exceeded. Please try again later."
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'billing' in error_msg:
            return "Error: Insufficient quota. Please check your OpenAI account billing."
        elif 'authentication' in error_msg or 'api key' in error_msg:
            return f"Error: Authentication failed - {str(e)}. Please verify your OpenAI API key is correct and active."
        else:
            return f"Error: {str(e)}"

def get_chat_response_legacy(api_key, messages, uploaded_content=""):
    """Simplified OpenAI API approach"""
    try:
        # Create client with explicit API key
        client = openai.OpenAI(api_key=api_key)
        # Prepare messages for OpenAI
        openai_messages = []
        
        # Add system prompt with 2025 knowledge context
        system_prompt = """You are AI BOOST, an advanced AI assistant with knowledge updated through 2025. 
        
Key information about your knowledge:
- Current date: August 27, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

Please provide helpful, accurate, and up-to-date responses based on your 2025 knowledge base."""

        openai_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions."
            })
        
        # Add conversation history
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Use modern API call with GPT-3.5-turbo
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Reliable model that works with all API keys
            messages=openai_messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error (fallback): {str(e)}"

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

@app.route('/')
def index():
    """Main page"""
    # Initialize session variables if not present
    if 'messages' not in session:
        session['messages'] = []
    if 'api_key' not in session:
        session['api_key'] = ''
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/api-key-status')
def api_key_status():
    """Check if API key is configured in Key Vault or environment"""
    api_key = get_api_key()
    has_key = bool(api_key)
    
    return jsonify({
        'has_environment_key': has_key
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_api_key = data.get('api_key', '').strip()
        
        # Smart API key handling - check Key Vault and environment first
        secure_api_key = get_api_key()
        
        # Use secure key (Key Vault/environment) if available, otherwise user input
        if secure_api_key:
            api_key = secure_api_key
        else:
            api_key = user_api_key
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if not api_key:
            return jsonify({'error': 'Please enter your OpenAI API key'}), 400
        
        # Update session API key
        session['api_key'] = api_key
        
        # Add user message to session
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        session['messages'].append(user_msg)
        
        # Get AI response - pass API key directly
        ai_response = get_chat_response(api_key, session['messages'])
        
        # Add AI response to session
        ai_msg = {
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        session['messages'].append(ai_msg)
        
        # Save session
        session.modified = True
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Process the file based on type
        if file.filename.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file)
        elif file.filename.lower().endswith('.txt'):
            content = file.read().decode('utf-8')
        else:
            return jsonify({'error': 'Unsupported file type. Please upload PDF or TXT files.'}), 400
        
        return jsonify({
            'content': content[:1000] + ('...' if len(content) > 1000 else ''),
            'filename': file.filename,
            'full_content': content
        })
        
    except Exception as e:
        return jsonify({'error': f'File processing error: {str(e)}'}), 500

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session['messages'] = []
    session['conversation_id'] = str(uuid.uuid4())
    session.modified = True
    return jsonify({'success': True})

@app.route('/get_messages')
def get_messages():
    """Get current chat messages"""
    try:
        # Ensure session variables exist
        if 'messages' not in session:
            session['messages'] = []
        if 'api_key' not in session:
            session['api_key'] = ''
            
        return jsonify({
            'messages': session.get('messages', []),
            'api_key': session.get('api_key', '')
        })
    except Exception as e:
        return jsonify({
            'messages': [],
            'api_key': ''
        })

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
