"""
SHASTRA Permissions & RBAC Module
=
Role-Based Access Control (RBAC) implementation.
Authorization is enforced in backend logic, not just UI.
"""

from enum import Enum, auto
from typing import Callable, Optional, List, TypeVar, Any
from functools import wraps
from auth.session import get_session_manager, get_current_session


class Roles:
    """Role constants for SHASTRA."""
    ADMIN = "Admin"
    OPERATOR = "Operator"
    
    ALL_ROLES = [ADMIN, OPERATOR]


class Permission(Enum):
    """
    Enumeration of all permissions in SHASTRA.
    Each permission maps to specific actions.
    """
    # User Management Permissions
    CREATE_USER = auto()
    DELETE_USER = auto()
    MODIFY_USER = auto()
    VIEW_USERS = auto()
    RESET_PASSWORD = auto()
    
    # Settings Permissions
    VIEW_SETTINGS = auto()
    MODIFY_SETTINGS = auto()
    
    # Application Feature Permissions
    USE_APPLICATION = auto()
    VIEW_AUDIT_LOG = auto()
    
    # System Permissions
    SYSTEM_ADMIN = auto()


# Permission mappings for each role
ROLE_PERMISSIONS = {
    Roles.ADMIN: {
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.MODIFY_USER,
        Permission.VIEW_USERS,
        Permission.RESET_PASSWORD,
        Permission.VIEW_SETTINGS,
        Permission.MODIFY_SETTINGS,
        Permission.USE_APPLICATION,
        Permission.VIEW_AUDIT_LOG,
        Permission.SYSTEM_ADMIN,
    },
    Roles.OPERATOR: {
        Permission.VIEW_SETTINGS,
        Permission.USE_APPLICATION,
    }
}


def has_permission(permission: Permission) -> bool:
    """
    Check if the current session user has a specific permission.
    
    Args:
        permission: Permission to check
        
    Returns:
        bool: True if user has the permission
    """
    session = get_current_session()
    if not session or not session.is_authenticated:
        return False
    
    role_perms = ROLE_PERMISSIONS.get(session.role, set())
    return permission in role_perms


def has_any_permission(permissions: List[Permission]) -> bool:
    """
    Check if the current session user has any of the given permissions.
    
    Args:
        permissions: List of permissions to check
        
    Returns:
        bool: True if user has at least one of the permissions
    """
    return any(has_permission(p) for p in permissions)


def has_all_permissions(permissions: List[Permission]) -> bool:
    """
    Check if the current session user has all of the given permissions.
    
    Args:
        permissions: List of permissions to check
        
    Returns:
        bool: True if user has all of the permissions
    """
    return all(has_permission(p) for p in permissions)


def is_admin() -> bool:
    """
    Check if the current session user is an Admin.
    
    Returns:
        bool: True if user is Admin
    """
    session_mgr = get_session_manager()
    return session_mgr.is_admin()


def is_operator() -> bool:
    """
    Check if the current session user is an Operator.
    
    Returns:
        bool: True if user is Operator
    """
    session_mgr = get_session_manager()
    return session_mgr.is_operator()


def get_role_display_name(role: str) -> str:
    """
    Get human-readable display name for a role.
    
    Args:
        role: Role identifier
        
    Returns:
        str: Display name
    """
    return role  # For SHASTRA, roles are already display-friendly


class AuthorizationError(Exception):
    """Exception raised when authorization fails."""
    def __init__(self, message: str = "Access denied"):
        self.message = message
        super().__init__(self.message)


# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


def require_permission(permission: Permission) -> Callable[[F], F]:
    """
    Decorator to require a specific permission for a function.
    
    Args:
        permission: Required permission
        
    Returns:
        Callable: Decorated function
        
    Raises:
        AuthorizationError: If user lacks the required permission
        
    Example:
        @require_permission(Permission.MODIFY_SETTINGS)
        def change_setting(key, value):
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not has_permission(permission):
                raise AuthorizationError(
                    f"Permission denied: {permission.name} required"
                )
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def require_admin(func: F) -> F:
    """
    Decorator to require Admin role for a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
        
    Raises:
        AuthorizationError: If user is not an Admin
        
    Example:
        @require_admin
        def delete_user(user_id):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin():
            raise AuthorizationError("Admin access required")
        return func(*args, **kwargs)
    return wrapper  # type: ignore


def check_authorization(
    permission: Optional[Permission] = None,
    admin_only: bool = False
) -> tuple[bool, str]:
    """
    Check authorization and return result with error message.
    Useful for UI-level checks before performing actions.
    
    Args:
        permission: Optional specific permission to check
        admin_only: If True, require Admin role
        
    Returns:
        tuple[bool, str]: (is_authorized, error_message)
    """
    session = get_current_session()
    
    if not session or not session.is_authenticated:
        return False, "Not authenticated"
    
    if admin_only and not session.is_admin():
        return False, "Admin access required"
    
    if permission and not has_permission(permission):
        return False, f"Permission denied: {permission.name}"
    
    return True, ""


def can_manage_users() -> bool:
    """Check if current user can manage other users."""
    return has_permission(Permission.CREATE_USER) or has_permission(Permission.MODIFY_USER)


def can_modify_settings() -> bool:
    """Check if current user can modify application settings."""
    return has_permission(Permission.MODIFY_SETTINGS)


def can_view_audit_log() -> bool:
    """Check if current user can view audit logs."""
    return has_permission(Permission.VIEW_AUDIT_LOG)
