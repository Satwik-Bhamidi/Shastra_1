from typing import Tuple, Optional
from core.app_paths import is_first_run, get_database_path
from db.db_init import get_db
from auth.passwords import hash_password, generate_temporary_password


# Default admin credentials
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_TEMP_PASSWORD = "Admin@123"  # Must be changed on first login


class BootstrapResult:
    """Result of bootstrap operation."""
    def __init__(
        self,
        success: bool,
        is_first_run: bool = False,
        default_password: Optional[str] = None,
        error: Optional[str] = None
    ):
        self.success = success
        self.is_first_run = is_first_run
        self.default_password = default_password
        self.error = error


def bootstrap_application() -> BootstrapResult:
    first_run = is_first_run()
    
    try:
        # Initialize database (creates schema if needed)
        db = get_db()
        
        # Check if this is first run (no users exist)
        has_users = db.has_users()
        
        if first_run or not has_users:
            # First run - no default admin created
            # First user to signup will be admin
            return BootstrapResult(
                success=True,
                is_first_run=True,
                default_password=None
            )
        
        # Database exists and has users
        return BootstrapResult(success=True, is_first_run=False)
        
    except Exception as e:
        return BootstrapResult(
            success=False,
            error=f"Bootstrap failed: {str(e)}"
        )


def _create_default_admin(db, first_run: bool) -> BootstrapResult:
    # Check if admin already exists
    existing_admin = db.get_user_by_username(DEFAULT_ADMIN_USERNAME)
    if existing_admin:
        return BootstrapResult(success=True, is_first_run=first_run)
    
    # Generate temporary password
    temp_password = DEFAULT_ADMIN_TEMP_PASSWORD
    
    # Hash the password
    password_hash = hash_password(temp_password)
    
    # Create admin user with must_change_password flag
    user_id = db.create_user(
        username=DEFAULT_ADMIN_USERNAME,
        password_hash=password_hash,
        role="Admin",
        must_change_password=True
    )
    
    if user_id:
        # Log the bootstrap event
        db.log_audit(
            action="SYSTEM_BOOTSTRAP",
            user_id=user_id,
            username=DEFAULT_ADMIN_USERNAME,
            details="Application initialized with default admin user"
        )
        
        return BootstrapResult(
            success=True,
            is_first_run=True,
            default_password=temp_password
        )
    else:
        return BootstrapResult(
            success=False,
            error="Failed to create default admin user"
        )


def check_bootstrap_required() -> bool:
    if is_first_run():
        return True
    
    try:
        db = get_db()
        return not db.has_users()
    except Exception:
        return True


def get_default_admin_info() -> Tuple[str, str]:
    return DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_TEMP_PASSWORD
