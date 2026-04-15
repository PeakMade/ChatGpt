"""
AI BOOST - Flask Application
A modern, responsive web application that replicates ChatGPT functionality using Flask
"""

# Internal note: App running optimally - Sept 2025

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import openai
from datetime import datetime
import uuid
import os
import time
from typing import List, Dict, Any
import PyPDF2
import io
import json
import base64
from docx import Document

# Import configuration functions for external model settings
from config.config import (
    get_model_for_task, 
    get_max_tokens, 
    get_temperature, 
    get_complexity_threshold,
    get_complex_keywords,
    get_openai_api_key,
    get_web_search_keywords,
    is_intelligent_selection_enabled,
    get_model_description,
    SECRET_KEY
)

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
import re

# ── System prompt (single source of truth) ───────────────────────────────────
SYSTEM_PROMPT = (
    "You are AI BOOST. Write responses that feel natural and well-structured — "
    "like a knowledgeable person explaining something clearly, not a robot filling a template.\n\n"
    "You have access to real-time web search for current information such as sports scores, schedules, "
    "news, prices, weather, and other live data. When a question is about something current or time-sensitive, "
    "answer it directly using that capability — do NOT tell the user you lack web search or browsing access.\n\n"
    "Use paragraphs to explain context, reasoning, and nuance. "
    "Use bullet points ONLY when you are listing 3 or more distinct items, steps, or options. "
    "Do NOT convert every sentence into a bullet. Do NOT put the entire response in bullets. "
    "A good response might open with a paragraph, use bullets for a specific list, "
    "then continue with another short paragraph or closing thought.\n\n"
    "CRITICAL formatting rule: each bullet MUST be on its own separate line starting with '- '. "
    "Never write bullets inline like 'text - item - item - item' all on one line.\n\n"
    "NO URLS — do not write https://, www., or any links. "
    "If you must reference a source, write only the bare domain like (nfl.com)."
)
# ─────────────────────────────────────────────────────────────────────────────

def check_session_cookie_size():
    """Check if session will exceed browser cookie limits WITHOUT removing conversation data"""
    try:
        import json
        session_data = dict(session)
        session_json = json.dumps(session_data, default=str)
        session_size = len(session_json.encode('utf-8'))
        
        print(f"📊 Session size: {session_size} bytes (browser limit: ~4000 bytes)")
        
        # Log warning if approaching limit but DON'T remove data
        if session_size > 3500:
            print(f"⚠️ Session size warning: {session_size} bytes - approaching browser limit")
            print("🔍 Large session detected but preserving conversation continuity")
            
        return session_size
        
    except Exception as e:
        print(f"⚠️ Session size check error: {e}")
        return 0

def strip_urls_from_response(response):
    """Remove all URLs from the response to ensure clean output"""
    if not response:
        return response
    
    # Remove markdown links [text](url) but keep the text
    response = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)', r'\1', response)
    
    # Remove URLs in parentheses with https://
    response = re.sub(r'\(https://[^)]+\)', '', response)
    # Remove URLs in parentheses with http://
    response = re.sub(r'\(http://[^)]+\)', '', response)
    
    # Remove standalone URLs (not in parentheses)
    response = re.sub(r'https?://[^\s)]+[^\s.,!?)]', '', response)
    
    # Extract domain names from remaining URL patterns and convert to simple citations
    def extract_domain(match):
        url = match.group(0)
        # Extract domain from URL
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            return f'({domain})'
        return ''
    
    # Look for any remaining URL patterns and convert to domain citations
    response = re.sub(r'\([^)]*https?://[^)]*\)', extract_domain, response)
    
    # Clean up formatting issues
    response = re.sub(r'\(\s*\)', '', response)  # Remove empty parentheses
    response = re.sub(r'\s+', ' ', response)     # Remove extra spaces
    response = re.sub(r'\s+([.,!?])', r'\1', response)  # Fix punctuation spacing
    response = response.strip()
    
    return response

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(dotenv_path=Path(__file__).parent / 'config' / '.env')
except ImportError:
    # dotenv not installed, skip loading
    pass

