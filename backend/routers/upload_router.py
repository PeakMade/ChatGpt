"""
File upload router for handling text and PDF files.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import pdfplumber
from io import BytesIO

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    try:
        if file.content_type == "application/pdf":
            # Handle PDF files
            content = await file.read()
            text = ""
            with pdfplumber.open(BytesIO(content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return {"content": text, "type": "pdf"}
        
        elif file.content_type.startswith("text/"):
            # Handle text files
            content = await file.read()
            text = content.decode("utf-8")
            return {"content": text, "type": "text"}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
