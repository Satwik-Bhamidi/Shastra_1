"""
Shastra Proof Yard - External Updater
This script is compiled to updater.exe using PyInstaller.

Build command:
    pyinstaller --onefile --noconsole updater.py

The updater lifecycle:
1. Main app (Shastra.exe) downloads new version to temp/Shastra_new.exe
2. Main app launches this updater and exits immediately
3. This updater waits for main app to fully close (release file lock)
4. This updater verifies SHA256 integrity of the new binary (SECURITY!)
5. This updater replaces Shastra.exe with the new version
6. This updater restarts Shastra.exe
7. This updater exits

This is exactly how Chrome, Discord, and Steam updates work.
"""

import time
import os
import sys
import shutil
import subprocess
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime

# Configuration - MUST match your PyInstaller --name parameter
# On Windows: "Shastra_App.exe"
# On Linux: "Shastra_App" (no extension)
import platform
APP_NAME = "Shastra_App.exe" if platform.system() == "Windows" else "Shastra_App"
NEW_APP_NAME = "Shastra_new.exe" if platform.system() == "Windows" else "Shastra_new"
NEW_APP_PATH = f"temp/{NEW_APP_NAME}"
BACKUP_NAME = f"{APP_NAME}.backup"
LOG_FILE = "updater.log"
UPDATE_INFO_FILE = "temp/update_info.json"  # Contains SHA256 and version info
MAX_WAIT_SECONDS = 30
CHECK_INTERVAL = 0.5


def setup_logging():
    """Setup logging for the updater."""
    log_path = get_base_path() / LOG_FILE
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def get_base_path() -> Path:
    """Get the base path of the updater (where Shastra.exe lives)."""
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parent.parent


def is_process_running(process_name: str) -> bool:
    """
    Check if a process with given name is running.
    
    Args:
        process_name: Name of the process to check
        
    Returns:
        True if process is running, False otherwise
    """
    try:
        if sys.platform == "win32":
            # Windows: Use tasklist
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return process_name.lower() in result.stdout.lower()
        else:
            # Linux/Mac: Use pgrep
            result = subprocess.run(
                ['pgrep', '-f', process_name],
                capture_output=True
            )
            return result.returncode == 0
    except Exception:
        return False


def wait_for_app_exit(logger, app_name: str = APP_NAME) -> bool:
    """
    Wait for the main application to exit completely.
    
    This is critical because Windows locks running executables.
    We need to wait until the lock is released.
    
    Args:
        logger: Logger instance
        app_name: Name of the application to wait for
        
    Returns:
        True if app exited, False if timeout
    """
    logger.info(f"Waiting for {app_name} to exit...")
    
    # Initial delay to give the app time to start closing
    time.sleep(2)
    
    waited = 0
    while waited < MAX_WAIT_SECONDS:
        if not is_process_running(app_name):
            logger.info(f"{app_name} has exited")
            # Extra delay to ensure file lock is fully released
            time.sleep(1)
            return True
        
        time.sleep(CHECK_INTERVAL)
        waited += CHECK_INTERVAL
        logger.info(f"Still waiting... ({waited:.1f}s)")
    
    logger.warning(f"Timeout waiting for {app_name} to exit")
    return False


def create_backup(logger) -> bool:
    """
    Create a backup of the current executable before replacing.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if backup created, False otherwise
    """
    base_path = get_base_path()
    app_path = base_path / APP_NAME
    backup_path = base_path / BACKUP_NAME
    
    if not app_path.exists():
        logger.warning(f"Original {APP_NAME} not found, skipping backup")
        return True
    
    try:
        logger.info(f"Creating backup: {backup_path}")
        shutil.copy2(app_path, backup_path)
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False