app = Flask(__name__)
# Use a consistent secret key for development, secure random for production
app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 365  # 1 year

from flask_session import Session
Session(app)

# Register auth blueprint
from auth.routes import auth_bp
app.register_blueprint(auth_bp)

# Public paths that don't require authentication
_PUBLIC_PREFIXES = ('/auth/', '/favicon.ico', '/static/')

@app.before_request
def make_session_permanent():
    """Make all sessions permanent and enforce authentication."""
    session.permanent = True

    # Allow auth routes and static assets through without a login check
    if request.path.startswith(_PUBLIC_PREFIXES):
        return

    if not session.get('authenticated'):
        return redirect(url_for('auth.login', next=request.url))

def get_api_key():
    """Get API key from configuration file, environment variables, or return None for user input"""
    # Try configuration file first (permanent embedding)
    config_key = get_openai_api_key().strip()
    if config_key and config_key.startswith('sk-') and len(config_key) > 20:
        print(f"Using configuration file API key (length: {len(config_key)})")
        return config_key
    
    # Try environment variable second (local development and production)
    env_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if env_key and env_key.startswith('sk-') and len(env_key) > 20:
        print(f"Using environment API key (length: {len(env_key)})")
        return env_key
    
    # Debug info
    print(f"No API key found in configuration file or environment variables")
    print(f"  - Config file key exists: {bool(config_key)}")
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
        clean_api_key = api_key.strip() if api_key else ""
        client = openai.OpenAI(api_key=clean_api_key)
        return client
    except Exception as e:
        return None

def should_use_web_search(user_message):
    """
    Determine if the user's message requires web search for current information.
    Uses external configuration for web search keywords.
    """
    if not user_message:
        return False
        
    message_lower = user_message.lower()
    
    # Get web search keywords from configuration
    current_patterns = get_web_search_keywords()
    
    for pattern in current_patterns:
        if pattern in message_lower:
            print(f"🌐 WEB SEARCH TRIGGERED → Pattern '{pattern}' detected in: \"{user_message[:50]}...\"")
            return True
    
    print(f"📚 NO WEB SEARCH → Using training data for: \"{user_message[:50]}...\"")
    return False

def format_web_search_response(response_text):
    """
    Reformat web search response to move all source citations to the end.
    Converts inline citations like (source.com) to a clean sources section at the bottom.
    """
    import re
    
    if not response_text:
        return response_text
    
    # Extract all source citations (pattern: text in parentheses ending with .com or similar)
    source_pattern = r'\(([^)]*\.(?:com|org|net|edu|gov|co\.uk|news|io|ai)[^)]*)\)'
    sources = re.findall(source_pattern, response_text)
    
    if not sources:
        return response_text
    
    # Remove duplicate sources while preserving order
    unique_sources = []
    seen = set()
    for source in sources:
        if source.lower() not in seen:
            unique_sources.append(source)
            seen.add(source.lower())
    
    # Remove all inline source citations from the text
    clean_text = re.sub(source_pattern, '', response_text)
    
    # Clean up any double spaces or extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Add sources section at the end if we found any
    if unique_sources:
        clean_text += "\n\n**Sources:**"
        for i, source in enumerate(unique_sources, 1):
            clean_text += f"\n{i}. {source}"
    
    return clean_text

