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

# Removed Azure Key Vault integration - using environment variables instead

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
- Current date: September 3, 2025
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
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions."
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
    """Handle chat messages with conversation callbacks"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_api_key = data.get('api_key', '').strip()
        conversation_id = data.get('conversation_id', session.get('conversation_id'))
        
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
        
        # Initialize or get conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            session['conversation_id'] = conversation_id
        
        # Update session API key
        session['api_key'] = api_key
        
        # Get existing conversation history
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
        
        # Add user message to conversation
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        session['conversations'][conversation_id]['messages'].append(user_msg)
        
        # Prepare messages for OpenAI API with conversation history
        conversation_messages = session['conversations'][conversation_id]['messages']
        
        # Get AI response with full conversation context
        ai_response = get_chat_response_with_conversation(api_key, conversation_messages)
        
        # Add AI response to conversation
        ai_msg = {
            "role": "assistant", 
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        session['conversations'][conversation_id]['messages'].append(ai_msg)
        session['conversations'][conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Save session
        session.modified = True
        
        return jsonify({
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now().isoformat(),
            'conversation_id': conversation_id,
            'message_ids': {
                'user': user_msg['id'],
                'assistant': ai_msg['id']
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations - mimics OpenAI conversation API"""
    try:
        conversations = session.get('conversations', {})
        conversation_list = []
        
        for conv_id, conv_data in conversations.items():
            conversation_summary = {
                'id': conv_id,
                'title': conv_data.get('title', 'Untitled Conversation'),
                'created_at': conv_data.get('created_at'),
                'updated_at': conv_data.get('updated_at'),
                'message_count': len(conv_data.get('messages', [])),
                'last_message': conv_data.get('messages', [])[-1] if conv_data.get('messages') else None
            }
            conversation_list.append(conversation_summary)
        
        # Sort by updated_at (most recent first)
        conversation_list.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return jsonify({
            'conversations': conversation_list,
            'total': len(conversation_list)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve conversations: {str(e)}'}), 500

@app.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation_by_id(conversation_id):
    """Get specific conversation by ID - mimics OpenAI conversation API"""
    try:
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        conversation = conversations[conversation_id]
        
        return jsonify({
            'id': conversation_id,
            'title': conversation.get('title', 'Untitled Conversation'),
            'created_at': conversation.get('created_at'),
            'updated_at': conversation.get('updated_at'),
            'messages': conversation.get('messages', []),
            'message_count': len(conversation.get('messages', []))
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve conversation: {str(e)}'}), 500

@app.route('/conversations/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    try:
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        messages = conversations[conversation_id].get('messages', [])
        
        return jsonify({
            'conversation_id': conversation_id,
            'messages': messages,
            'total': len(messages)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve messages: {str(e)}'}), 500

@app.route('/conversations', methods=['POST'])
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

@app.route('/conversations/<conversation_id>', methods=['DELETE'])
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

@app.route('/conversations/<conversation_id>/switch', methods=['POST'])
def switch_conversation(conversation_id):
    """Switch to a different conversation"""
    try:
        conversations = session.get('conversations', {})
        
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        session['conversation_id'] = conversation_id
        session.modified = True
        
        return jsonify({
            'conversation_id': conversation_id,
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
