import streamlit as st
import openai

st.set_page_config(page_title="AI Chat")

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI Chat")

# API Key input
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

if api_key:
    st.success("✅ API Key entered!")
    
    # Display messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.write(f"**You:** {msg['content']}")
        else:
            st.write(f"**AI:** {msg['content']}")
    
    # Chat input
    if user_input := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            # Call OpenAI
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            
            ai_response = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.warning("Please enter your OpenAI API key above to start chatting.")