def select_optimal_model(user_message, user_preference=None):
    """
    Enhanced intelligent model selection using external configuration.
    Uses model_config.json for models, keywords, and settings.
    """
    # Check if intelligent selection is enabled
    if not is_intelligent_selection_enabled():
        return get_model_for_task('fallback')
        
    if user_preference and user_preference != "auto":
        return get_model_for_task('complex')
    
    # Convert to lowercase for analysis
    message_lower = user_message.lower()
    
    # Get complex keywords from configuration
    all_complex_keywords = get_complex_keywords()
    
    # Check for any complexity triggers → use complex model
    for keyword in all_complex_keywords:
        if keyword in message_lower:
            print(f"🧠 COMPLEX MODEL SELECTED → Complex keyword '{keyword}' detected in: \"{user_message[:50]}...\"")
            return get_model_for_task('complex')
    
    # Check message length → longer messages use complex model
    complexity_threshold = get_complexity_threshold()
    if len(user_message) > complexity_threshold:
        print(f"📏 COMPLEX MODEL SELECTED → Long message ({len(user_message)} chars): \"{user_message[:50]}...\"")
        return get_model_for_task('complex')
    
    # Check for complex question patterns → use complex model
    complex_patterns = [
        'how does', 'why does', 'what are the implications',
        'explain how', 'explain why', 'what would happen if',
        'pros and cons', 'advantages and disadvantages',
        'step by step', 'detailed explanation'
    ]
    
    for pattern in complex_patterns:
        if pattern in message_lower:
            print(f"🧠 COMPLEX MODEL SELECTED → Complex pattern '{pattern}' in: \"{user_message[:50]}...\"")
            return get_model_for_task('complex')
    
    # Default to simple model for simple queries (cost optimization)
    print(f"💰 SIMPLE MODEL SELECTED → Simple query: \"{user_message[:50]}...\"")
    return get_model_for_task('simple')