def load_update_info(logger) -> dict:
    """
    Load update info from temp/update_info.json.
    
    This file is created by the main app before launching the updater
    and contains the SHA256 hash and version info for verification.
    
    Args:
        logger: Logger instance
        
    Returns:
        Dictionary with update info or empty dict if not found
    """
    base_path = get_base_path()
    update_info_path = base_path / UPDATE_INFO_FILE
    
    if not update_info_path.exists():
        logger.warning(f"Update info file not found: {update_info_path}")
        return {}
    
    try:
        with open(update_info_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded update info: version={data.get('version', 'unknown')}")
        return data
    except Exception as e:
        logger.error(f"Failed to load update info: {e}")
        return {}


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_sha256(logger, expected_hash: str) -> bool:
    """
    Verify SHA256 hash of the new executable before installation.
    
    This is a CRITICAL security step that ensures the binary hasn't been
    tampered with between download and installation.
    
    Args:
        logger: Logger instance
        expected_hash: Expected SHA256 hash from version.json
        
    Returns:
        True if hash matches or no hash provided, False if mismatch
    """
    if not expected_hash:
        logger.warning("No SHA256 hash provided - skipping verification")
        logger.warning("⚠️ Security: Consider providing SHA256 in version.json")
        return True
    
    base_path = get_base_path()
    new_app_path = base_path / NEW_APP_PATH
    
    if not new_app_path.exists():
        logger.error(f"New executable not found for SHA256 verification: {new_app_path}")
        return False
    
    logger.info("Verifying SHA256 integrity of new binary...")
    logger.info(f"  Expected: {expected_hash}")
    
    try:
        actual_hash = calculate_sha256(new_app_path)
        logger.info(f"  Actual:   {actual_hash}")
        
        if actual_hash.lower() == expected_hash.lower():
            logger.info("✅ SHA256 VERIFICATION PASSED - Binary integrity confirmed")
            return True
        else:
            logger.error("❌ SHA256 VERIFICATION FAILED - Binary may be corrupted or tampered!")
            logger.error("  This could indicate:")
            logger.error("    - File corruption during transfer")
            logger.error("    - Tampering by malware")
            logger.error("    - Incomplete download")
            logger.error("  Update will be ABORTED for security.")
            return False
            
    except Exception as e:
        logger.error(f"SHA256 verification error: {e}")
        return False


def replace_exe(logger) -> bool:
    """
    Replace the old executable with the new one.
    
    The new executable is always downloaded to temp/Shastra_new (or .exe on Windows)
    regardless of its GitHub asset name (e.g., Shastra_App_1.1.0).
    
    Args:
        logger: Logger instance
        
    Returns:
        True if replacement successful, False otherwise
    """
    base_path = get_base_path()
    app_path = base_path / APP_NAME
    new_app_path = base_path / NEW_APP_PATH
    
    # Verify the new executable exists
    if not new_app_path.exists():
        logger.error(f"New executable not found at {new_app_path}")
        # List what's in the temp folder for debugging
        temp_folder = base_path / "temp"
        if temp_folder.exists():
            logger.error(f"Contents of {temp_folder}:")
            for item in temp_folder.iterdir():
                logger.error(f"  - {item.name}")
        return False
    
    try:
        # Remove old executable
        if app_path.exists():
            logger.info(f"Removing old {APP_NAME}")
            os.remove(app_path)
        
        # Move new executable
        logger.info(f"Installing new {APP_NAME} from {new_app_path}")
        shutil.move(str(new_app_path), str(app_path))
        
        # Set executable permissions on Linux/Mac (CRITICAL!)
        # Without this, the app won't start after update on Linux
        if sys.platform != "win32":
            logger.info("Setting executable permissions (Linux/Mac)")
            os.chmod(app_path, 0o755)
        
        logger.info("Replacement successful!")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        logger.error("The application may still be running or locked by antivirus")
        return False
    except Exception as e:
        logger.error(f"Failed to replace executable: {e}")
        return False


def rollback(logger) -> bool:
    """
    Rollback to backup if update failed.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if rollback successful, False otherwise
    """
    base_path = get_base_path()
    app_path = base_path / APP_NAME
    backup_path = base_path / BACKUP_NAME
    
    if not backup_path.exists():
        logger.error("No backup found for rollback")
        return False
    
    try:
        if app_path.exists():
            os.remove(app_path)
        
        shutil.move(str(backup_path), str(app_path))
        logger.info("Rollback successful")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False


def restart_app(logger, new_version: str = "") -> bool:
    """
    Restart the main application after update.
    
    Args:
        logger: Logger instance
        new_version: The version that was just installed
        
    Returns:
        True if restart initiated, False otherwise
    """
    base_path = get_base_path()
    app_path = base_path / APP_NAME
    
    if not app_path.exists():
        logger.error(f"Cannot restart: {APP_NAME} not found")
        return False
    
    try:
        # Create a marker file to indicate successful update
        # The main app will check for this and show confirmation
        update_marker = base_path / ".update_complete"
        with open(update_marker, "w") as f:
            f.write(new_version if new_version else "unknown")
        logger.info(f"Created update marker: {update_marker}")
        
        logger.info(f"Starting {APP_NAME}...")
        
        if sys.platform == "win32":
            # Windows: Start as separate process
            subprocess.Popen(
                [str(app_path)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                close_fds=True
            )
        else:
            # Linux/Mac
            subprocess.Popen(
                [str(app_path)],
                start_new_session=True,
                close_fds=True
            )
        
        logger.info("Application restarted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to restart application: {e}")
        return False


def cleanup(logger):
    """
    Clean up temporary files after successful update.
    
    Args:
        logger: Logger instance
    """
    base_path = get_base_path()
    temp_path = base_path / "temp"
    backup_path = base_path / BACKUP_NAME
    
    try:
        # Clean temp folder
        if temp_path.exists():
            shutil.rmtree(temp_path)
            logger.info("Cleaned up temp folder")
        
        # Remove backup after successful update
        if backup_path.exists():
            os.remove(backup_path)
            logger.info("Removed backup file")
            
    except Exception as e:
        logger.warning(f"Cleanup warning: {e}")


def show_error_message(message: str):
    """
    Show error message to user (Windows only).
    
    Args:
        message: Error message to display
    """
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                "Shastra Updater - Error",
                0x10  # MB_ICONERROR
            )
        except:
            pass


def show_success_message(message: str):
    """
    Show success message to user (Windows only).
    
    Args:
        message: Success message to display
    """
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                message,
                "Shastra Updater",
                0x40  # MB_ICONINFORMATION
            )
        except:
            pass


