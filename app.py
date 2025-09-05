"""
AI BOOST - Flask Application
A modern, responsive web application that replicates ChatGPT functionality using Flask
Multi-User Support with PostgreSQL
"""

from flask import Flask, render_template, request, jsonify, session
import openai
import sqlite3
from datetime import datetime
import uuid
import os
from typing import List, Dict, Any
import PyPDF2
import io
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import multi-user database, fallback to single-user if not available
try:
    from database_multiuser import MultiUserDatabaseManager
    USE_MULTIUSER = True
    print("🔄 Multi-user database manager loaded")
except ImportError as e:
    print(f"⚠️  ImportError loading multi-user database: {e}")
    from database import DatabaseManager
    USE_MULTIUSER = False
    print("⚠️  Fallback to single-user database (run migration first)")
except Exception as e:
    print(f"⚠️  Exception loading multi-user database: {e}")
    from database import DatabaseManager
    USE_MULTIUSER = False
    print("⚠️  Fallback to single-user database (connection failed)")

def get_or_create_user_id():
    """Get or create a proper UUID for the user"""
    # Allow testing with specific user ID via URL parameter
    test_user_id = request.args.get('user_id')
    if test_user_id and test_user_id in ['3d261fbb-1066-4db2-8339-00c287325f6b', 'b895109e-5ce3-494f-a3e5-c829d41f6b2c']:
        session['user_id'] = test_user_id
        print(f"🔍 DEBUG: Using test user_id from URL: {session['user_id']}")
    elif 'user_id' not in session or session['user_id'] == 'default_user':
        # Generate a proper UUID for anonymous users
        session['user_id'] = str(uuid.uuid4())
        print(f"🔍 DEBUG: Created new user_id: {session['user_id']}")
    else:
        print(f"🔍 DEBUG: Using existing user_id: {session['user_id']}")
    
    # ALWAYS ensure the user exists in the database if using multi-user mode
    if USE_MULTIUSER:
        try:
            print(f"🔍 DEBUG: Ensuring user exists in database: {session['user_id']}")
            if not db_manager.ensure_user_exists(session['user_id']):
                print(f"⚠️  Warning: Could not ensure user exists in database")
            else:
                print(f"✅ User verified/created in database")
        except Exception as e:
            print(f"❌ Error ensuring user exists: {e}")
    
    return session['user_id']

# Database manager
if USE_MULTIUSER:
    try:
        db_manager = MultiUserDatabaseManager()
        print("🔗 Multi-user database manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize multi-user database: {e}")
        from database import db_manager
        USE_MULTIUSER = False
        print("⚠️  Fallback to single-user database manager")
else:
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

