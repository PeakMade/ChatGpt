"""
AI BOOST - Flask Application
A modern, responsive web application that replicates ChatGPT functionality using Flask
"""

# Internal note: App running optimally - Sept 2025

from flask import Flask, render_template, request, jsonify, session
import openai
from datetime import datetime
import uuid
import os
import time
from typing import List, Dict, Any
import PyPDF2
import io
import json

# Removed Azure Key Vault integration - using environment variables instead

# Import OpenAI Assistant Manager for thread-based conversations
try:
    from openai_assistant_manager import OpenAIAssistantManager
    ASSISTANT_MANAGER_AVAILABLE = True
    print("✅ OpenAI Assistant Manager imported successfully")
except ImportError as e:
    ASSISTANT_MANAGER_AVAILABLE = False
    print(f"⚠️ OpenAI Assistant Manager not available: {e}")

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
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 365  # 1 year

@app.before_request
def make_session_permanent():
    """Make all sessions permanent to extend conversation persistence"""
    session.permanent = True

def get_api_key():
    """Get API key from environment variables or return None for user input"""
    # Try environment variable first (local development and production)
    env_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if env_key and env_key.startswith('sk-') and len(env_key) > 20:
        print(f"Using environment API key (length: {len(env_key)})")
        return env_key
    
    # Debug info
    print(f"No API key found in environment variables")
    print(f"  - Environment var exists: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print(f"  - Environment var value length: {len(os.environ.get('OPENAI_API_KEY', ''))}")
    
    # No valid key found, require user input
    return None

def get_or_create_user_id():
    """Get or create a unique user ID for session management"""
    # Check for test user_id in URL (for debugging/testing)
    test_user_id = request.args.get('user_id')
    if test_user_id and test_user_id in ['3d261fbb-1066-4db2-8339-00c287325f6b', 'b895109e-5ce3-494f-a3e5-c829d41f6b2c']:
        session['user_id'] = test_user_id
        print(f"🔍 DEBUG: Using test user_id from URL: {session['user_id']}")
    elif 'user_id' not in session or session['user_id'] == 'default_user' or not session['user_id']:
        # Generate new user ID
        session['user_id'] = str(uuid.uuid4())
        print(f"🆕 Generated new user_id: {session['user_id']}")
    else:
        print(f"🔍 DEBUG: Using existing user_id: {session['user_id']}")
    
    return session['user_id']

def get_or_create_assistant_manager(api_key):
    """Get or create OpenAI Assistant Manager for thread-based conversations"""
    if not ASSISTANT_MANAGER_AVAILABLE:
        raise Exception("OpenAI Assistant Manager not available")
    
    if not api_key:
        raise Exception("API key required for Assistant Manager")
    
    # Create a new assistant manager instance each time with the provided API key
    # (Don't store in session as it contains the API key)
    try:
        assistant_manager = OpenAIAssistantManager(api_key)
        print("🤖 Created new OpenAI Assistant Manager")
        return assistant_manager
    except Exception as e:
        print(f"❌ Failed to create assistant manager: {e}")
        raise

def get_openai_client(api_key):
    """Initialize OpenAI client with API key"""
    if not api_key:
        return None
    try:
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        return None

def get_chat_response_with_conversation(api_key, conversation_messages, uploaded_content=""):
    """Get response from OpenAI API with full conversation context"""
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
                return get_chat_response_legacy(api_key, conversation_messages, uploaded_content)
        
        # Prepare messages for OpenAI
        openai_messages = []
        
        # Add system prompt with 2025 knowledge context
        system_prompt = """You are AI BOOST, an advanced AI assistant with knowledge updated through 2025. 
        
Key information about your knowledge:
- Current date: September 17, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

CRITICAL FORMATTING REQUIREMENTS - FOLLOW THESE EXACTLY:
- limit the response to no more than 300 words
- Always use double line breaks between paragraphs for maximum readability
- Start each major section with a clear heading using ### or **bold** formatting
- Use proper indentation and spacing for nested content
- When providing multiple steps or points, use bullet points (•) or numbered lists (1., 2., 3.)
- Add blank lines before and after all lists, code blocks, or formulas
- Break up long explanations into short, digestible paragraphs (1-2 sentences max)
- Use proper line spacing: paragraph → blank line → paragraph → blank line
- For processes or instructions, use numbered steps with descriptions
- For lists of features or benefits, use bullet points with clear spacing
- Ensure each response has excellent visual hierarchy and white space
- Use indentation for sub-points and nested information
- Always separate different topics with clear visual breaks

CONVERSATION CONTEXT:
You can refer back to previous messages in this conversation. Use the conversation history to provide contextual and relevant responses that build upon earlier exchanges."""

        openai_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions. Respond in 300 words or less."
            })
        
        # Add conversation history (only user and assistant messages)
        for msg in conversation_messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Get response from OpenAI using GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Latest efficient model with better performance
            messages=openai_messages,
            max_tokens=300,  # Increased for more detailed responses
            temperature=0.2
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
- Current date: September 17, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

