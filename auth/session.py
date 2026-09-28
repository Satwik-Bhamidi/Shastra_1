"""
SHASTRA Session Management Module
=
In-memory session management for offline authentication.
No persistence, no tokens - cleared on logout and app exit.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Session:
    """
    Represents an authenticated user session.
    All session data is held in memory only.
    """
    user_id: int
    username: str
    role: str
    is_authenticated: bool = True
    login_time: datetime = field(default_factory=datetime.now)
    must_change_password: bool = False
    
    def is_admin(self) -> bool:
        """Check if session user is an admin."""
        return self.role == "Admin"
    
    def is_operator(self) -> bool:
        """Check if session user is an operator."""
        return self.role == "Operator"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'is_authenticated': self.is_authenticated,
            'login_time': self.login_time.isoformat(),
            'must_change_password': self.must_change_password
        }


class SessionManager:
    """
    Manages the current user session.
    Singleton pattern ensures single session across application.
    """
    
    _instance: Optional['SessionManager'] = None
    
    def __new__(cls) -> 'SessionManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._session = None
        return cls._instance
    
    @property
    def current_session(self) -> Optional[Session]:
        """Get the current session."""
        return self._session
    
    @property
    def is_authenticated(self) -> bool:
        """Check if there is an active authenticated session."""
        return self._session is not None and self._session.is_authenticated
    
    @property
    def current_user_id(self) -> Optional[int]:
        """Get current user ID if authenticated."""
        return self._session.user_id if self._session else None
    
    @property
    def current_username(self) -> Optional[str]:
        """Get current username if authenticated."""
        return self._session.username if self._session else None
    
    @property
    def current_role(self) -> Optional[str]:
        """Get current user's role if authenticated."""
        return self._session.role if self._session else None
    
    def create_session(
        self,
        user_id: int,
        username: str,
        role: str,
        must_change_password: bool = False
    ) -> Session:
        """
        Create a new session for an authenticated user.
        
        Args:
            user_id: Authenticated user's ID
            username: Authenticated user's username
            role: User's role ('Admin' or 'Operator')
            must_change_password: Whether user must change password
            
        Returns:
            Session: The created session object
        """
        self._session = Session(
            user_id=user_id,
            username=username,
            role=role,
            is_authenticated=True,
            must_change_password=must_change_password
        )
        return self._session
    
    def clear_session(self) -> None:
        """
        Clear the current session (logout).
        All session data is destroyed.
        """
        self._session = None
    
    def is_admin(self) -> bool:
        """Check if current session user is an admin."""
        return self._session is not None and self._session.is_admin()
    
    def is_operator(self) -> bool:
        """Check if current session user is an operator."""
        return self._session is not None and self._session.is_operator()
    
    def update_password_changed(self) -> None:
        """Mark that user has changed their password."""
        if self._session:
            self._session.must_change_password = False


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return _session_manager


def get_current_session() -> Optional[Session]:
    """Get the current active session."""
    return _session_manager.current_session


def is_authenticated() -> bool:
    """Check if there is an authenticated session."""
    return _session_manager.is_authenticated


def get_current_user_id() -> Optional[int]:
    """Get current user ID if authenticated."""
    return _session_manager.current_user_id


def get_current_username() -> Optional[str]:
    """Get current username if authenticated."""
    return _session_manager.current_username


def get_current_role() -> Optional[str]:
    """Get current user's role if authenticated."""
    return _session_manager.current_role