def main():
    """
    Main updater logic.
    
    Workflow:
    1. Wait for main app to exit (release file lock)
    2. Load update info (SHA256, version)
    3. Verify SHA256 integrity of new binary (SECURITY!)
    4. Create backup of current executable
    5. Replace executable with new version
    6. Restart the application
    7. Clean up temporary files
    8. Exit updater
    """
    logger = setup_logging()
    
    logger.info("=" * 50)
    logger.info("Shastra Updater Started")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Working directory: {get_base_path()}")
    logger.info("=" * 50)
    
    success = False
    
    try:
        # Step 1: Wait for main app to exit
        if not wait_for_app_exit(logger):
            logger.error("Main application did not exit in time")
            show_error_message(
                "Update failed: The main application did not close properly.\n\n"
                "Please close Shastra manually and try again."
            )
            return
        
        # Step 2: Load update info (contains SHA256 hash)
        update_info = load_update_info(logger)
        expected_sha256 = update_info.get("sha256", "")
        new_version = update_info.get("version", "")
        
        # Step 3: Verify SHA256 integrity (CRITICAL SECURITY STEP)
        if not verify_sha256(logger, expected_sha256):
            logger.error("SHA256 verification failed - ABORTING UPDATE")
            show_error_message(
                "Update ABORTED: Security verification failed!\n\n"
                "The downloaded file may be corrupted or tampered with.\n"
                "Please try downloading the update again.\n\n"
                "Your current version remains unchanged."
            )
            return
        
        # Step 4: Create backup
        if not create_backup(logger):
            logger.warning("Backup creation failed, continuing anyway...")
        
        # Step 5: Replace executable
        if not replace_exe(logger):
            logger.error("Failed to replace executable")
            
            # Try rollback
            if rollback(logger):
                show_error_message(
                    "Update failed but previous version was restored.\n\n"
                    "Please try updating again later."
                )
            else:
                show_error_message(
                    "Update failed and rollback also failed.\n\n"
                    "Please reinstall the application."
                )
            return
        
        success = True
        logger.info("Update completed successfully!")
        
        # Read the new version from update_info or version.json
        if not new_version:
            try:
                version_file = get_base_path() / "version.json"
                if version_file.exists():
                    with open(version_file, "r") as f:
                        version_data = json.load(f)
                        new_version = version_data.get("version", "")
            except Exception as e:
                logger.warning(f"Could not read version: {e}")
        
        # Step 6: Restart application
        if not restart_app(logger, new_version):
            logger.warning("Auto-restart failed")
            show_success_message(
                "Update installed successfully!\n\n"
                "Please start Shastra manually."
            )
        
        # Step 7: Cleanup
        cleanup(logger)
        
    except Exception as e:
        logger.exception(f"Unexpected error during update: {e}")
        
        if not success:
            rollback(logger)
            show_error_message(
                f"Update failed with error:\n{str(e)}\n\n"
                "Previous version has been restored."
            )
    
    finally:
        logger.info("Updater exiting")
        logger.info("=" * 50)
        
        # Give user a moment to see the log
        time.sleep(2)


if __name__ == "__main__":
    main()