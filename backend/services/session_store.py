"""Session management service for storing user sessions"""

import uuid
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionStore:
    """In-memory session store with expiration"""

    def __init__(self, timeout_minutes: int = 15):
        """
        Initialize session store.

        Args:
            timeout_minutes: Session expiration time in minutes
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout_seconds = timeout_minutes * 60
        logger.info(f"SessionStore initialized with {timeout_minutes}min timeout")

    def create_session(self, schema: Dict[str, Any]) -> str:
        """
        Create a new session and store schema.

        Args:
            schema: Parsed schema dictionary with tables

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        creation_time = time.time()
        expiry_time = creation_time + self.timeout_seconds

        self.sessions[session_id] = {
            "schema": schema,
            "created_at": creation_time,
            "expires_at": expiry_time,
            "last_accessed": creation_time,
            "query_count": 0,
        }

        logger.info(f"Created session {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data if not expired.

        Args:
            session_id: Session identifier

        Returns:
            Session data if valid, None if expired or not found
        """
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return None

        session = self.sessions[session_id]
        current_time = time.time()

        # Check expiration
        if current_time > session["expires_at"]:
            logger.info(f"Session {session_id} expired, removing")
            del self.sessions[session_id]
            return None

        # Update last accessed time
        session["last_accessed"] = current_time
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False

    def increment_query_count(self, session_id: str) -> bool:
        """
        Increment query count for a session.

        Args:
            session_id: Session identifier

        Returns:
            True if updated, False if session not found/expired
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session["query_count"] += 1
        return True

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        current_time = time.time()
        expired = [
            sid for sid, s in self.sessions.items()
            if current_time > s["expires_at"]
        ]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    def get_active_session_count(self) -> int:
        """Get count of active (non-expired) sessions"""
        self.cleanup_expired_sessions()
        return len(self.sessions)

    def session_exists(self, session_id: str) -> bool:
        """Check if a valid session exists"""
        return self.get_session(session_id) is not None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata (without schema data).

        Args:
            session_id: Session identifier

        Returns:
            Session info dict with timestamps and stats
        """
        session = self.get_session(session_id)
        if not session:
            return None

        created = datetime.fromtimestamp(session["created_at"])
        expires = datetime.fromtimestamp(session["expires_at"])

        return {
            "session_id": session_id,
            "created_at": created.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "query_count": session["query_count"],
            "table_count": len(session["schema"]),
        }
