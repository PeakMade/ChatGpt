"""
ChatGPT Clone - Streamlit Application
A modern, responsive web application that replicates ChatGPT functionality
"""

import streamlit as st
import openai
import os
from datetime import datetime
import uuid
import PyPDF2
import io
import json

# Configure page
st.set_page_config(
    page_title="ChatGPT Clone",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .user-message {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #0066cc;
    }
    
    .assistant-message {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #00cc66;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .sidebar-content {
        padding: 1rem;
    }
    
    .category-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background-color: #f8f9fa;
        border-radius: 5px;
        cursor: pointer;
    }
    
    .conversation-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
    }
    
    .conversation-item:hover {
        background-color: #f0f2f6;
        border-color: #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'categories' not in st.session_state:
    st.session_state.categories = ["General", "Work", "Learning", "Creative"]
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "General"

# OpenAI configuration
def init_openai():
    """Initialize OpenAI client"""
    # Check for API key in various locations
    api_key = None
    
    # Try environment variable first
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Try Streamlit secrets
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
    
    # If no API key found, ask user to input it
    if not api_key:
        with st.sidebar:
            st.error("OpenAI API key required")
            api_key = st.text_input("Enter your OpenAI API Key:", type="password")
            if api_key:
                st.success("API key provided!")
            else:
                st.warning("Please enter your OpenAI API key to continue")
                return False
    
    try:
        openai.api_key = api_key
        # Test the API key with a simple request
        openai.models.list()
        return True
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return False

# Local storage functions (using session state for demo)
def save_conversation_local(conversation_data):
    """Save conversation to local session state"""
    conversation_data['id'] = str(uuid.uuid4())
    conversation_data['created_at'] = datetime.now()
    conversation_data['updated_at'] = datetime.now()
    st.session_state.conversations.append(conversation_data)
    return conversation_data['id']

def load_conversations_local(category=None):
    """Load conversations from local session state"""
    conversations = st.session_state.conversations
    if category and category != "All":
        conversations = [conv for conv in conversations if conv.get("category") == category]
    return sorted(conversations, key=lambda x: x.get('created_at', datetime.now()), reverse=True)

def update_conversation_local(conversation_id, messages):
    """Update existing conversation in local session state"""
    for i, conv in enumerate(st.session_state.conversations):
        if conv.get('id') == conversation_id:
            st.session_state.conversations[i]['messages'] = messages
            st.session_state.conversations[i]['updated_at'] = datetime.now()
            return True
    return False

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
def get_chat_response(messages, uploaded_content=""):
    """Get response from OpenAI API"""
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
        
        # Get response from OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an error while processing your request. Please check your API key and try again."

# Main application
def main():
    # Initialize OpenAI
    openai_ready = init_openai()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 ChatGPT Clone</h1>
        <p>A modern AI assistant powered by OpenAI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for conversation management
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        st.header("💬 Conversations")
        
        # New conversation button
        if st.button("➕ New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.rerun()
        
        # Category management
        st.subheader("📁 Categories")
        
        # Add new category
        with st.expander("Add New Category"):
            new_category = st.text_input("Category Name", placeholder="Enter category name")
            if st.button("Add Category") and new_category:
                if new_category not in st.session_state.categories:
                    st.session_state.categories.append(new_category)
                    st.success(f"Added category: {new_category}")
                    st.rerun()
                else:
                    st.warning("Category already exists!")
        
        # Category selection
        category_options = ["All"] + st.session_state.categories
        selected_category = st.selectbox("Filter by Category", category_options)
        
        # Save current conversation
        if st.session_state.messages:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save", use_container_width=True):
                    conversation_data = {
                        "user_id": st.session_state.user_id,
                        "title": st.session_state.messages[0]["content"][:50] + "..." if st.session_state.messages else "New Conversation",
                        "category": st.session_state.selected_category,
                        "messages": st.session_state.messages,
                    }
                    
                    if st.session_state.current_conversation_id:
                        # Update existing conversation
                        update_conversation_local(st.session_state.current_conversation_id, st.session_state.messages)
                        st.success("Updated!")
                    else:
                        # Save new conversation
                        conversation_id = save_conversation_local(conversation_data)
                        if conversation_id:
                            st.session_state.current_conversation_id = conversation_id
                            st.success("Saved!")
            
            with col2:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.current_conversation_id = None
                    st.rerun()
        
        # Load conversations
        st.subheader("📋 Saved Conversations")
        conversations = load_conversations_local(selected_category if selected_category != "All" else None)
        
        if conversations:
            for conv in conversations[:10]:  # Limit to recent 10
                title = conv.get("title", "Untitled")
                category = conv.get("category", "General")
                created = conv.get("created_at", datetime.now()).strftime("%m/%d %H:%M")
                
                if st.button(f"📄 {title[:25]}...", key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.messages = conv.get("messages", [])
                    st.session_state.current_conversation_id = conv["id"]
                    st.session_state.selected_category = category
                    st.rerun()
                
                st.caption(f"🏷️ {category} • 📅 {created}")
        else:
            st.info("No saved conversations yet")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main chat interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # File upload section
        st.subheader("📎 Upload Content")
        uploaded_file = st.file_uploader(
            "Upload a file to include in your conversation",
            type=['txt', 'pdf'],
            help="Upload text files or PDFs to provide context for your questions"
        )
        
        uploaded_content = ""
        if uploaded_file:
            with st.spinner("Processing file..."):
                if uploaded_file.type == "application/pdf":
                    uploaded_content = process_pdf(uploaded_file)
                else:
                    uploaded_content = process_text_file(uploaded_file)
                
                if uploaded_content:
                    st.success(f"✅ File processed: {len(uploaded_content)} characters")
                    with st.expander("📄 View uploaded content"):
                        st.text_area("Content", uploaded_content[:1000] + "..." if len(uploaded_content) > 1000 else uploaded_content, height=200, disabled=True)
        
        # Display chat messages
        st.subheader("💬 Chat")
        
        # Chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>You:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-message">
                        <strong>Assistant:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        if prompt := st.chat_input("Type your message here...", disabled=not openai_ready):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Get AI response
            with st.spinner("Thinking..."):
                response = get_chat_response(st.session_state.messages, uploaded_content)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Category selection for new messages
        st.subheader("🏷️ Current Category")
        st.session_state.selected_category = st.selectbox(
            "Category for this conversation",
            st.session_state.categories,
            index=st.session_state.categories.index(st.session_state.selected_category) if st.session_state.selected_category in st.session_state.categories else 0
        )
        
        # Conversation stats
        st.subheader("📊 Stats")
        st.metric("Messages", len(st.session_state.messages))
        if st.session_state.messages:
            word_count = sum(len(msg["content"].split()) for msg in st.session_state.messages)
            st.metric("Total Words", word_count)
        
        # Help section
        st.subheader("ℹ️ Help")
        with st.expander("How to use"):
            st.markdown("""
            **Getting Started:**
            1. Enter your OpenAI API key in the sidebar
            2. Type a message in the chat input
            3. Upload files for context (optional)
            4. Save conversations with categories
            
            **Features:**
            - 💬 Real-time chat with GPT
            - 📁 Organize with categories
            - 📎 Upload PDF/text files
            - 💾 Save conversation history
            - 🔍 Filter saved conversations
            """)
        
        # API key status
        st.subheader("🔑 API Status")
        if openai_ready:
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ API Key Required")

if __name__ == "__main__":
    main()
