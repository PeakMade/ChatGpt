"""
ChatGPT Clone - Streamlit Application
A modern, responsive web application that replicates ChatGPT functionality
"""

import streamlit as st
import openai
from datetime import datetime
import uuid
import os
from typing import List, Dict, Any
import PyPDF2
import io
import json

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading
    pass

# Configure page
st.set_page_config(
    page_title="AI BOOST",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
    }
    
    .main-header p {
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 0.5rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0.75rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-size: 0.9rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 0.75rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        font-size: 0.9rem;
    }
    
    .sidebar-content {
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 0.75rem;
    }
    
    .conversation-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.85rem;
    }
    
    .conversation-item:hover {
        background: #f0f8f0;
        border-color: #28a745;
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
        font-size: 0.85rem;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #218838 0%, #1ea085 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(40, 167, 69, 0.4);
    }
    
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #28a745;
        font-size: 0.85rem;
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #28a745;
        font-size: 0.85rem;
    }
    
    .stFileUploader > div {
        border: 2px dashed #28a745;
        border-radius: 8px;
        background: #f8f9fa;
        padding: 0.5rem;
    }
    
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #2d3436;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid #28a745;
    }
    
    .compact-metric {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.25rem 0;
    }
    
    .compact-metric .metric-value {
        font-size: 1.2rem;
        font-weight: bold;
        color: #28a745;
    }
    
    .compact-metric .metric-label {
        font-size: 0.75rem;
        color: #6c757d;
    }
    
    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Make expander more compact */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
    }
    
    /* Compact chat input */
    .stChatInput {
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'categories' not in st.session_state:
    st.session_state.categories = ["General", "Work", "Learning", "Creative"]
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "General"

# Session-based storage functions (no database needed)
def save_conversation_to_session(conversation_data):
    """Save conversation to session state"""
    if 'saved_conversations' not in st.session_state:
        st.session_state.saved_conversations = []
    
    conversation_id = str(uuid.uuid4())
    conversation_data['id'] = conversation_id
    st.session_state.saved_conversations.insert(0, conversation_data)  # Add to beginning
    
    # Keep only last 10 conversations to avoid memory issues
    if len(st.session_state.saved_conversations) > 10:
        st.session_state.saved_conversations = st.session_state.saved_conversations[:10]
    
    return conversation_id

def load_conversations_from_session(user_id, category=None):
    """Load conversations from session state"""
    if 'saved_conversations' not in st.session_state:
        return []
    
    conversations = st.session_state.saved_conversations
    
    # Filter by category if specified
    if category and category != "All":
        conversations = [conv for conv in conversations if conv.get("category") == category]
    
    return conversations

def update_conversation_in_session(conversation_id, messages):
    """Update existing conversation in session"""
    if 'saved_conversations' not in st.session_state:
        return False
    
    for i, conv in enumerate(st.session_state.saved_conversations):
        if conv.get('id') == conversation_id:
            st.session_state.saved_conversations[i]['messages'] = messages
            st.session_state.saved_conversations[i]['updated_at'] = datetime.now().isoformat()
            return True
    
    return False

# OpenAI configuration
def init_openai():
    """Initialize OpenAI client"""
    # Check for API key in session state first (from sidebar input)
    api_key = st.session_state.get('user_api_key', '')
    
    # If not in session state, check environment variables
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            try:
                api_key = st.secrets.get("OPENAI_API_KEY", "")
            except:
                api_key = ""
    
    if not api_key:
        return None
    
    # Initialize OpenAI client with the new v1.0+ API
    try:
        client = openai.OpenAI(api_key=api_key)
        return client
    except Exception as e:
        return None

# Database operations
def save_conversation(container, conversation_data):
    """Save conversation to Azure Cosmos DB"""
    if container:
        try:
            # Add a unique ID for Cosmos DB
            conversation_data["id"] = str(uuid.uuid4())
            result = container.create_item(body=conversation_data)
            return result["id"]
        except Exception as e:
            st.error(f"Failed to save conversation: {e}")
            return None
    return None

# File processing functions
def process_pdf(uploaded_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Failed to process PDF: {e}")
        return ""

def process_text_file(uploaded_file):
    """Process text file"""
    try:
        content = uploaded_file.read().decode("utf-8")
        return content
    except Exception as e:
        st.error(f"Failed to process text file: {e}")
        return ""

# Chat function
def get_chat_response(client, messages, uploaded_content=""):
    """Get response from OpenAI API"""
    if not client:
        return "Error: No OpenAI client available. Please check your API key."
        
    try:
        # Prepare messages for OpenAI
        openai_messages = []
        
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
        
        # Get response from OpenAI using new client API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Main application
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>AI BOOST</h1>
        <p>Modern AI-powered chat interface</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for conversation management
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        # API Configuration - Always show at top
        st.markdown('<div class="section-header">API Configuration</div>', unsafe_allow_html=True)
        
        # Check if we already have an API key
        current_api_key = os.getenv("OPENAI_API_KEY", "")
        if not current_api_key:
            try:
                current_api_key = st.secrets.get("OPENAI_API_KEY", "")
            except:
                current_api_key = ""
        
        # API Key input - using text_area for long keys
        user_api_key = st.text_area(
            "OpenAI API Key",
            value="",
            height=80,
            placeholder="Enter your OpenAI API key (paste the full key here)",
            help="Get your API key from https://platform.openai.com/api-keys"
        )
        
        # Remove any whitespace/newlines
        if user_api_key:
            user_api_key = user_api_key.strip()
        
        # Store the API key in session state
        if user_api_key:
            st.session_state.user_api_key = user_api_key
            st.success("✅ API key configured!")
            # Force a rerun to update the OpenAI client
            st.rerun()
        elif current_api_key:
            st.session_state.user_api_key = current_api_key
            st.info("✅ Using environment API key")
        else:
            st.warning("⚠️ Please enter your OpenAI API key to use the AI")
        
        st.markdown("---")  # Separator line
        
        # New conversation and controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_conversation_id = None
                st.rerun()
        
        with col2:
            if st.session_state.messages and st.button("Save", use_container_width=True):
                conversation_data = {
                    "user_id": st.session_state.user_id,
                    "title": st.session_state.messages[0]["content"][:30] + "..." if st.session_state.messages else "New Conversation",
                    "category": st.session_state.selected_category,
                    "messages": st.session_state.messages,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                if st.session_state.current_conversation_id:
                    update_conversation_in_session(st.session_state.current_conversation_id, st.session_state.messages)
                    st.success("Updated!")
                else:
                    conversation_id = save_conversation_to_session(conversation_data)
                    if conversation_id:
                        st.session_state.current_conversation_id = conversation_id
                        st.success("Saved!")
        
        # Category and filter in one row
        category_options = ["All"] + st.session_state.categories
        selected_category = st.selectbox("Category Filter", category_options, key="filter_cat")
        
        # Add category input (compact)
        new_category = st.text_input("Add Category", placeholder="New category", key="new_cat")
        if st.button("Add") and new_category:
            if new_category not in st.session_state.categories:
                st.session_state.categories.append(new_category)
                st.success(f"Added: {new_category}")
                st.rerun()
        
        # Saved conversations (compact list)
        st.markdown("**Saved Conversations:**")
        conversations = load_conversations_from_session(st.session_state.user_id, selected_category if selected_category != "All" else None)
        
        for conv in conversations[:5]:  # Show only 5 most recent
            title = conv.get("title", "Untitled")[:25] + "..."
            if st.button(title, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.messages = conv.get("messages", [])
                st.session_state.current_conversation_id = conv["id"]
                st.session_state.selected_category = conv.get("category", "General")
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize OpenAI client after sidebar (so we have the API key from session state)
    openai_client = init_openai()
    
    # Main chat interface
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Compact file upload
        uploaded_file = st.file_uploader("📎 Upload file for context", type=['txt', 'pdf'], help="Upload text/PDF files")
        
        uploaded_content = ""
        if uploaded_file:
            with st.spinner("Processing..."):
                if uploaded_file.type == "application/pdf":
                    uploaded_content = process_pdf(uploaded_file)
                else:
                    uploaded_content = process_text_file(uploaded_file)
                
                if uploaded_content:
                    st.success(f"✅ {len(uploaded_content)} chars processed")
        
        # Simple chat input that actually works
        if prompt := st.chat_input("What would you like to know?"):
            if openai_client:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get and add AI response
                with st.spinner("Thinking..."):
                    response = get_chat_response(openai_client, st.session_state.messages, uploaded_content)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Force rerun to show new messages
                st.rerun()
            else:
                st.error("Please enter your API key in the sidebar first!")
        
        # Display conversation history AFTER chat input processing
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**AI:** {message['content']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Compact stats and category
        st.markdown("**Current Category**")
        st.session_state.selected_category = st.selectbox(
            "Category",
            st.session_state.categories,
            index=st.session_state.categories.index(st.session_state.selected_category),
            label_visibility="collapsed"
        )
        
        # Compact stats
        st.markdown("**Session Stats**")
        message_count = len(st.session_state.messages)
        word_count = sum(len(msg["content"].split()) for msg in st.session_state.messages) if st.session_state.messages else 0
        
        st.markdown(f"""
        <div class="compact-metric">
            <div class="metric-value">{message_count}</div>
            <div class="metric-label">Messages</div>
        </div>
        <div class="compact-metric">
            <div class="metric-value">{word_count}</div>
            <div class="metric-label">Words</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