CRITICAL FORMATTING REQUIREMENTS - FOLLOW THESE EXACTLY:
- limit the response to no more than 300 words
- Always use double line breaks between paragraphs for maximum readability
- Start each major section with a clear heading using ### or **bold** formatting
- Use proper indentation and spacing for nested content
- When providing multiple steps or points, use bullet points (•) or numbered lists (1., 2., 3.)
- Add blank lines before and after all lists, code blocks, or formulas
- Break up long explanations into short, digestible paragraphs (1-2 sentences max)
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
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions. Respond in 300 words or less."
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
            max_tokens=300,  # Increased for more detailed responses
            temperature=0.2
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
- Current date: September 17, 2025
- You have access to information and events through 2025
- You can discuss recent developments, technologies, and current events
- When discussing dates or timelines, remember it's currently 2025

CRITICAL FORMATTING REQUIREMENTS - FOLLOW THESE EXACTLY:
- limit the response to no more than 300 words
- Always use double line breaks between paragraphs for maximum readability
- Start each major section with a clear heading using ### or **bold** formatting
- Use proper indentation and spacing for nested content
- When providing multiple steps or points, use bullet points (•) or numbered lists (1., 2., 3.)
- Add blank lines before and after all lists, code blocks, or formulas
- Break up long explanations into short, digestible paragraphs (1-2 sentences max)
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
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions. Respond in 300 words or less."
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
            max_tokens=300,
            temperature=0.2
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
    """Check if API key is configured in environment variables"""
    api_key = get_api_key()
    has_key = bool(api_key)
    
    # Debug info (remove after testing)
    debug_info = {
        'env_var_exists': bool(os.environ.get('OPENAI_API_KEY')),
        'has_key': has_key
    }
    
    return jsonify({
        'has_environment_key': has_key,
        'debug': debug_info
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with conversation callbacks using thread_id and user_id"""
    try:
        data = request.get_json()
        print(f"🔍 DEBUG: Received data: {data}")
        
        user_message = data.get('message', '').strip()
        user_api_key = data.get('api_key', '').strip()
        thread_id = data.get('thread_id') or ''  # Handle None case
        thread_id = thread_id.strip() if thread_id else ''  # Safe strip
        conversation_id = data.get('conversation_id', session.get('conversation_id'))
        
        print(f"🔍 DEBUG: user_message: {user_message}")
        print(f"🔍 DEBUG: thread_id: {thread_id}")
        print(f"🔍 DEBUG: conversation_id: {conversation_id}")
        
        # Get or create user ID for session management
        user_id = get_or_create_user_id()
        print(f"🔍 DEBUG: user_id: {user_id}")
        
        # Smart API key handling - check environment variables first
        secure_api_key = get_api_key()
        
        # Use secure key (environment) if available, otherwise user input
        if secure_api_key:
            api_key = secure_api_key
        else:
            api_key = user_api_key
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if not api_key:
            return jsonify({'error': 'Please enter your OpenAI API key'}), 400
        
        # Get or create OpenAI Assistant Manager
        try:
            assistant_manager = get_or_create_assistant_manager(api_key)
        except Exception as e:
            print(f"❌ Failed to initialize assistant manager: {e}")
            # Fallback to basic chat completion API
            return handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id)
        
        # Use OpenAI thread_id if provided, otherwise create new thread
        if thread_id and thread_id.startswith('thread_'):
            print(f"🧵 Using existing OpenAI thread: {thread_id}")
        else:
            print("🆕 Creating new OpenAI thread")
            thread_id = None  # Will be created by assistant manager
        
        # Initialize conversation if needed (for session storage)
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            session['conversation_id'] = conversation_id
        
        # Update session API key
        session['api_key'] = api_key
        
        # Store conversation metadata in session (but messages will be in OpenAI threads)
        if 'conversations' not in session:
            session['conversations'] = {}
        
        if conversation_id not in session['conversations']:
            session['conversations'][conversation_id] = {
                'id': conversation_id,
                'thread_id': thread_id,  # Store OpenAI thread_id
                'user_id': user_id,      # Store user_id
                'created_at': datetime.now().isoformat(),
                'title': user_message[:50] + ('...' if len(user_message) > 50 else ''),
                'updated_at': datetime.now().isoformat(),
                'message_count': 0
            }
        
        # Execute the optimal OpenAI chat flow with thread management
        print("🤖 Executing optimal OpenAI Assistants API flow...")
        
        try:
            # Use Assistant Manager for thread-based conversation
            result = assistant_manager.complete_chat_flow(
                user_message=user_message,
                thread_id=thread_id
            )
            
            # Extract thread_id from result
            if result and 'thread_id' in result:
                new_thread_id = result['thread_id']
                session['conversations'][conversation_id]['thread_id'] = new_thread_id
                session['conversations'][conversation_id]['updated_at'] = datetime.now().isoformat()
                session['conversations'][conversation_id]['message_count'] += 2  # user + assistant
                
                print(f"✅ Thread-based chat completed. Thread ID: {new_thread_id}")
                
                # Save session
                session.modified = True
                
                return jsonify({
                    'user_message': user_message,
                    'ai_response': result.get('response', 'No response received'),
                    'thread_id': new_thread_id,
                    'user_id': user_id,
                    'conversation_id': conversation_id,
                    'timestamp': datetime.now().isoformat(),
                    'message_ids': result.get('message_ids', {})
                })
            else:
                raise Exception("Invalid response from Assistant Manager")
                
        except Exception as e:
            print(f"❌ Thread-based chat failed: {e}")
            # Fallback to basic chat completion
            return handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id):
    """Fallback to basic chat completion when Assistant Manager fails"""
    try:
        print("🔄 Using fallback chat completion API")
        
        # Get conversation history from session
        conversation_messages = []
        conversations = session.get('conversations', {})
        print(f"🔍 DEBUG: Available conversations: {list(conversations.keys())}")
        print(f"🔍 DEBUG: Looking for conversation_id: {conversation_id}")
        
        if conversation_id and conversation_id in conversations:
            conversation = conversations[conversation_id]
            stored_messages = conversation.get('messages', [])
            print(f"🔍 DEBUG: Found {len(stored_messages)} stored messages")
            conversation_messages = [{"role": msg["role"], "content": msg["content"]} for msg in stored_messages if "role" in msg and "content" in msg]
        else:
            print("🔍 DEBUG: No existing conversation found, starting fresh")
        
        # Add current user message
        conversation_messages.append({"role": "user", "content": user_message})
        print(f"🔍 DEBUG: Total messages for API call: {len(conversation_messages)}")
        
        # Get AI response using basic completion
        ai_response = get_chat_response_with_conversation(api_key, conversation_messages)
        
        # Store messages in session
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        ai_msg = {
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        # Update session
        if 'conversations' not in session:
            session['conversations'] = {}
        if conversation_id not in session['conversations']:
            session['conversations'][conversation_id] = {
                'id': conversation_id,
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'title': user_message[:50] + ('...' if len(user_message) > 50 else ''),
                'updated_at': datetime.now().isoformat()
            }
        
        session['conversations'][conversation_id]['messages'].extend([user_msg, ai_msg])
        session['conversations'][conversation_id]['updated_at'] = datetime.now().isoformat()
        session.modified = True
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conversation_id,
            'user_id': user_id,
            'message_ids': {
                'user': user_msg['id'],
                'assistant': ai_msg['id']
            },
            'fallback': True
        })
        
    except Exception as e:
        print(f"❌ Fallback chat also failed: {e}")
        return jsonify({'error': f'Chat error: {str(e)}'}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations - includes thread_id and user_id for proper callback management"""
    try:
        user_id = get_or_create_user_id()
        conversations = session.get('conversations', {})
        conversation_list = []
        
        for conv_id, conv_data in conversations.items():
            # Generate preview from messages
            preview_text = ""  # Empty by default, no "New conversation"
            messages = conv_data.get('messages', [])
            if messages:
                # Use the first user message as preview
                for msg in messages:
                    if msg.get('role') == 'user' and msg.get('content'):
                        content = msg.get('content', '').strip()
                        preview_text = content[:80] + ('...' if len(content) > 80 else '')
                        break
            
            conversation_summary = {
                'id': conv_id,
                'title': conv_data.get('title', 'Untitled Conversation'),
                'created_at': conv_data.get('created_at'),
                'updated_at': conv_data.get('updated_at'),
                'message_count': conv_data.get('message_count', len(messages)),
                'thread_id': conv_data.get('thread_id'),  # Include OpenAI thread_id
                'user_id': conv_data.get('user_id', user_id),  # Include user_id
                'last_message': messages[-1] if messages else None,
                'preview': preview_text  # Add actual preview text
            }
            conversation_list.append(conversation_summary)
        
        # Sort by updated_at (most recent first)
        conversation_list.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return jsonify({
            'conversations': conversation_list,
            'total': len(conversation_list),
            'user_id': user_id  # Include current user_id in response
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve conversations: {str(e)}'}), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation_by_id(conversation_id):
    """Get specific conversation by ID - handles both thread-based and fallback conversations"""
    try:
        user_id = get_or_create_user_id()
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation = conversations[conversation_id]
        thread_id = conversation.get('thread_id')
        
        # For now, use session-stored messages since we don't have API key access here
        # In the future, we could retrieve messages from threads if API key is available
        messages = conversation.get('messages', [])
        if thread_id:
            print(f"ℹ️ Conversation has thread ID {thread_id} but using session messages")
        
        return jsonify({
            'id': conversation_id,
            'title': conversation.get('title', 'Untitled Conversation'),
            'created_at': conversation.get('created_at'),
            'updated_at': conversation.get('updated_at'),
            'messages': messages,
            'message_count': conversation.get('message_count', len(messages)),
            'thread_id': thread_id,
            'user_id': conversation.get('user_id', user_id)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve conversation: {str(e)}'}), 500

@app.route('/api/conversations/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation - handles thread-based messages"""
    try:
        user_id = get_or_create_user_id()
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation = conversations[conversation_id]
        thread_id = conversation.get('thread_id')
        
        # Default to session-stored messages
        messages = conversation.get('messages', [])
        
        # If we have a thread_id and API key, try to get messages from OpenAI thread
        if thread_id and thread_id.startswith('thread_'):
            api_key = get_api_key()
            if api_key and ASSISTANT_MANAGER_AVAILABLE:
                try:
                    print(f"🧵 Retrieving messages from OpenAI thread: {thread_id}")
                    assistant_manager = get_or_create_assistant_manager(api_key)
                    thread_messages = assistant_manager.list_messages(thread_id)
                    
                    if thread_messages and 'messages' in thread_messages:
                        # Convert OpenAI thread messages to our format
                        formatted_messages = []
                        for msg in thread_messages['messages']:  # Messages already in chronological order (asc)
                            formatted_msg = {
                                'id': msg.get('id', str(uuid.uuid4())),
                                'role': msg.get('role', 'assistant'),
                                'content': msg.get('content', [{}])[0].get('text', {}).get('value', '') if msg.get('content') else '',
                                'timestamp': msg.get('created_at', datetime.now().isoformat()),
                                'created_at': msg.get('created_at', datetime.now().isoformat())
                            }
                            formatted_messages.append(formatted_msg)
                        
                        messages = formatted_messages
                        print(f"✅ Retrieved {len(messages)} messages from OpenAI thread")
                    else:
                        print("⚠️ No messages found in OpenAI thread, using session messages")
                        
                except Exception as e:
                    print(f"⚠️ Failed to retrieve thread messages: {e}, using session messages")
            else:
                print("ℹ️ No API key available, using session messages")
        
        return jsonify({
            'messages': messages,
            'total': len(messages),
            'conversation_id': conversation_id,
            'thread_id': thread_id,
            'user_id': conversation.get('user_id', user_id)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve messages: {str(e)}'}), 500
        
        return jsonify({
            'conversation_id': conversation_id,
            'messages': messages,
            'total': len(messages)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve messages: {str(e)}'}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json() or {}
        title = data.get('title', 'New Conversation')
        
        conversation_id = str(uuid.uuid4())
        
        if 'conversations' not in session:
            session['conversations'] = {}
        
        session['conversations'][conversation_id] = {
            'id': conversation_id,
            'title': title,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        session['conversation_id'] = conversation_id
        session.modified = True
        
        return jsonify({
            'id': conversation_id,
            'title': title,
            'created_at': session['conversations'][conversation_id]['created_at'],
            'message': 'Conversation created successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to create conversation: {str(e)}'}), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        del conversations[conversation_id]
        session['conversations'] = conversations
        
        # If this was the active conversation, clear it
        if session.get('conversation_id') == conversation_id:
            session['conversation_id'] = None
        
        session.modified = True
        
        return jsonify({'message': 'Conversation deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete conversation: {str(e)}'}), 500

@app.route('/api/conversations/search', methods=['GET'])
def search_conversations():
    """Search conversations by title or content"""
    try:
        query = request.args.get('q', '').strip().lower()
        if not query:
            return jsonify({'conversations': []})
        
        conversations = session.get('conversations', {})
        matching_conversations = []
        
        for conv_id, conversation in conversations.items():
            # Search in title
            title = conversation.get('title', '').lower()
            if query in title:
                matching_conversations.append({
                    'id': conv_id,
                    'title': conversation.get('title', 'Untitled'),
                    'preview': conversation.get('preview', ''),
                    'thread_id': conversation.get('thread_id'),
                    'lastUpdated': conversation.get('updated_at', conversation.get('created_at')),
                    'message_count': conversation.get('message_count', 0)
                })
                continue
            
            # Search in messages if available
            messages = conversation.get('messages', [])
            for message in messages:
                content = message.get('content', '').lower()
                if query in content:
                    matching_conversations.append({
                        'id': conv_id,
                        'title': conversation.get('title', 'Untitled'),
                        'preview': conversation.get('preview', ''),
                        'thread_id': conversation.get('thread_id'),
                        'lastUpdated': conversation.get('updated_at', conversation.get('created_at')),
                        'message_count': conversation.get('message_count', 0)
                    })
                    break  # Only add once per conversation
        
        # Sort by last updated (most recent first)
        matching_conversations.sort(key=lambda x: x.get('lastUpdated', ''), reverse=True)
        
        return jsonify({
            'conversations': matching_conversations,
            'query': query,
            'total': len(matching_conversations)
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/conversations/<conversation_id>/switch', methods=['POST'])
def switch_conversation(conversation_id):
    """Switch to a different conversation with proper thread and session handling"""
    try:
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation = conversations[conversation_id]
        
        # Update session with conversation context
        session['conversation_id'] = conversation_id
        session['messages'] = conversation.get('messages', [])
        
        # Handle thread_id if available
        thread_id = conversation.get('thread_id')
        if thread_id and thread_id.startswith('thread_'):
            # Verify thread still exists and get fresh messages from OpenAI
            api_key = get_api_key()
            if api_key and ASSISTANT_MANAGER_AVAILABLE:
                try:
                    assistant_manager = get_or_create_assistant_manager(api_key)
                    thread_messages = assistant_manager.list_messages(thread_id)
                    
                    if thread_messages and thread_messages.get('success'):
                        # Update session with fresh OpenAI thread messages
                        formatted_messages = []
                        for msg in thread_messages['messages']:
                            formatted_msg = {
                                'id': msg.get('id', str(uuid.uuid4())),
                                'role': msg.get('role', 'assistant'),
                                'content': msg.get('content', [{}])[0].get('text', {}).get('value', '') if msg.get('content') else '',
                                'timestamp': datetime.fromtimestamp(msg.get('created_at', time.time())).isoformat()
                            }
                            formatted_messages.append(formatted_msg)
                        
                        session['messages'] = formatted_messages
                        print(f"✅ Refreshed conversation from OpenAI thread: {len(formatted_messages)} messages")
                    else:
                        print(f"⚠️ Failed to refresh from OpenAI thread, using stored messages")
                        
                except Exception as e:
                    print(f"⚠️ Error refreshing from OpenAI thread: {e}, using stored messages")
        
        session.modified = True
        
        return jsonify({
            'conversation_id': conversation_id,
            'thread_id': thread_id,
            'message_count': len(session.get('messages', [])),
            'message': 'Switched to conversation successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to switch conversation: {str(e)}'}), 500

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

@app.route('/set-conversation-context', methods=['POST'])
def set_conversation_context():
    """Set conversation context in session from loaded conversation"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        # Convert frontend message format to session format
        session_messages = []
        for msg in messages:
            session_msg = {
                'id': msg.get('id', str(uuid.uuid4())),
                'role': msg.get('role', 'user' if msg.get('isUser') else 'assistant'),
                'content': msg.get('textContent', ''),
                'timestamp': msg.get('timestamp', datetime.now().isoformat())
            }
            session_messages.append(session_msg)
        
        # Update session with conversation context
        session['messages'] = session_messages
        session.modified = True
        
        print(f"✅ Set conversation context with {len(session_messages)} messages")
        return jsonify({'success': True, 'message_count': len(session_messages)})
        
    except Exception as e:
        print(f"❌ Error setting conversation context: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/favicon.ico')
def favicon():
    """Return a 204 No Content for favicon requests to avoid 404 errors"""
    return '', 204

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
