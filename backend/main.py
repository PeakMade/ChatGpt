"""
FastAPI main entry point for ChatGPT clone backend.
Handles API routing, authentication, chat, file upload, and MongoDB connection.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers will be included here
# from .routers import auth, chat, upload, dashboard
# app.include_router(auth.router)
# app.include_router(chat.router)
# app.include_router(upload.router)
# app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "ChatGPT API is running"}
