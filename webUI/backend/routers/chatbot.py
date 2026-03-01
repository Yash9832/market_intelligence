"""
Chatbot router for handling chat interactions and financial analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import APIResponse
from services.chatbot_service import chatbot_service

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]] = []
    chart_data: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=APIResponse)
async def chat_message(request: ChatMessage):
    """
    Process a chat message and return AI response with financial data
    """
    try:
        # Process the message
        result = await chatbot_service.process_message(
            message=request.message,
            conversation_history=request.conversation_history or []
        )
        
        return APIResponse(
            success=True,
            message="Chat response generated successfully",
            data=result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/extract-entities", response_model=APIResponse)
async def extract_entities(request: dict):
    """
    Extract named entities from text for financial analysis
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        from services.ner_service import ner_service
        result = ner_service.extract_entities(text)
        
        return APIResponse(
            success=True,
            message="Entity extraction completed",
            data=result
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")

@router.get("/health", response_model=APIResponse)
async def chatbot_health():
    """
    Health check for chatbot service
    """
    try:
        return APIResponse(
            success=True,
            message="Chatbot service is healthy",
            data={"status": "active", "tools_available": ["ner", "stock_data", "stock_analysis"]}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")