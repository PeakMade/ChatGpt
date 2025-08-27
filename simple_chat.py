import streamlit as st
import openai
import os

# Page config
st.set_page_config(page_title="AI Chat", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for API key
with st.sidebar:
    st.title("Settings")
    api_key = st.text_area("Enter your OpenAI API Key:", height=100)
    if api_key:
        st.success("API Key entered!")

# Main chat
st.title("AI Chat Assistant")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    if not api_key:
        st.error("Please enter your API key in the sidebar!")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        try:
            client = openai.OpenAI(api_key=api_key)
            
            messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            with st.chat_message("assistant"):
                st.write(ai_response)
        
        except Exception as e:
            st.error(f"Error: {e}")
