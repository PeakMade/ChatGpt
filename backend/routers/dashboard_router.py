"""
Dashboard router for managing conversations and categories.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models import Conversation, Category
from auth import verify_token
from database import get_database
from bson import ObjectId

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    conversations = await db.conversations.find({"user_id": current_user}).to_list(100)
    return conversations

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    conversation = await db.conversations.find_one({
        "_id": conversation_id,
        "user_id": current_user
    })
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    result = await db.conversations.delete_one({
        "_id": conversation_id,
        "user_id": current_user
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}

@router.post("/categories")
async def create_category(
    name: str,
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    category = Category(name=name, user_id=current_user)
    result = await db.categories.insert_one(category.dict(by_alias=True))
    return {"id": str(result.inserted_id), "name": name}

@router.get("/categories", response_model=List[Category])
async def get_categories(
    current_user: str = Depends(verify_token),
    db = Depends(get_database)
):
    categories = await db.categories.find({"user_id": current_user}).to_list(100)
    return categories
