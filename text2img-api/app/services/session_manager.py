import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import logging

from app.config import settings
from app.models.schemas import SessionInfo

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.data_path = Path(settings.data_path)
        self.sessions_file = self.data_path / "sessions.json"
        self.sessions = self._load_sessions()
    
    def create_session(self, session_id: str) -> bool:
        """
        Create a new session.
        """
        try:
            session_info = SessionInfo(
                session_id=session_id,
                created_at=datetime.utcnow(),
                images_generated=0,
                last_activity=datetime.utcnow()
            )
            
            self.sessions[session_id] = session_info.dict()
            self._save_sessions()
            
            logger.info(f"Created session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information.
        """
        try:
            if session_id in self.sessions:
                session_data = self.sessions[session_id]
                return SessionInfo(**session_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """
        Get all sessions.
        """
        try:
            sessions = []
            for session_data in self.sessions.values():
                sessions.append(SessionInfo(**session_data))
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get all sessions: {e}")
            return []
    
    def update_session(self, session_id: str, action: str) -> bool:
        """
        Update session activity.
        """
        try:
            if session_id in self.sessions:
                session_data = self.sessions[session_id]
                session_data["last_activity"] = datetime.utcnow().isoformat()
                
                if action == "image_generated":
                    session_data["images_generated"] += 1
                
                self.sessions[session_id] = session_data
                self._save_sessions()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        """
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self._save_sessions()
                logger.info(f"Deleted session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def delete_all_sessions(self) -> bool:
        """
        Delete all sessions.
        """
        try:
            self.sessions.clear()
            self._save_sessions()
            logger.info("Deleted all sessions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete all sessions: {e}")
            return False
    
    def _load_sessions(self) -> Dict:
        """
        Load sessions from file.
        """
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            return {}
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}
    
    def _save_sessions(self) -> bool:
        """
        Save sessions to file.
        """
        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
            return False
