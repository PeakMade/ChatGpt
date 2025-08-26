"""
Chat router for handling conversations with OpenAI API.
"""
from fastapi import APIRouter, HTTPException, Depends
import openai
from models import ChatRequest, ChatResponse, Conversation, Message
from auth import verify_token
from database import get_database
from config import settings
import uuid
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])

# Set OpenAI API key
openai.api_key = settings.openai_api_key

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    try:
        # Get or create conversation
        if chat_request.conversation_id:
            conversation = await db.conversations.find_one({"_id": chat_request.conversation_id})
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
                user_id=current_user,
                messages=[]
            )
            await db.conversations.insert_one(conversation.dict(by_alias=True))
        
        # Add user message to conversation
        user_message = Message(role="user", content=chat_request.message)
        
        # Prepare messages for OpenAI API
        messages = []
        if conversation.get("messages"):
            for msg in conversation["messages"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add uploaded content if present
        content = chat_request.message
        if chat_request.uploaded_content:
            content += f"\n\nUploaded content:\n{chat_request.uploaded_content}"
        
        messages.append({"role": "user", "content": content})
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        
        assistant_response = response.choices[0].message.content
        assistant_message = Message(role="assistant", content=assistant_response)
        
        # Update conversation with both messages
        await db.conversations.update_one(
            {"_id": conversation_id if not chat_request.conversation_id else chat_request.conversation_id},
            {
                "$push": {
                    "messages": {
                        "$each": [user_message.dict(), assistant_message.dict()]
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return ChatResponse(
            response=assistant_response,
            conversation_id=conversation_id if not chat_request.conversation_id else chat_request.conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
