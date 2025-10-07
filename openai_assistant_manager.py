"""
OpenAI Assistant Manager
Implements the optimal OpenAI Assistants API pattern:
1. Create Assistant once
2. Create Thread per conversation
3. Add Messages to thread
4. Create Run and poll
5. List Messages for response
"""

import openai
import time
import json
from typing import Dict, List, Optional
from datetime import datetime

class OpenAIAssistantManager:
    def __init__(self, api_key: str):
        clean_api_key = api_key.strip() if api_key else ""
        self.client = openai.OpenAI(api_key=clean_api_key)
        self.assistant_id = None
        
    def create_assistant(self) -> str:
        """Step 1: Create an Assistant once and reuse it"""
        if self.assistant_id:
            return self.assistant_id
            
        try:
            assistant = self.client.beta.assistants.create(
                name="AI BOOST Assistant",
                instructions="""You are AI BOOST, a helpful and intelligent AI assistant. 
                
You should:
- Provide clear, accurate, and helpful responses
- Remember the conversation context from previous messages
- Be engaging and conversational
- Format your responses clearly with appropriate line breaks
- Use markdown formatting when helpful for structure
                
You are knowledgeable, friendly, and always aim to be as helpful as possible.""",
                model="gpt-4o",
                tools=[]
            )
            self.assistant_id = assistant.id
            print(f"✅ Created Assistant: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            print(f"❌ Error creating assistant: {e}")
            raise
    
    def create_thread(self) -> Dict:
        """Step 2: Create a Thread when a user starts a chat"""
        try:
            thread = self.client.beta.threads.create()
            thread_id = thread.id
            print(f"✅ Created Thread: {thread_id}")
            
            return {
                "success": True,
                "thread_id": thread_id
            }
            
        except Exception as e:
            print(f"❌ Error creating thread: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_message_to_thread(self, thread_id: str, content: str, role: str = "user") -> Dict:
        """Step 3: Add Messages to that thread as the user types"""
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
            print(f"✅ Added {role} message: {message.id} to thread: {thread_id}")
            print(f"🆔🆔🆔 MESSAGE ID: {message.id} 🆔🆔🆔")
            print(f"📝 Content: {content[:50]}...")
            print(f"🧵 Thread: {thread_id}")
            print("=" * 80)
            
            return {
                "success": True,
                "message_id": message.id,
                "content": content,
                "role": role,
                "created_at": datetime.fromtimestamp(message.created_at).isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error adding message to thread: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_and_poll_run(self, thread_id: str) -> Dict:
        """Step 4: Create a Run on the thread with assistant_id and poll until completed"""
        try:
            # Ensure we have an assistant
            if not self.assistant_id:
                self.create_assistant()
            
            # Create run
            create_start = time.time()
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )
            create_time = time.time() - create_start
            print(f"✅ Created Run: {run.id} (took {create_time:.2f}s)")
            
            # Poll until completed with timeout and optimized intervals
            max_wait_time = 60  # 60 seconds timeout
            start_time = time.time()
            last_status = None
            poll_count = 0
            
            while run.status in ["queued", "in_progress"]:
                # Check timeout
                if time.time() - start_time > max_wait_time:
                    print(f"⏰ Run timeout after {max_wait_time} seconds")
                    return {
                        "success": False,
                        "error": f"Run timed out after {max_wait_time} seconds"
                    }
                
                # Log status changes
                if run.status != last_status:
                    elapsed = time.time() - start_time
                    print(f"🔄 Run status: {run.status} (after {elapsed:.2f}s)")
                    last_status = run.status
                
                # Optimized polling intervals: start fast, then slow down
                poll_count += 1
                if poll_count <= 3:
                    sleep_time = 0.5  # First 3 polls: 0.5 seconds
                elif poll_count <= 10:
                    sleep_time = 1.0  # Next 7 polls: 1 second
                else:
                    sleep_time = 2.0  # After that: 2 seconds
                
                time.sleep(sleep_time)
                
                # Retrieve updated run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            total_time = time.time() - start_time
            if run.status == "completed":
                print(f"✅ Run completed: {run.id} (total time: {total_time:.2f}s)")
                return {
                    "success": True,
                    "run_id": run.id,
                    "status": "completed",
                    "total_time": total_time
                }
            else:
                error_msg = f"Run failed with status: {run.status}"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg += f" - {run.last_error.get('message', '')}"
                
                print(f"❌ {error_msg} (after {total_time:.2f}s)")
                return {
                    "success": False,
                    "error": error_msg,
                    "status": run.status,
                    "total_time": total_time
                }
                
        except Exception as e:
            print(f"❌ Error in create_and_poll_run: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_latest_assistant_message(self, thread_id: str) -> Dict:
        """Step 5: List Messages from the thread and get the assistant's reply"""
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )
            
            if messages.data:
                latest_message = messages.data[0]
                if latest_message.role == "assistant":
                    content = latest_message.content[0].text.value if latest_message.content else ""
                    print(f"✅ Retrieved assistant message: {latest_message.id}")
                    print(f"🆔🆔🆔 ASSISTANT MESSAGE ID: {latest_message.id} 🆔🆔🆔")
                    print(f"📝 Assistant Response: {content[:100]}...")
                    print(f"🧵 Thread: {thread_id}")
                    print("=" * 80)
                    
                    return {
                        "success": True,
                        "message_id": latest_message.id,
                        "content": content,
                        "created_at": datetime.fromtimestamp(latest_message.created_at).isoformat()
                    }
            
            return {
                "success": False,
                "error": "No assistant message found"
            }
            
        except Exception as e:
            print(f"❌ Error getting latest assistant message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_conversation_history(self, thread_id: str, limit: int = 50) -> Dict:
        """Get full conversation history from thread"""
        try:
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="asc",  # Chronological order
                limit=limit
            )
            
            conversation = []
            for message in messages.data:
                conversation.append({
                    "message_id": message.id,
                    "role": message.role,
                    "content": message.content[0].text.value if message.content else "",
                    "created_at": datetime.fromtimestamp(message.created_at).isoformat()
                })
            
            print(f"✅ Retrieved {len(conversation)} messages from thread: {thread_id}")
            return {
                "success": True,
                "messages": conversation,
                "count": len(conversation)
            }
            
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def complete_chat_flow(self, user_message: str, thread_id: str = None) -> Dict:
        """Complete optimal chat flow: Create thread if needed, add message, run, get response"""
        try:
            flow_start_time = time.time()
            print(f"🤖 Executing optimal OpenAI Assistants API flow...")
            
            # Step 2: Create thread if new conversation
            if not thread_id:
                thread_result = self.create_thread()
                if not thread_result["success"]:
                    return thread_result
                thread_id = thread_result["thread_id"]
            
            # Step 3: Add user message to thread
            user_msg_result = self.add_message_to_thread(thread_id, user_message, "user")
            if not user_msg_result["success"]:
                return user_msg_result
            
            # Step 4: Create and poll run
            run_result = self.create_and_poll_run(thread_id)
            if not run_result["success"]:
                return run_result
            
            # Step 5: Get assistant's response
            assistant_msg_result = self.get_latest_assistant_message(thread_id)
            if not assistant_msg_result["success"]:
                return assistant_msg_result
            
            total_flow_time = time.time() - flow_start_time
            print(f"✅ Complete chat flow successful for thread: {thread_id} (total: {total_flow_time:.2f}s)")
            print("\n" + "🆔" * 50)
            print("📋 OPENAI MESSAGE IDS SUMMARY:")
            print(f"   🧵 Thread ID: {thread_id}")
            print(f"   👤 User Message ID: {user_msg_result['message_id']}")
            print(f"   🤖 Assistant Message ID: {assistant_msg_result['message_id']}")
            print(f"   ⚡ Run ID: {run_result['run_id']}")
            print("🆔" * 50 + "\n")
            
            return {
                "success": True,
                "thread_id": thread_id,
                "user_message_id": user_msg_result["message_id"],
                "assistant_message_id": assistant_msg_result["message_id"],
                "response": assistant_msg_result["content"],
                "run_id": run_result["run_id"],
                "timing": {
                    "total_flow_time": total_flow_time,
                    "run_time": run_result.get("total_time", 0)
                },
                "message_ids": {
                    "user_message_id": user_msg_result["message_id"],
                    "assistant_message_id": assistant_msg_result["message_id"]
                }
            }
            
        except Exception as e:
            print(f"❌ Error in complete_chat_flow: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_messages(self, thread_id: str) -> Dict:
        """List messages from a thread for conversation restoration"""
        try:
            print(f"📋 Listing messages from thread: {thread_id}")
            
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="asc"  # Get messages in chronological order (oldest first)
            )
            
            message_list = []
            for message in messages.data:
                message_content = ""
                if message.content and len(message.content) > 0:
                    # Handle text content
                    if hasattr(message.content[0], 'text') and message.content[0].text:
                        message_content = message.content[0].text.value
                
                message_list.append({
                    "id": message.id,
                    "role": message.role,
                    "content": [{"text": {"value": message_content}}],
                    "created_at": message.created_at,
                    "assistant_id": getattr(message, 'assistant_id', None),
                    "run_id": getattr(message, 'run_id', None)
                })
            
            print(f"✅ Retrieved {len(message_list)} messages from thread")
            return {
                "success": True,
                "messages": message_list,
                "thread_id": thread_id,
                "total": len(message_list)
            }
            
        except Exception as e:
            print(f"❌ Error listing messages from thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