def extract_text_from_content(content):
    """Safely extract plain text from a message content (handles str or vision list)"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Vision content: list of dicts with type 'text' or 'image_url'
        parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
        return " ".join(parts)
    return ""

def get_chat_response_with_conversation(api_key, conversation_messages, selected_model=None, uploaded_content=""):
    """Get response from OpenAI API with full conversation context"""
    if not api_key:
        return "Error: No OpenAI API key provided."
        
    try:
        # Clean the API key of any whitespace
        api_key = api_key.strip()
        
        # Get the user's message text for model selection (safe for vision messages)
        user_message = ""
        if conversation_messages:
            for msg in reversed(conversation_messages):
                if msg.get("role") == "user":
                    user_message = extract_text_from_content(msg.get("content", ""))
                    break
        

        
        # Select optimal model based on message complexity (if not provided)
        if not selected_model:
            selected_model = select_optimal_model(user_message)
        
        try:
            # Method 1: Basic client creation - ensure clean API key
            clean_api_key = api_key.strip() if api_key else ""
            client = openai.OpenAI(api_key=clean_api_key)
        except Exception as e:
            try:
                # Method 2: Fallback - try with explicit parameters only
                client = openai.OpenAI(api_key=clean_api_key, timeout=60.0)
            except Exception as e2:
                # Method 3: Use simplified approach
                print(f"Error (fallback): {e2}")
                return f"Error (fallback): {e2}"
        
        # Prepare messages for OpenAI
        openai_messages = []
        
        openai_messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"The user has uploaded the following content for context:\n\n{uploaded_content}\n\nPlease use this content to help answer their questions with comprehensive, detailed responses."
            })
        
        # Add conversation history (only user and assistant messages)
        for msg in conversation_messages:
            if msg["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # DEBUG: Show messages being sent to OpenAI API
        print("\n" + "🚀" * 30)
        print("📤 MESSAGES BEING SENT TO OPENAI API:")
        print("🚀" * 60)
        for i, msg in enumerate(openai_messages):
            role_emoji = "🧠" if msg["role"] == "system" else ("👤" if msg["role"] == "user" else "🤖")
            content_text = extract_text_from_content(msg["content"])
            content_preview = content_text[:100] + ("..." if len(content_text) > 100 else "")
            print(f"{role_emoji} Message {i+1} ({msg['role'].upper()}): {content_preview}")
        print("🚀" * 60)
        print(f"🎯 MODEL SELECTED: {selected_model}")
        print(f"📊 TOTAL MESSAGES: {len(openai_messages)}")
        print("🚀" * 60 + "\n")
        
        # Get response from OpenAI using intelligently selected model
        print(f"here2: {openai_messages}")
        
        # Check if we should use web search for current information
        last_content = conversation_messages[-1]["content"] if conversation_messages else ""
        user_message = extract_text_from_content(last_content)
        needs_web_search = should_use_web_search(user_message)
        
        if needs_web_search:
            print("🌐 ENABLING WEB SEARCH for current information")
            try:
                response = client.responses.create(
                    model=get_model_for_task('web_search'),
                    tools=[{"type": "web_search"}],
                    input=openai_messages,
                    temperature=get_temperature()
                )
                raw_response = response.output_text
                ai_response = format_web_search_response(raw_response)
            except Exception as ws_err:
                print(f"⚠️ Web search unavailable ({ws_err}), falling back to training data")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=openai_messages,
                    max_completion_tokens=get_max_tokens(),
                    temperature=get_temperature()
                )
                ai_response = response.choices[0].message.content
        else:
            response = client.chat.completions.create(
                model=selected_model,
                messages=openai_messages,
                max_completion_tokens=get_max_tokens(),
                temperature=get_temperature()
            )
            ai_response = response.choices[0].message.content
        
        # DEBUG: Show response received from OpenAI API
        print("\n" + "📥" * 30)
        print("📥 RESPONSE RECEIVED FROM OPENAI API:")
        print("📥" * 60)
        print(f"🤖 AI RESPONSE: {ai_response}")
        print(f"🎯 MODEL USED: {selected_model}")
        print(f"📊 RESPONSE LENGTH: {len(ai_response)} characters")
        print("📥" * 60 + "\n")
        
        # Strip URLs from response before returning
        clean_response = strip_urls_from_response(ai_response)
        return clean_response
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
        
        # Get the user's message for model selection
        user_message = ""
        if messages:
            # Get the last user message
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
        
        # Select optimal model based on message complexity
        selected_model = select_optimal_model(user_message)
        
        try:
            # Method 1: Basic client creation
            clean_api_key = api_key.strip() if api_key else ""
            client = openai.OpenAI(api_key=clean_api_key)
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
        
        openai_messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"Context: {uploaded_content}\n\nUse this information to help answer the user's question. NO URLS ANYWHERE."
            })
        
        # Add conversation history
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # DEBUG: Show messages being sent to OpenAI API
        print("\n" + "🚀" * 30)
        print("📤 MESSAGES BEING SENT TO OPENAI API (get_chat_response):")
        print("🚀" * 60)
        for i, msg in enumerate(openai_messages):
            role_emoji = "🧠" if msg["role"] == "system" else ("👤" if msg["role"] == "user" else "🤖")
            content_text = extract_text_from_content(msg["content"])
            content_preview = content_text[:100] + ("..." if len(content_text) > 100 else "")
            print(f"{role_emoji} Message {i+1} ({msg['role'].upper()}): {content_preview}")
        print("🚀" * 60)
        print(f"🎯 MODEL SELECTED: {selected_model}")
        print(f"📊 TOTAL MESSAGES: {len(openai_messages)}")
        print("🚀" * 60 + "\n")
        
        # Get response from OpenAI using intelligently selected model
        print(f"here3: {openai_messages}")
        
        # Check if we should use web search for current information
        user_message = messages[-1]["content"] if messages else ""
        needs_web_search = should_use_web_search(user_message)
        
        if needs_web_search:
            print("🌐 ENABLING WEB SEARCH for current information")
            try:
                response = client.responses.create(
                    model=get_model_for_task('web_search'),
                    tools=[{"type": "web_search"}],
                    input=openai_messages,
                    temperature=get_temperature()
                )
                raw_response = response.output_text
                ai_response = format_web_search_response(raw_response)
            except Exception as ws_err:
                print(f"⚠️ Web search unavailable ({ws_err}), falling back to training data")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=openai_messages,
                    max_completion_tokens=get_max_tokens(),
                    temperature=get_temperature()
                )
                ai_response = response.choices[0].message.content
        else:
            response = client.chat.completions.create(
                model=selected_model,
                messages=openai_messages,
                max_completion_tokens=get_max_tokens(),
                temperature=get_temperature()
            )
            ai_response = response.choices[0].message.content
        
        # DEBUG: Show response received from OpenAI API
        print("\n" + "📥" * 30)
        print("📥 RESPONSE RECEIVED FROM OPENAI API (get_chat_response):")
        print("📥" * 60)
        print(f"🤖 AI RESPONSE: {ai_response}")
        print(f"🎯 MODEL USED: {selected_model}")
        print(f"📊 RESPONSE LENGTH: {len(ai_response)} characters")
        print("📥" * 60 + "\n")
        
        # Strip URLs from response before returning
        clean_response = strip_urls_from_response(ai_response)
        return clean_response
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
        # Get the user's message for model selection
        user_message = ""
        if messages:
            # Get the last user message
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
        
        # Select optimal model based on message complexity
        selected_model = select_optimal_model(user_message)
        
        # Create client with explicit API key - ensure clean parameters
        clean_api_key = api_key.strip() if api_key else ""
        client = openai.OpenAI(api_key=clean_api_key)
        # Prepare messages for OpenAI
        openai_messages = []
        
        # Add system prompt with 2025 knowledge context
        current_date = datetime.now().strftime("%B %Y")  # e.g., "September 2025"
        openai_messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })
        
        # Add uploaded content as context if provided
        if uploaded_content:
            openai_messages.append({
                "role": "system",
                "content": f"Context: {uploaded_content}\n\nUse this information to help answer the user's question. NO URLS ANYWHERE."
            })
        
        # Add conversation history
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # DEBUG: Show messages being sent to OpenAI API
        print("\n" + "🚀" * 30)
        print("📤 MESSAGES BEING SENT TO OPENAI API (get_chat_response_legacy):")
        print("🚀" * 60)
        for i, msg in enumerate(openai_messages):
            role_emoji = "🧠" if msg["role"] == "system" else ("👤" if msg["role"] == "user" else "🤖")
            content_text = extract_text_from_content(msg["content"])
            content_preview = content_text[:100] + ("..." if len(content_text) > 100 else "")
            print(f"{role_emoji} Message {i+1} ({msg['role'].upper()}): {content_preview}")
        print("🚀" * 60)
        print(f"🎯 MODEL SELECTED: {selected_model}")
        print(f"📊 TOTAL MESSAGES: {len(openai_messages)}")
        print("🚀" * 60 + "\n")
        
        # Use modern API call with intelligently selected model
        print(f"here: {openai_messages}")
        
        # Check if we should use web search for current information
        user_message = extract_text_from_content(messages[-1]["content"]) if messages else ""
        needs_web_search = should_use_web_search(user_message)
        
        if needs_web_search:
            print("🌐 ENABLING WEB SEARCH for current information")
            try:
                response = client.responses.create(
                    model=get_model_for_task('web_search'),
                    tools=[{"type": "web_search"}],
                    input=openai_messages,
                    temperature=get_temperature()
                )
                raw_response = response.output_text
                ai_response = format_web_search_response(raw_response)
            except Exception as ws_err:
                print(f"⚠️ Web search unavailable ({ws_err}), falling back to training data")
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=openai_messages,
                    max_completion_tokens=get_max_tokens(),
                    temperature=get_temperature()
                )
                ai_response = response.choices[0].message.content
        else:
            response = client.chat.completions.create(
                model=selected_model,
                messages=openai_messages,
                max_completion_tokens=get_max_tokens(),
                temperature=get_temperature()
            )
            ai_response = response.choices[0].message.content
        
        # DEBUG: Show response received from OpenAI API
        print("\n" + "📥" * 30)
        print("📥 RESPONSE RECEIVED FROM OPENAI API (get_chat_response_legacy):")
        print("📥" * 60)
        print(f"🤖 AI RESPONSE: {ai_response}")
        print(f"🎯 MODEL USED: {selected_model}")
        print(f"📊 RESPONSE LENGTH: {len(ai_response)} characters")
        print("📥" * 60 + "\n")
        
        # Strip URLs from response before returning
        clean_response = strip_urls_from_response(ai_response)
        return clean_response
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

def extract_text_from_docx(file):
    """Extract text from Word .docx file"""
    try:
        doc = Document(file)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"Error reading Word document: {str(e)}"

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
    
    return render_template('index.html', user=session.get('user'))

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

@app.route('/config')
def config_status():
    """View current model configuration settings"""
    from config.config import load_model_config, get_all_models, get_all_settings
    
    try:
        config_data = load_model_config()
        
        # Test the configuration functions
        config_info = {
            'config_loaded': True,
            'config_type': 'INI',
            'models': {
                'simple': get_model_for_task('simple'),
                'complex': get_model_for_task('complex'),
                'web_search': get_model_for_task('web_search'),
                'fallback': get_model_for_task('fallback')
            },
            'settings': {
                'max_tokens': get_max_tokens(),
                'temperature': get_temperature(),
                'complexity_threshold': get_complexity_threshold(),
                'intelligent_selection_enabled': is_intelligent_selection_enabled()
            },
            'keywords': {
                'complex_keywords_count': len(get_complex_keywords()),
                'web_search_keywords_count': len(get_web_search_keywords()),
                'sample_complex_keywords': get_complex_keywords()[:5],
                'sample_web_search_keywords': get_web_search_keywords()[:5]
            },
            'descriptions': {
                'simple': get_model_description('simple'),
                'complex': get_model_description('complex'),
                'web_search': get_model_description('web_search'),
                'fallback': get_model_description('fallback')
            },
            'raw_sections': {
                'models': get_all_models(),
                'settings': get_all_settings()
            }
        }
        
        return jsonify(config_info)
        
    except Exception as e:
        return jsonify({
            'config_loaded': False,
            'error': str(e),
            'fallback_models': {
                'simple': 'gpt-5.4-mini',
                'complex': 'gpt-5.4-mini',
                'web_search': 'gpt-5.4-mini',
                'fallback': 'gpt-5.4-mini'
            }
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with conversation callbacks using thread_id and user_id"""
    print("\n" + "="*80)
    print("🎯 NEW CHAT REQUEST RECEIVED!")
    print("="*80)
    
    try:
        # Monitor session size for debugging (preserves all conversation data)
        session_size = check_session_cookie_size()
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
        
        uploaded_content_check = data.get('uploaded_content', '').strip() if data.get('uploaded_content') else ''
        uploaded_image_check = data.get('uploaded_image', None)
        if not user_message:
            if uploaded_image_check:
                user_message = 'What is in this image?'
            elif uploaded_content_check:
                user_message = 'Please summarize this document.'
            else:
                return jsonify({'error': 'Message cannot be empty'}), 400
        
        if not api_key:
            return jsonify({'error': 'Please enter your OpenAI API key'}), 400
        
        # Get uploaded content and image data if present
        uploaded_image = data.get('uploaded_image', None)
        uploaded_content = data.get('uploaded_content', '').strip() if data.get('uploaded_content') else ''

        # Check for web search requirements FIRST
        needs_web_search = should_use_web_search(user_message)
        if needs_web_search:
            print("🌐 WEB SEARCH REQUIRED - Using web search model")
            selected_model = get_model_for_task('web_search')
            # For web search, use the fallback handler that includes web search functionality
            return handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id, uploaded_image=uploaded_image, uploaded_content=uploaded_content)
        
        # Smart model selection with debug output
        print("=" * 60)
        print(f"🤖 PROCESSING MESSAGE: \"{user_message[:80]}{'...' if len(user_message) > 80 else ''}\"")
        selected_model = select_optimal_model(user_message)
        print(f"🚀 FINAL DECISION: {selected_model.upper()}")
        print("=" * 60)

        # Use Responses API directly
        return handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id, selected_model, uploaded_image=uploaded_image, uploaded_content=uploaded_content)
        
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        # Log session size during error for debugging
        try:
            error_session_size = check_session_cookie_size()
            print(f"🐛 Session size during error: {error_session_size} bytes")
        except:
            pass
        
        # DON'T clear session - preserve conversation memory
        return jsonify({
            'error': f'Chat error: {str(e)}',
            'session_size_bytes': session_size if 'session_size' in locals() else 0
        }), 500

