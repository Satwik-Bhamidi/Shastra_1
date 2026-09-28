from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from db.db_init import get_db, DatabaseManager
from auth.passwords import hash_password, verify_password, validate_password_strength
from auth.session import (
    get_session_manager, 
    SessionManager as AuthSessionManager,
    Session
)
from auth.permissions import (
    Permission, 
    Roles,
    has_permission, 
    require_permission,
    require_admin,
    AuthorizationError
)
from auth.bootstrap import bootstrap_application, BootstrapResult


class AuthManager:
    _instance: Optional['AuthManager'] = None
    
    def __new__(cls) -> 'AuthManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._db: DatabaseManager = get_db()
        self._session_mgr: AuthSessionManager = get_session_manager()
    
    def initialize(self) -> BootstrapResult:
        """
        Initialize the authentication system.
        Should be called on application startup.
        
        Returns:
            BootstrapResult: Result of initialization
        """
        return bootstrap_application()
    
    #Authentication
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Session]]:
        # Input validation
        if not username or not password:
            self._log_auth_failure(username, "Empty credentials")
            return False, "Username and password are required", None
        
        # Fetch user
        user = self._db.get_user_by_username(username)
        
        if not user:
            self._log_auth_failure(username, "User not found")
            return False, "Invalid username or password", None
        
        # Check if user is active
        if not user.get('is_active', False):
            self._log_auth_failure(username, "Account disabled")
            return False, "Account is disabled. Contact administrator.", None
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            self._log_auth_failure(username, "Invalid password")
            return False, "Invalid username or password", None
        
        # Create session
        session = self._session_mgr.create_session(
            user_id=user['id'],
            username=user['username'],
            role=user['role'],
            must_change_password=bool(user.get('must_change_password', 0))
        )
        
        # Update last login
        self._db.update_last_login(user['id'])
        
        # Log successful login
        self._db.log_audit(
            action="LOGIN_SUCCESS",
            user_id=user['id'],
            username=username,
            details=f"Role: {user['role']}"
        )
        
        return True, "Login successful", session
    
    def logout(self) -> None:
        session = self._session_mgr.current_session
        if session:
            self._db.log_audit(
                action="LOGOUT",
                user_id=session.user_id,
                username=session.username
            )
        self._session_mgr.clear_session()
    
    def _log_auth_failure(self, username: str, reason: str) -> None:
        """Log authentication failure to audit log."""
        self._db.log_audit(
            action="LOGIN_FAILURE",
            username=username,
            details=reason
        )
    
    # user management
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str
    ) -> Tuple[bool, str]:
        # Authorization check
        if not has_permission(Permission.CREATE_USER):
            self._log_unauthorized_action("CREATE_USER", username)
            return False, "Permission denied: Cannot create users"
        
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if role not in Roles.ALL_ROLES:
            return False, f"Invalid role. Must be one of: {', '.join(Roles.ALL_ROLES)}"
        
        # Validate password strength
        is_valid, error = validate_password_strength(password)
        if not is_valid:
            return False, error
        
        # Check if username exists
        if self._db.get_user_by_username(username):
            return False, "Username already exists"
        
        # Hash password and create user
        password_hash = hash_password(password)
        user_id = self._db.create_user(
            username=username,
            password_hash=password_hash,
            role=role,
            must_change_password=False
        )
        
        if user_id:
            # Log user creation
            session = self._session_mgr.current_session
            self._db.log_audit(
                action="USER_CREATED",
                user_id=session.user_id if session else None,
                username=session.username if session else "System",
                details=f"Created user: {username} with role: {role}"
            )
            return True, f"User '{username}' created successfully"
        
        return False, "Failed to create user"
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        if not has_permission(Permission.VIEW_USERS):
            return []
        return self._db.get_all_users()
    
    def update_user_role(self, user_id: int, new_role: str) -> Tuple[bool, str]:
        if not has_permission(Permission.MODIFY_USER):
            self._log_unauthorized_action("MODIFY_USER_ROLE", str(user_id))
            return False, "Permission denied"
        
        if new_role not in Roles.ALL_ROLES:
            return False, f"Invalid role. Must be one of: {', '.join(Roles.ALL_ROLES)}"
        
        # Get target user
        target_user = self._db.get_user_by_id(user_id)
        if not target_user:
            return False, "User not found"
        
        # Prevent removing last admin
        if target_user['role'] == Roles.ADMIN and new_role != Roles.ADMIN:
            if self._db.count_admins() <= 1:
                return False, "Cannot remove the last admin"
        
        if self._db.update_user_role(user_id, new_role):
            session = self._session_mgr.current_session
            self._db.log_audit(
                action="ROLE_CHANGED",
                user_id=session.user_id if session else None,
                username=session.username if session else "System",
                details=f"User {target_user['username']}: {target_user['role']} -> {new_role}"
            )
            return True, "Role updated successfully"
        
        return False, "Failed to update role"
    
    def update_user_status(self, user_id: int, is_active: bool) -> Tuple[bool, str]:
        if not has_permission(Permission.MODIFY_USER):
            self._log_unauthorized_action("MODIFY_USER_STATUS", str(user_id))
            return False, "Permission denied"
        
        target_user = self._db.get_user_by_id(user_id)
        if not target_user:
            return False, "User not found"
        
        # Prevent disabling yourself
        session = self._session_mgr.current_session
        if session and session.user_id == user_id and not is_active:
            return False, "Cannot disable your own account"
        
        # Prevent disabling last active admin
        if target_user['role'] == Roles.ADMIN and not is_active:
            if self._db.count_admins() <= 1:
                return False, "Cannot disable the last admin"
        
        if self._db.update_user_status(user_id, is_active):
            status_str = "enabled" if is_active else "disabled"
            self._db.log_audit(
                action="USER_STATUS_CHANGED",
                user_id=session.user_id if session else None,
                username=session.username if session else "System",
                details=f"User {target_user['username']} {status_str}"
            )
            return True, f"User {status_str} successfully"
        
        return False, "Failed to update user status"
    
    def reset_user_password(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        if not has_permission(Permission.RESET_PASSWORD):
            self._log_unauthorized_action("RESET_PASSWORD", str(user_id))
            return False, "Permission denied"
        
        # Validate password strength
        is_valid, error = validate_password_strength(new_password)
        if not is_valid:
            return False, error
        
        target_user = self._db.get_user_by_id(user_id)
        if not target_user:
            return False, "User not found"
        
        password_hash = hash_password(new_password)
        if self._db.update_user_password(user_id, password_hash):
            session = self._session_mgr.current_session
            self._db.log_audit(
                action="PASSWORD_RESET",
                user_id=session.user_id if session else None,
                username=session.username if session else "System",
                details=f"Password reset for user: {target_user['username']}"
            )
            return True, "Password reset successfully"
        
        return False, "Failed to reset password"
    
    def change_own_password(
        self,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, str]:
        session = self._session_mgr.current_session
        if not session:
            return False, "Not authenticated"
        
        # Get user from database
        user = self._db.get_user_by_id(session.user_id)
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not verify_password(current_password, user['password_hash']):
            self._db.log_audit(
                action="PASSWORD_CHANGE_FAILED",
                user_id=session.user_id,
                username=session.username,
                details="Invalid current password"
            )
            return False, "Current password is incorrect"
        
        # Validate new password strength
        is_valid, error = validate_password_strength(new_password)
        if not is_valid:
            return False, error
        
        # Update password
        password_hash = hash_password(new_password)
        if self._db.update_user_password(session.user_id, password_hash):
            self._session_mgr.update_password_changed()
            self._db.log_audit(
                action="PASSWORD_CHANGED",
                user_id=session.user_id,
                username=session.username,
                details="User changed their own password"
            )
            return True, "Password changed successfully"
        
        return False, "Failed to change password"
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """
        Delete a user (Admin only).
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not has_permission(Permission.DELETE_USER):
            self._log_unauthorized_action("DELETE_USER", str(user_id))
            return False, "Permission denied"
        
        target_user = self._db.get_user_by_id(user_id)
        if not target_user:
            return False, "User not found"
        
        # Prevent deleting yourself
        session = self._session_mgr.current_session
        if session and session.user_id == user_id:
            return False, "Cannot delete your own account"
        
        # Prevent deleting last admin
        if target_user['role'] == Roles.ADMIN:
            if self._db.count_admins() <= 1:
                return False, "Cannot delete the last admin"
        
        if self._db.delete_user(user_id):
            self._db.log_audit(
                action="USER_DELETED",
                user_id=session.user_id if session else None,
                username=session.username if session else "System",
                details=f"Deleted user: {target_user['username']}"
            )
            return True, f"User '{target_user['username']}' deleted successfully"
        
        return False, "Failed to delete user"
    
    def _log_unauthorized_action(self, action: str, target: str) -> None:
        """Log unauthorized action attempt."""
        session = self._session_mgr.current_session
        self._db.log_audit(
            action="UNAUTHORIZED_ATTEMPT",
            user_id=session.user_id if session else None,
            username=session.username if session else "Unknown",
            details=f"Attempted: {action} on {target}"
        )
    
    # audit log
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not has_permission(Permission.VIEW_AUDIT_LOG):
            return []
        return self._db.get_audit_log(limit=limit)
        
    @property
    def current_session(self) -> Optional[Session]:
        """Get current session."""
        return self._session_mgr.current_session
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self._session_mgr.is_authenticated
    
    @property
    def current_user(self) -> Optional[Dict[str, Any]]:
        """Get current user's data."""
        session = self._session_mgr.current_session
        if session:
            return self._db.get_user_by_id(session.user_id)
        return None
    
    def must_change_password(self) -> bool:
        """Check if current user must change password."""
        session = self._session_mgr.current_session
        return session is not None and session.must_change_password


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get the global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
