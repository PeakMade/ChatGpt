# Current API and Web Search Behavior

This document describes the current API surface and how the app retrieves current (post-training) information via web search.

## API Overview

### Core UI and Config
- GET / - serves the main UI and initializes session state.
- GET /api-key-status - reports whether an environment API key is available.
- GET /config - returns the current model, settings, and keyword info from external config.

### Chat
- POST /chat - primary chat endpoint. Validates input, checks whether web search is needed, then routes to either the web-search fallback or the Assistants flow.

### Conversation Management
- GET /api/conversations - list conversations with metadata (thread_id, user_id, timestamps, preview).
- GET /api/conversations/<conversation_id> - get a single conversation with messages.
- GET /api/conversations/<conversation_id>/messages - get conversation messages, optionally from the OpenAI thread if available.
- POST /api/conversations - create a new conversation.
- DELETE /api/conversations/<conversation_id> - delete a conversation.
- GET /api/conversations/search?q=... - search by title or message content.
- POST /api/conversations/<conversation_id>/switch - switch active conversation and optionally refresh messages from the OpenAI thread.

### Utilities
- POST /upload - upload PDF or TXT and return extracted text.
- POST /set-conversation-context - set session messages from the frontend.
- POST /clear_chat - clear session chat history.
- GET /get_messages - return current session messages and API key.

## How Current (Post-Training) Search Works

### 1) Keyword trigger
The app decides whether to use web search by checking the user message against configured keywords.

- Function: should_use_web_search(user_message)
- Source of keywords: config/model_config.ini, section [web_search_keywords]
- Loader: get_web_search_keywords() in config/config.py

If any keyword or phrase appears in the user message, web search is triggered. Otherwise, the response uses the standard chat model (training data only).

### 2) Routing decision
The /chat endpoint checks for web search first. If a match is found, it routes to the fallback flow that supports web search.

### 3) Live web search call
When web search is required, the app uses the OpenAI Responses API with a web_search tool:

- client.responses.create(..., tools=[{"type": "web_search"}], ...)
- Model is chosen from the config under web_search_model

This retrieves current information beyond the model training data.

### 4) Source formatting and URL removal
The response is cleaned before returning to the user:

- format_web_search_response() extracts citations and appends a Sources section.
- strip_urls_from_response() removes any URLs for a clean, link-free response.

## Configuration Notes

Key settings live in config/model_config.ini:

- [models] web_search_model = gpt-4o (default)
- [web_search_keywords] defines the trigger phrases for current information

You can update the keywords or web_search_model without changing any code.

## Quick Reference: Where It Is Implemented

- app_flask.py
  - should_use_web_search()
  - format_web_search_response()
  - get_chat_response_with_conversation()
  - POST /chat
- config/config.py
  - get_web_search_keywords()
  - get_model_for_task()
- config/model_config.ini
  - [web_search_keywords]
  - [models]