def handle_basic_chat_fallback(user_message, api_key, conversation_id, user_id, selected_model=None, uploaded_image=None, uploaded_content=''):
    """Fallback to basic chat completion when Assistant Manager fails"""
    try:
        print("🔄 Using fallback chat completion API")
        
        # Use provided model or select one
        if not selected_model:
            selected_model = select_optimal_model(user_message)
            print(f"🧠 Model selected for fallback: {selected_model}")
        else:
            print(f"🔄 Using pre-selected model for fallback: {selected_model}")
        
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
        
        # Add current user message (with vision content if image uploaded)
        if uploaded_image:
            conversation_messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message if user_message else "What is in this image?"},
                    {"type": "image_url", "image_url": {"url": uploaded_image}}
                ]
            })
        elif uploaded_content:
            # Embed document content directly in the user message so it is unambiguous
            combined = f"{user_message}\n\n[Attached document]:\n{uploaded_content}"
            conversation_messages.append({"role": "user", "content": combined})
        else:
            conversation_messages.append({"role": "user", "content": user_message})
        print(f"🔍 DEBUG: Total messages for API call: {len(conversation_messages)}")
        
        # Get AI response using basic completion with selected model
        ai_response = get_chat_response_with_conversation(api_key, conversation_messages, selected_model, uploaded_content=uploaded_content)
        
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
            'model_used': selected_model,  # Send model used to frontend
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

