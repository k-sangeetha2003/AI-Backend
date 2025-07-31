from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime

from app.models.schemas import SessionInfo
from app.services.session_manager import SessionManager

router = APIRouter()

session_manager = SessionManager()

@router.post("/sessions")
async def create_session():
    """
    Create a new session.
    """
    try:
        session_id = str(uuid.uuid4())
        session_manager.create_session(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """
    Get session information.
    """
    try:
        session_info = session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")
        return session_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions", response_model=List[SessionInfo])
async def get_all_sessions():
    """
    Get all sessions.
    """
    try:
        sessions = session_manager.get_all_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session.
    """
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "success": True,
            "message": "Session deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions")
async def delete_all_sessions():
    """
    Delete all sessions.
    """
    try:
        session_manager.delete_all_sessions()
        return {
            "success": True,
            "message": "All sessions deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
