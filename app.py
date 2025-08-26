"""
ChatGPT Clone - Streamlit Application
A modern, responsive web application that replicates ChatGPT functionality
"""

import streamlit as st
import openai
import pymongo
from datetime import datetime
import uuid
import os
from typing import List, Dict, Any
import PyPDF2
import io
import json
from bson import ObjectId

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
if 'current_conversation_id' not in st.session_state:
    st.session_state.current_conversation_id = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'categories' not in st.session_state:
    st.session_state.categories = ["General", "Work", "Learning", "Creative"]
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "General"

# Database connection
@st.cache_resource
def init_mongodb():
    """Initialize MongoDB connection"""
    try:
        # Use MongoDB Atlas connection string from environment variables
        mongo_uri = os.getenv("MONGODB_URI", "")
        if not mongo_uri:
            # Fall back to session state storage if no MongoDB
            st.warning("MongoDB not configured. Using session-based storage.")
            return None
            
        client = pymongo.MongoClient(mongo_uri)
        # Test the connection
        client.admin.command('ping')
        db = client.chatgpt_clone
        return db
    except Exception as e:
        st.warning(f"MongoDB connection failed, using session storage: {e}")
        return None

# OpenAI configuration
def init_openai():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except:
            api_key = ""
    
    if not api_key:
        st.error("❗ OpenAI API key is required for deployment.")
        st.info("💡 Set OPENAI_API_KEY in Azure App Service Configuration → Application Settings")
        st.stop()
    
    # Initialize OpenAI client with the new v1.0+ API
    client = openai.OpenAI(api_key=api_key)
    return client

# Database operations
def save_conversation(db, conversation_data):
    """Save conversation to MongoDB"""
    if db:
        try:
            conversations = db.conversations
            result = conversations.insert_one(conversation_data)
            return str(result.inserted_id)
        except Exception as e:
            st.error(f"Failed to save conversation: {e}")
            return None
    return None

def load_conversations(db, user_id, category=None):
    """Load conversations from MongoDB"""
    if db:
        try:
            conversations = db.conversations
            query = {"user_id": user_id}
            if category and category != "All":
                query["category"] = category
            
            results = conversations.find(query).sort("created_at", -1)
            return list(results)
        except Exception as e:
            st.error(f"Failed to load conversations: {e}")
            return []
    return []

def update_conversation(db, conversation_id, messages):
    """Update existing conversation"""
    if db:
        try:
            conversations = db.conversations
            conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$set": {
                        "messages": messages,
                        "updated_at": datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            st.error(f"Failed to update conversation: {e}")
            return False
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
def get_chat_response(client, messages, uploaded_content=""):
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
        
        # Get response from OpenAI using new client API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an error while processing your request."

# Main application
def main():
    # Initialize services
    db = init_mongodb()
    openai_client = init_openai()
    
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
        new_category = st.text_input("Add Category", placeholder="Enter category name")
        if st.button("Add") and new_category:
            if new_category not in st.session_state.categories:
                st.session_state.categories.append(new_category)
                st.success(f"Added category: {new_category}")
                st.rerun()
        
        # Category selection
        category_options = ["All"] + st.session_state.categories
        selected_category = st.selectbox("Filter by Category", category_options)
        
        # Save current conversation
        if st.session_state.messages and st.button("💾 Save Conversation"):
            if db:
                conversation_data = {
                    "user_id": st.session_state.user_id,
                    "title": st.session_state.messages[0]["content"][:50] + "..." if st.session_state.messages else "New Conversation",
                    "category": st.session_state.selected_category,
                    "messages": st.session_state.messages,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                if st.session_state.current_conversation_id:
                    # Update existing conversation
                    update_conversation(db, st.session_state.current_conversation_id, st.session_state.messages)
                    st.success("Conversation updated!")
                else:
                    # Save new conversation
                    conversation_id = save_conversation(db, conversation_data)
                    if conversation_id:
                        st.session_state.current_conversation_id = conversation_id
                        st.success("Conversation saved!")
        
        # Load conversations
        st.subheader("📋 Saved Conversations")
        conversations = load_conversations(db, st.session_state.user_id, selected_category if selected_category != "All" else None)
        
        for conv in conversations[:10]:  # Limit to recent 10
            with st.container():
                title = conv.get("title", "Untitled")
                category = conv.get("category", "General")
                created = conv.get("created_at", datetime.now()).strftime("%m/%d %H:%M")
                
                if st.button(f"📄 {title[:30]}...", key=f"conv_{conv['_id']}"):
                    st.session_state.messages = conv.get("messages", [])
                    st.session_state.current_conversation_id = str(conv["_id"])
                    st.session_state.selected_category = category
                    st.rerun()
                
                st.caption(f"🏷️ {category} • 📅 {created}")
        
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
                        st.text_area("Content", uploaded_content, height=200, disabled=True)
        
        # Display chat messages
        st.subheader("💬 Chat")
        
        # Chat history
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
        if prompt := st.chat_input("Type your message here...", disabled=not openai_client):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message immediately
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong><br>
                {prompt}
            </div>
            """, unsafe_allow_html=True)
            
            # Get AI response
            with st.spinner("Thinking..."):
                response = get_chat_response(openai_client, st.session_state.messages, uploaded_content)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Display assistant response
            st.markdown(f"""
            <div class="assistant-message">
                <strong>Assistant:</strong><br>
                {response}
            </div>
            """, unsafe_allow_html=True)
            
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Category selection for new messages
        st.subheader("🏷️ Current Category")
        st.session_state.selected_category = st.selectbox(
            "Category for this conversation",
            st.session_state.categories,
            index=st.session_state.categories.index(st.session_state.selected_category)
        )
        
        # Conversation stats
        st.subheader("📊 Stats")
        st.metric("Messages", len(st.session_state.messages))
        if st.session_state.messages:
            word_count = sum(len(msg["content"].split()) for msg in st.session_state.messages)
            st.metric("Total Words", word_count)
        
        # Keyboard shortcuts help
        st.subheader("⌨️ Shortcuts")
        st.markdown("""
        - **Ctrl+Enter**: Send message
        - **Ctrl+N**: New conversation
        - **Ctrl+S**: Save conversation
        """)

if __name__ == "__main__":
    main()