ALLOWED_IMAGE_TYPES = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_DOC_TYPES = {'.pdf', '.txt', '.docx'}

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads: PDF, TXT, DOCX, and images"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate filename to prevent path traversal
        filename = os.path.basename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ALLOWED_IMAGE_TYPES:
            # Read image and encode as base64 data URL
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                        '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp'}
            mime_type = mime_map.get(ext, 'image/jpeg')
            image_bytes = file.read()
            b64_data = base64.b64encode(image_bytes).decode('utf-8')
            data_url = f"data:{mime_type};base64,{b64_data}"
            return jsonify({
                'type': 'image',
                'filename': filename,
                'data_url': data_url,
                'mime_type': mime_type
            })
        elif ext == '.pdf':
            content = extract_text_from_pdf(file)
        elif ext == '.txt':
            content = file.read().decode('utf-8', errors='replace')
        elif ext == '.docx':
            content = extract_text_from_docx(file)
        else:
            return jsonify({'error': 'Unsupported file type. Supported: PDF, TXT, DOCX, JPG, PNG, GIF, WEBP'}), 400
        
        return jsonify({
            'type': 'document',
            'content': content[:1000] + ('...' if len(content) > 1000 else ''),
            'filename': filename,
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
        
        # Use permanent API key if available, otherwise use session key
        permanent_api_key = get_api_key()
        api_key_to_return = permanent_api_key if permanent_api_key else session.get('api_key', '')
            
        return jsonify({
            'messages': session.get('messages', []),
            'api_key': api_key_to_return
        })
    except Exception as e:
        return jsonify({
            'messages': [],
            'api_key': ''
        })

@app.route('/favicon.ico')
@app.route('/favicon.svg')
def favicon():
    """Serve the brain favicon."""
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.svg',
        mimetype='image/svg+xml',
    )

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
