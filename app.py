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
from database import db_manager

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
        print(f"Using Key Vault API key (length: {len(keyvault_key)})")
        return keyvault_key
    
    # Fall back to environment variable (local development)
    env_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if env_key and env_key.startswith('sk-') and len(env_key) > 20:
        print(f"Using environment API key (length: {len(env_key)})")
        return env_key
    
    # Debug info
    print(f"No API key found:")
    print(f"  - Key Vault available: {AZURE_AVAILABLE}")
    print(f"  - Key Vault result: {bool(keyvault_key)}")
    print(f"  - Environment var exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print(f"  - Environment var value length: {len(os.environ.get('OPENAI_API_KEY', ''))}")
    
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

CRITICAL FORMATTING REQUIREMENTS - FOLLOW THESE EXACTLY:
- Always use double line breaks between paragraphs for maximum readability
- Start each major section with a clear heading using ### or **bold** formatting
- Use proper indentation and spacing for nested content
- When providing multiple steps or points, use bullet points (•) or numbered lists (1., 2., 3.)
- Add blank lines before and after all lists, code blocks, or formulas
- Break up long explanations into short, digestible paragraphs (3-4 sentences max)
- Use proper line spacing: paragraph → blank line → paragraph → blank line
- For processes or instructions, use numbered steps with descriptions
- For lists of features or benefits, use bullet points with clear spacing
- Ensure each response has excellent visual hierarchy and white space
- Use indentation for sub-points and nested information
- Always separate different topics with clear visual breaks

SPACING EXAMPLE:
### Main Topic

This is a paragraph with good spacing.

This is another paragraph after a blank line.

1. First step in a process
   - Sub-point with indentation
   - Another sub-point

2. Second step with proper spacing

• Bullet point for features
• Another bullet point
• Third bullet point

### Next Section

New content starts here with proper separation.

Please provide helpful, accurate, and up-to-date responses with excellent formatting and spacing."""

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
        
        # Get response from OpenAI using GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Latest efficient model with better performance
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

CRITICAL FORMATTING REQUIREMENTS - FOLLOW THESE EXACTLY:
- Always use double line breaks between paragraphs for maximum readability
- Start each major section with a clear heading using ### or **bold** formatting
- Use proper indentation and spacing for nested content
- When providing multiple steps or points, use bullet points (•) or numbered lists (1., 2., 3.)
- Add blank lines before and after all lists, code blocks, or formulas
- Break up long explanations into short, digestible paragraphs (3-4 sentences max)
- Use proper line spacing: paragraph → blank line → paragraph → blank line
- For processes or instructions, use numbered steps with descriptions
- For lists of features or benefits, use bullet points with clear spacing
- Ensure each response has excellent visual hierarchy and white space
- Use indentation for sub-points and nested information
- Always separate different topics with clear visual breaks

SPACING EXAMPLE:
### Main Topic

This is a paragraph with good spacing.

This is another paragraph after a blank line.

1. First step in a process
   - Sub-point with indentation
   - Another sub-point

2. Second step with proper spacing

• Bullet point for features
• Another bullet point
• Third bullet point

### Next Section

New content starts here with proper separation.

Please provide helpful, accurate, and up-to-date responses with excellent formatting and spacing."""

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
        
        # Use modern API call with GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Latest efficient model with better performance
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
    
    # Debug info (remove after testing)
    debug_info = {
        'keyvault_available': AZURE_AVAILABLE,
        'keyvault_url': config.KEYVAULT_URL,
        'env_var_exists': bool(os.environ.get('OPENAI_API_KEY')),
        'has_key': has_key
    }
    
    return jsonify({
        'has_environment_key': has_key,
        'debug': debug_info
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_api_key = data.get('api_key', '').strip()
        conversation_id = data.get('conversation_id', '').strip()
        message_id = data.get('message_id', '').strip()
        
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
        
        # Ensure we have a conversation ID
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Create conversation in database
            user_id = session.get('user_id', 'default_user')
            db_manager.create_conversation(
                conversation_id=conversation_id,
                title=user_message[:50] + '...' if len(user_message) > 50 else user_message,
                user_id=user_id
            )
        
        # Generate message ID if not provided
        if not message_id:
            message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Update session API key
        session['api_key'] = api_key
        
        # Add user message to session
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        session['messages'].append(user_msg)
        
        # Save user message to database
        db_manager.save_message(
            conversation_id=conversation_id,
            message_id=message_id,
            role="user",
            content=user_message,
            tokens_used=0,  # User messages don't use tokens
            metadata={"frontend_timestamp": datetime.now().isoformat()}
        )
        
        # Get AI response - pass API key directly
        ai_response = get_chat_response(api_key, session['messages'])
        
        # Generate AI message ID
        ai_message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Estimate tokens used
        estimated_tokens = len(ai_response.split()) * 1.3  # Rough estimation
        
        # Add AI response to session
        ai_msg = {
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        }
        session['messages'].append(ai_msg)
        
        # Save AI message to database
        db_manager.save_message(
            conversation_id=conversation_id,
            message_id=ai_message_id,
            role="assistant",
            content=ai_response,
            tokens_used=int(estimated_tokens),
            metadata={"frontend_timestamp": datetime.now().isoformat()}
        )
        
        # Save session
        session.modified = True
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'conversation_id': conversation_id,
            'user_message_id': message_id,
            'ai_message_id': ai_message_id,
            'timestamp': datetime.now().isoformat(),
            'estimated_tokens': int(estimated_tokens)
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

# ============================================================================
# THREAD MANAGEMENT API ENDPOINTS
# ============================================================================

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the user"""
    try:
        user_id = session.get('user_id', 'default_user')
        conversations = db_manager.get_conversations(user_id)
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with all messages"""
    try:
        conversation = db_manager.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': conversation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json() or {}
        user_id = session.get('user_id', 'default_user')
        title = data.get('title', 'New Conversation')
        conversation_id = data.get('conversation_id')
        
        new_conversation_id = db_manager.create_conversation(
            conversation_id=conversation_id,
            title=title,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'conversation_id': new_conversation_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    """Update conversation title"""
    try:
        data = request.get_json()
        title = data.get('title')
        
        if not title:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        success = db_manager.update_conversation_title(conversation_id, title)
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        success = db_manager.delete_conversation(conversation_id)
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages', methods=['POST'])
def save_message():
    """Save a message to the database"""
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        message_id = data.get('message_id')
        role = data.get('role')
        content = data.get('content')
        tokens_used = data.get('tokens_used', 0)
        metadata = data.get('metadata', {})
        
        if not all([conversation_id, message_id, role, content]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        success = db_manager.save_message(
            conversation_id=conversation_id,
            message_id=message_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            metadata=metadata
        )
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/search', methods=['GET'])
def search_conversations():
    """Search conversations"""
    try:
        query = request.args.get('q', '').strip()
        user_id = session.get('user_id', 'default_user')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        results = db_manager.search_conversations(query, user_id)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/stats', methods=['GET'])
def get_conversation_stats():
    """Get conversation statistics"""
    try:
        user_id = session.get('user_id', 'default_user')
        stats = db_manager.get_conversation_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>/export', methods=['GET'])
def export_conversation(conversation_id):
    """Export conversation data"""
    try:
        export_data = db_manager.export_conversation(conversation_id)
        
        if not export_data:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/import', methods=['POST'])
def import_conversation():
    """Import conversation data"""
    try:
        data = request.get_json()
        export_data = data.get('export_data')
        new_conversation_id = data.get('conversation_id')
        
        if not export_data:
            return jsonify({
                'success': False,
                'error': 'Export data is required'
            }), 400
        
        conversation_id = db_manager.import_conversation(export_data, new_conversation_id)
        
        if not conversation_id:
            return jsonify({
                'success': False,
                'error': 'Failed to import conversation'
            }), 500
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
