"""
Modern ChatGPT Clone - Streamlit Application
Features: Chat interface, conversation history, file upload, categories, user auth
"""

import streamlit as st
import openai
import pymongo
from datetime import datetime
import hashlib
import bcrypt
import uuid
import PyPDF2
import io
import os
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="ChatGPT",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure sidebar stays expanded
if 'sidebar_state' not in st.session_state:
    st.session_state.sidebar_state = "expanded"

# Custom CSS for modern, clean design
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    
    /* Force sidebar to stay expanded */
    .css-1d391kg {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    .css-1lcbmhc {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    /* Sidebar styling */
    .stSidebar {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    .stSidebar > div {
        width: 350px !important;
        min-width: 350px !important;
    }
    
    .stTextInput > div > div > input {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px;
    }
    
    .stButton > button {
        background-color: #10a37f;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0d8a6b;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .user-message {
        background-color: #f1f3f4;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background-color: white;
        margin-right: 2rem;
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
    
    h1 {
        color: #1f2937;
        font-weight: 600;
        margin-bottom: 2rem;
    }
    
    .conversation-item {
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        margin-bottom: 8px;
        cursor: pointer;
    }
    
    .conversation-item:hover {
        background-color: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
@st.cache_resource
def init_database():
    """Initialize MongoDB connection"""
    try:
        client = pymongo.MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
        db = client.chatgpt_clone
        return db
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(db, email: str, password: str) -> bool:
    """Create new user account"""
    try:
        # Check if user exists
        if db.users.find_one({"email": email}):
            return False
        
        user_data = {
            "user_id": str(uuid.uuid4()),
            "email": email,
            "password_hash": hash_password(password),
            "created_at": datetime.now(),
            "categories": ["General", "Work", "Personal"]
        }
        
        db.users.insert_one(user_data)
        return True
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def authenticate_user(db, email: str, password: str) -> Optional[Dict]:
    """Authenticate user and return user data"""
    try:
        user = db.users.find_one({"email": email})
        if user and verify_password(password, user["password_hash"]):
            return user
        return None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None

# File processing functions
def extract_text_from_pdf(file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_text_from_txt(file) -> str:
    """Extract text from uploaded text file"""
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        st.error(f"Error reading text file: {e}")
        return ""

# OpenAI integration
def get_chatgpt_response(messages: List[Dict], api_key: str) -> str:
    """Get response from OpenAI ChatGPT API"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Conversation management
def save_conversation(db, user_id: str, conversation_data: Dict) -> str:
    """Save conversation to database"""
    try:
        conversation_id = str(uuid.uuid4())
        conversation_data.update({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        
        db.conversations.insert_one(conversation_data)
        return conversation_id
    except Exception as e:
        st.error(f"Error saving conversation: {e}")
        return ""

def update_conversation(db, conversation_id: str, messages: List[Dict]):
    """Update existing conversation with new messages"""
    try:
        db.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "messages": messages,
                    "updated_at": datetime.now()
                }
            }
        )
    except Exception as e:
        st.error(f"Error updating conversation: {e}")

def get_user_conversations(db, user_id: str, category: str = None) -> List[Dict]:
    """Get user's conversations, optionally filtered by category"""
    try:
        query = {"user_id": user_id}
        if category and category != "All":
            query["category"] = category
        
        conversations = list(db.conversations.find(query).sort("updated_at", -1))
        return conversations
    except Exception as e:
        st.error(f"Error fetching conversations: {e}")
        return []

def add_user_category(db, user_id: str, category: str):
    """Add new category for user"""
    try:
        db.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"categories": category}}
        )
    except Exception as e:
        st.error(f"Error adding category: {e}")

# Main application
def main():
    # Force sidebar to stay expanded
    st.markdown("""
    <script>
    // Force sidebar to stay expanded
    setTimeout(function() {
        var sidebar = parent.document.querySelector('.css-1d391kg');
        if (sidebar) {
            sidebar.style.transform = 'translateX(0px)';
            sidebar.style.width = '350px';
        }
        
        var sidebarControl = parent.document.querySelector('[data-testid="collapsedControl"]');
        if (sidebarControl) {
            sidebarControl.style.display = 'none';
        }
    }, 100);
    </script>
    """, unsafe_allow_html=True)
    
    # Initialize database (optional - for persistence)
    db = init_database()
    # Note: Database connection warning removed - app works without MongoDB
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "categories" not in st.session_state:
        st.session_state.categories = ["General", "Work", "Personal", "Learning"]
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "sidebar_state" not in st.session_state:
        st.session_state.sidebar_state = "expanded"
    
    # Main application - no authentication required
    st.title("ChatGPT")
    
    # Sidebar for navigation and settings
    with st.sidebar:
        st.markdown("**ChatGPT Settings**")
        
        st.divider()
        
        # New conversation button
        if st.button("New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.current_conversation_id = None
            st.rerun()
        
        # Categories management
        st.markdown("**Categories**")
        
        # Add new category
        with st.expander("Add Category"):
            new_category = st.text_input("Category name")
            if st.button("Add") and new_category:
                if new_category not in st.session_state.categories:
                    st.session_state.categories.append(new_category)
                    st.success(f"Added category: {new_category}")
                    st.rerun()
                else:
                    st.warning("Category already exists!")
        
        # Category filter
        selected_category = st.selectbox("Filter by category", ["All"] + st.session_state.categories)
        
        # Conversation history
        st.markdown("**Conversation History**")
        
        # Simple session-based conversation storage
        for i, conv in enumerate(st.session_state.conversations[-10:]):  # Show last 10 conversations
            title = conv.get("title", "Untitled")[:25] + "..." if len(conv.get("title", "")) > 25 else conv.get("title", "Untitled")
            if st.button(f"{title}", key=f"conv_{i}", use_container_width=True):
                st.session_state.messages = conv.get("messages", [])
                st.session_state.current_conversation_id = conv.get("id")
                st.rerun()
    
    # Main chat interface
    # File upload section
    with st.expander("Upload Files (Optional)"):
        uploaded_files = st.file_uploader(
        "Choose files to include in your prompt",
        type=["txt", "pdf"],
        accept_multiple_files=True
    )
    
    uploaded_content = ""
    if uploaded_files:
        for file in uploaded_files:
            if file.type == "application/pdf":
                content = extract_text_from_pdf(file)
            else:
                content = extract_text_from_txt(file)
            
            uploaded_content += f"\n\n--- Content from {file.name} ---\n{content}"

    # Display chat messages
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.text_area("Type your message here...", height=100, key="chat_input")
    
    col_send, col_save = st.columns([1, 1])
    
    with col_send:
        if st.button("Send Message", use_container_width=True):
            if user_input and st.session_state.api_key:
                # Prepare message content
                full_message = user_input
                if uploaded_content:
                    full_message += uploaded_content
                
                # Add user message
                st.session_state.messages.append({"role": "user", "content": full_message})
                
                # Get ChatGPT response
                with st.spinner("Getting response..."):
                    response = get_chatgpt_response(st.session_state.messages, st.session_state.api_key)
                
                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Auto-save conversation
                if st.session_state.current_conversation_id:
                    update_conversation(db, st.session_state.current_conversation_id, st.session_state.messages)
                
                st.rerun()
            elif not st.session_state.api_key:
                st.error("OpenAI API key not found. Please check your environment configuration.")
    
    with col_save:
        if st.button("Save Conversation", use_container_width=True) and st.session_state.messages:
            # Save conversation form
            with st.form("save_conversation"):
                title = st.text_input("Conversation Title", value=f"Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                category = st.selectbox("Category", st.session_state.categories)
                
                if st.form_submit_button("Save"):
                    conversation_data = {
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "category": category,
                        "messages": st.session_state.messages,
                        "created_at": datetime.now()
                    }
                    
                    # Save to session state
                    st.session_state.conversations.append(conversation_data)
                    st.session_state.current_conversation_id = conversation_data["id"]
                    st.success("Conversation saved!")

if __name__ == "__main__":
    main()