def get_chat_response(api_key, messages, uploaded_content="", preferred_model=None):
    """Get response from OpenAI API with multi-model fallback"""
    if not api_key:
        return "Error: No OpenAI API key provided."
    
    # Define model hierarchy - best to fallback order
    model_hierarchy = [
        {"name": "gpt-4o", "max_tokens": 2000, "description": "Latest GPT-4 Omni"},
        {"name": "gpt-4-turbo", "max_tokens": 1500, "description": "GPT-4 Turbo"},
        {"name": "gpt-4o-mini", "max_tokens": 1500, "description": "GPT-4 Omni Mini"},
        {"name": "gpt-4", "max_tokens": 1200, "description": "GPT-4 Base"},
        {"name": "gpt-3.5-turbo", "max_tokens": 1000, "description": "GPT-3.5 Turbo Fallback"}
    ]
    
    # If preferred model specified, try it first
    if preferred_model:
        for model in model_hierarchy:
            if model["name"] == preferred_model:
                model_hierarchy.insert(0, model)
                break
        
    try:
        # Clean the API key of any whitespace
        api_key = api_key.strip()
        
        try:
            client = openai.OpenAI(api_key=api_key)
        except Exception:
            try:
                openai.api_key = api_key
                client = openai.OpenAI()
            except Exception:
                return get_chat_response_legacy(api_key, messages, uploaded_content)
        
        # Prepare messages for OpenAI
        openai_messages = []
        
        # Add system prompt with 2025 knowledge context
        system_prompt = """You are AI BOOST, an advanced AI assistant with knowledge updated through 2025. 

Key information about your knowledge:
- Current date: September 5, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

CRITICAL: If you cannot answer a question or lack sufficient information, respond with:
"I need to try a different model for this question. Let me use a more capable version to help you better."

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
        
        # Try each model in hierarchy until one succeeds
        last_error = None
        for i, model_config in enumerate(model_hierarchy):
            try:
                print(f"🤖 Trying {model_config['name']} ({model_config['description']})...")
                
                response = client.chat.completions.create(
                    model=model_config["name"],
                    messages=openai_messages,
                    max_tokens=model_config["max_tokens"],
                    temperature=0.7
                )
                
                response_content = response.choices[0].message.content
                
                # Check if model indicated it needs fallback
                if "I need to try a different model" in response_content and i < len(model_hierarchy) - 1:
                    print(f"🔄 {model_config['name']} suggested trying another model, falling back...")
                    continue
                
                # Success! Add model info to response
                model_info = f"\n\n---\n*Response generated by {model_config['name']} ({model_config['description']})*"
                
                print(f"✅ Successfully used {model_config['name']}")
                return response_content + model_info, model_config['name']
                
            except openai.RateLimitError as e:
                print(f"⚠️ Rate limit for {model_config['name']}, trying next model...")
                last_error = f"Rate limit exceeded for {model_config['name']}"
                continue
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'model' in error_msg and 'not found' in error_msg:
                    print(f"⚠️ {model_config['name']} not available, trying next model...")
                    last_error = f"{model_config['name']} not available"
                    continue
                elif 'insufficient_quota' in error_msg or 'quota' in error_msg:
                    print(f"⚠️ Quota exceeded for {model_config['name']}, trying next model...")
                    last_error = f"Quota exceeded for {model_config['name']}"
                    continue
                else:
                    print(f"❌ Error with {model_config['name']}: {str(e)}")
                    last_error = str(e)
                    continue
        
        # All models failed
        return f"Error: All available models failed. Last error: {last_error}", "error"
        
    except openai.AuthenticationError as e:
        return f"Error: Authentication failed - {str(e)}. Please verify your OpenAI API key is correct and active.", "error"
    except Exception as e:
        error_msg = str(e).lower()
        if 'quota' in error_msg or 'billing' in error_msg:
            return "Error: Insufficient quota. Please check your OpenAI account billing.", "error"
        elif 'authentication' in error_msg or 'api key' in error_msg:
            return f"Error: Authentication failed - {str(e)}. Please verify your OpenAI API key is correct and active.", "error"
        else:
            return f"Error: {str(e)}", "error"

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

# OpenAI Chat Completions API Compatible Endpoint
@app.route('/v1/chat/completions', methods=['POST'])
def openai_chat_completions():
    """
    OpenAI Chat Completions API compatible endpoint
    Accepts standard OpenAI API requests and returns compatible responses
    """
    try:
        data = request.get_json() or {}
        
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': {'message': 'Missing or invalid Authorization header', 'type': 'authentication_error'}}), 401
        
        # Extract API key from Bearer token
        api_key = auth_header.replace('Bearer ', '').strip()
        if not api_key:
            return jsonify({'error': {'message': 'Invalid API key', 'type': 'authentication_error'}}), 401
        
        # Extract request parameters
        model = data.get('model', 'gpt-4o')
        messages = data.get('messages', [])
        max_tokens = data.get('max_tokens', 2000)
        temperature = data.get('temperature', 0.7)
        
        if not messages:
            return jsonify({'error': {'message': 'Messages cannot be empty', 'type': 'invalid_request_error'}}), 400
        
        # Use our multi-model chat response function
        try:
            ai_response, model_used = get_chat_response(api_key, messages, preferred_model=model)
            
            # Generate response in OpenAI API format
            response_id = f"chatcmpl-{uuid.uuid4().hex[:10]}"
            created_timestamp = int(datetime.now().timestamp())
            
            # Calculate token usage (rough estimation)
            prompt_tokens = sum(len(msg.get('content', '').split()) for msg in messages)
            completion_tokens = len(ai_response.split())
            total_tokens = prompt_tokens + completion_tokens
            
            return jsonify({
                "id": response_id,
                "object": "chat.completion",
                "created": created_timestamp,
                "model": model_used,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ai_response
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': {
                    'message': f'API request failed: {str(e)}',
                    'type': 'api_error'
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': {
                'message': f'Request processing failed: {str(e)}',
                'type': 'invalid_request_error'
            }
        }), 400

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        print("🔍 DEBUG: Chat route called")
        data = request.get_json()
        print(f"🔍 DEBUG: Received data: {data}")
        
        user_message = data.get('message', '').strip()
        user_api_key = data.get('api_key', '').strip()
        conversation_id = data.get('conversation_id', '').strip()
        message_id = data.get('message_id', '').strip()
        preferred_model = data.get('preferred_model', None)  # New: Allow model selection
        
        print(f"🔍 DEBUG: user_message: {user_message}")
        print(f"🔍 DEBUG: conversation_id: {conversation_id}")
        
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
            user_id = get_or_create_user_id()
            if USE_MULTIUSER:
                db_manager.create_conversation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    title=user_message[:50] + '...' if len(user_message) > 50 else user_message
                )
            else:
                db_manager.create_conversation(
                    conversation_id=conversation_id,
                    title=user_message[:50] + '...' if len(user_message) > 50 else user_message
                )
        
        # Generate message ID if not provided
        if not message_id:
            message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Update session API key
        session['api_key'] = api_key
        
        # Store current conversation ID in session for consistency
        session['conversation_id'] = conversation_id
        
        # Note: We will load actual conversation history from database for AI context,
        # but keep session messages for any legacy compatibility
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        session['messages'].append(user_msg)
        
        # Save user message to database
        if USE_MULTIUSER:
            db_manager.save_message(
                user_id=get_or_create_user_id(),
                conversation_id=conversation_id,
                message_id=message_id,
                role="user",
                content=user_message,
                tokens_used=0,  # User messages don't use tokens
                metadata={"frontend_timestamp": datetime.now().isoformat()}
            )
        else:
            db_manager.save_message(
                conversation_id=conversation_id,
                message_id=message_id,
                role="user",
                content=user_message,
                tokens_used=0,  # User messages don't use tokens
                metadata={"frontend_timestamp": datetime.now().isoformat()}
            )
        
        # CRITICAL FIX: Get the actual conversation history from the database instead of session
        try:
            user_id = get_or_create_user_id()
            if USE_MULTIUSER:
                conversation = db_manager.get_user_conversation(user_id, conversation_id)
            else:
                conversation = db_manager.get_conversation(conversation_id)
            
            # Build proper message history for AI context
            conversation_messages = []
            if conversation and 'messages' in conversation:
                for msg in conversation['messages']:
                    conversation_messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            else:
                # Fallback to current message if no history found
                conversation_messages = [{
                    "role": "user",
                    "content": user_message
                }]
            
            print(f"🔍 DEBUG: Using conversation history with {len(conversation_messages)} messages for AI context")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load conversation history, using session fallback: {e}")
            # Fallback to session messages if database fails
            conversation_messages = session.get('messages', [])
            # Add current message if not in session
            conversation_messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
        
        # Get AI response with proper conversation context - pass API key directly
        ai_response, model_used = get_chat_response(api_key, conversation_messages, preferred_model=preferred_model)
        
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
        
        # Save AI message to database with model info
        if USE_MULTIUSER:
            db_manager.save_message(
                user_id=get_or_create_user_id(),
                conversation_id=conversation_id,
                message_id=ai_message_id,
                role="assistant",
                content=ai_response,
                tokens_used=int(estimated_tokens),
                metadata={
                    "frontend_timestamp": datetime.now().isoformat(),
                    "model_used": model_used,
                    "preferred_model": preferred_model
                }
            )
        else:
            db_manager.save_message(
                conversation_id=conversation_id,
                message_id=ai_message_id,
                role="assistant",
                content=ai_response,
                tokens_used=int(estimated_tokens),
                metadata={
                    "frontend_timestamp": datetime.now().isoformat(),
                    "model_used": model_used,
                    "preferred_model": preferred_model
                }
            )
        
        # Update session with AI response for legacy compatibility
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
            'conversation_id': conversation_id,
            'user_message_id': message_id,
            'ai_message_id': ai_message_id,
            'model_used': model_used,
            'timestamp': datetime.now().isoformat(),
            'estimated_tokens': int(estimated_tokens)
        })
        
    except Exception as e:
        print(f"❌ ERROR in chat route: {str(e)}")
        import traceback
        traceback.print_exc()
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
        user_id = get_or_create_user_id()
        print(f"🔍 DEBUG: Getting conversations for user_id: {user_id}")
        
        if USE_MULTIUSER:
            conversations = db_manager.get_user_conversations(user_id)
            print(f"🔍 DEBUG: Multi-user mode - found {len(conversations)} conversations")
        else:
            conversations = db_manager.get_conversations()
            print(f"🔍 DEBUG: Single-user mode - found {len(conversations)} conversations")
        
        print(f"🔍 DEBUG: Conversations: {conversations}")
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
    except Exception as e:
        print(f"❌ Error getting conversations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with all messages"""
    try:
        user_id = get_or_create_user_id()
        print(f"🔍 DEBUG: Getting conversation {conversation_id} for user_id: {user_id}")
        
        conversation = db_manager.get_user_conversation(user_id, conversation_id)
        
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
        print(f"❌ Error getting conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# OpenAI Conversations API Compatible Endpoints

@app.route('/v1/conversations', methods=['POST'])
def create_openai_conversation():
    """
    Create a new conversation using OpenAI Conversations API format
    Example Request:
    {
        "metadata": {"topic": "demo"},
        "items": [
            {
                "type": "message",
                "role": "user", 
                "content": "Hello!"
            }
        ]
    }
    """
    try:
        data = request.get_json() or {}
        
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        # Extract API key from Bearer token
        api_key = auth_header.replace('Bearer ', '').strip()
        if not api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Generate conversation ID
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Extract metadata
        metadata = data.get('metadata', {})
        topic = metadata.get('topic', 'New Conversation')
        
        # Create conversation in database
        user_id = get_or_create_user_id()
        if USE_MULTIUSER:
            db_manager.create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                title=topic
            )
        else:
            db_manager.create_conversation(
                conversation_id=conversation_id,
                title=topic
            )
        
        # Process initial items (messages) if provided
        items = data.get('items', [])
        for item in items:
            if item.get('type') == 'message':
                message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                role = item.get('role', 'user')
                content = item.get('content', '')
                
                # Save message to database
                if USE_MULTIUSER:
                    db_manager.save_message(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        message_id=message_id,
                        role=role,
                        content=content,
                        tokens_used=0,
                        metadata={"api_key_used": True, "openai_api_format": True}
                    )
                else:
                    db_manager.save_message(
                        conversation_id=conversation_id,
                        message_id=message_id,
                        role=role,
                        content=content,
                        tokens_used=0,
                        metadata={"api_key_used": True, "openai_api_format": True}
                    )
        
        # Return OpenAI API format response
        return jsonify({
            "id": conversation_id,
            "object": "conversation",
            "created_at": int(datetime.now().timestamp()),
            "metadata": metadata
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create conversation: {str(e)}'}), 500

@app.route('/v1/conversations/<conversation_id>', methods=['GET'])
def get_openai_conversation(conversation_id):
    """
    Get conversation details using OpenAI Conversations API format
    """
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        # Get conversation from database
        conversation = db_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Parse created_at timestamp
        try:
            created_at = int(datetime.fromisoformat(conversation['created_at'].replace('Z', '+00:00')).timestamp())
        except:
            created_at = int(datetime.now().timestamp())
        
        # Extract metadata from conversation title or create default
        metadata = {"topic": conversation['title']}
        
        # Return OpenAI API format response
        return jsonify({
            "id": conversation['id'],
            "object": "conversation",
            "created_at": created_at,
            "metadata": metadata
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get conversation: {str(e)}'}), 500

@app.route('/v1/conversations/<conversation_id>', methods=['PATCH'])
def update_openai_conversation(conversation_id):
    """
    Update conversation using OpenAI Conversations API format
    Example Request:
    {
        "metadata": {"topic": "project-x"}
    }
    """
    try:
        # Get authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        data = request.get_json() or {}
        metadata = data.get('metadata', {})
        
        # Check if conversation exists
        conversation = db_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Update conversation title from metadata topic
        new_title = metadata.get('topic', conversation['title'])
        
        # Update in database
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE conversations 
                SET title = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_title, conversation_id))
            conn.commit()
        
        # Parse created_at timestamp
        try:
            created_at = int(datetime.fromisoformat(conversation['created_at'].replace('Z', '+00:00')).timestamp())
        except:
            created_at = int(datetime.now().timestamp())
        
        # Return OpenAI API format response
        return jsonify({
            "id": conversation_id,
            "object": "conversation",
            "created_at": created_at,
            "metadata": metadata
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update conversation: {str(e)}'}), 500

# Keep existing API endpoints for backward compatibility
@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation (legacy format)"""
    try:
        data = request.get_json() or {}
        user_id = get_or_create_user_id()
        title = data.get('title', 'New Conversation')
        conversation_id = data.get('conversation_id')
        
        if USE_MULTIUSER:
            new_conversation_id = db_manager.create_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                title=title
            )
        else:
            new_conversation_id = db_manager.create_conversation(
                conversation_id=conversation_id,
                title=title
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
        user_id = get_or_create_user_id()
        print(f"🔍 DEBUG: Deleting conversation {conversation_id} for user_id: {user_id}")
        
        success = db_manager.delete_user_conversation(user_id, conversation_id)
        
        return jsonify({
            'success': success
        })
    except Exception as e:
        print(f"❌ Error deleting conversation {conversation_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages', methods=['POST'])
def save_message():
    """Save a message to the database"""
    try:
        # Get user_id from session for multi-user support
        user_id = get_or_create_user_id()
        
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
        
        if USE_MULTIUSER:
            success = db_manager.save_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=message_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
                metadata=metadata
            )
        else:
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
        user_id = get_or_create_user_id()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        if USE_MULTIUSER:
            results = db_manager.search_user_conversations(user_id, query)
        else:
            results = db_manager.search_conversations(query)
        
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
        user_id = get_or_create_user_id()
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
