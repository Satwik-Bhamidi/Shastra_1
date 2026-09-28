"""
Shastra Proof Yard - Update Checker Module
Handles version checking, downloading updates, and launching the updater.

This module implements an update system similar to Chrome/Discord/Steam:
1. Check version.json for new versions
2. Download new executable to temp folder
3. Launch updater.exe and exit main app
4. Updater replaces the main exe and restarts

Supports three update sources (in priority order):
1. USB/Pendrive updates (highest priority - for offline/defence environments)
2. GitHub Releases API (for production private repo updates)
3. Local/LAN updates via local version.json (for testing/offline)
"""

import json
import os
import sys
import subprocess
import hashlib
import shutil
import platform
import requests
import getpass
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Union, Tuple
from packaging import version
from urllib.parse import urlparse


# ═══════════════════════════════════════════════════════════════════════════════
# Update Error Codes - Industry Standard Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

class UpdateErrorCode(Enum):
    """
    Standardized error codes for update operations.
    
    These follow industry best practices for user-friendly error handling.
    Each error code has a corresponding user-friendly message.
    """
    # Success
    SUCCESS = 0
    
    # File/Path Errors (100-199)
    FILE_NOT_FOUND = 100
    PATH_NOT_ACCESSIBLE = 101
    DISK_FULL = 102
    PERMISSION_DENIED = 103
    
    # Network Errors (200-299)
    NETWORK_ERROR = 200
    DOWNLOAD_FAILED = 201
    CONNECTION_TIMEOUT = 202
    AUTHENTICATION_FAILED = 203
    
    # Security Errors (300-399) - CRITICAL
    SHA256_MISMATCH = 300
    SIGNATURE_INVALID = 301
    INTEGRITY_CHECK_FAILED = 302
    TAMPER_DETECTED = 303
    
    # Update Process Errors (400-499)
    UPDATER_NOT_FOUND = 400
    UPDATE_CANCELLED = 401
    INVALID_VERSION = 402
    INCOMPATIBLE_PLATFORM = 403
    
    # Unknown/Generic Errors (500+)
    UNKNOWN_ERROR = 500


@dataclass
class UpdateResult:
    """
    Result object for update operations.
    
    Provides detailed error information for proper user notification.
    This is the industry-standard approach for operation results.
    """
    success: bool
    error_code: UpdateErrorCode = UpdateErrorCode.SUCCESS
    error_message: str = ""
    file_path: Optional[Path] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @classmethod
    def ok(cls, file_path: Optional[Path] = None, **details) -> "UpdateResult":
        """Create a successful result."""
        return cls(
            success=True,
            error_code=UpdateErrorCode.SUCCESS,
            file_path=file_path,
            details=details
        )
    
    @classmethod
    def error(
        cls, 
        code: UpdateErrorCode, 
        message: str = "",
        **details
    ) -> "UpdateResult":
        """Create an error result."""
        return cls(
            success=False,
            error_code=code,
            error_message=message or get_error_message(code),
            details=details
        )


def get_error_message(code: UpdateErrorCode) -> str:
    """
    Get user-friendly error message for an error code.
    
    These messages are designed to be:
    1. Clear and understandable to non-technical users
    2. Actionable - telling users what they can do
    3. Professional - suitable for production software
    """
    messages = {
        UpdateErrorCode.SUCCESS: "Operation completed successfully.",
        
        # File/Path Errors
        UpdateErrorCode.FILE_NOT_FOUND: (
            "The update file could not be found. "
            "Please ensure the update source is accessible and try again."
        ),
        UpdateErrorCode.PATH_NOT_ACCESSIBLE: (
            "Unable to access the required file path. "
            "Please check your permissions and try again."
        ),
        UpdateErrorCode.DISK_FULL: (
            "Not enough disk space to complete the update. "
            "Please free up some space and try again."
        ),
        UpdateErrorCode.PERMISSION_DENIED: (
            "Permission denied. Please run the application as administrator "
            "or check your file permissions."
        ),
        
        # Network Errors
        UpdateErrorCode.NETWORK_ERROR: (
            "A network error occurred. Please check your internet connection "
            "and try again."
        ),
        UpdateErrorCode.DOWNLOAD_FAILED: (
            "The download failed. This could be due to network issues. "
            "Please try again later."
        ),
        UpdateErrorCode.CONNECTION_TIMEOUT: (
            "The connection timed out. Please check your network and try again."
        ),
        UpdateErrorCode.AUTHENTICATION_FAILED: (
            "Authentication failed. Please verify your credentials and try again."
        ),
        
        # Security Errors - CRITICAL (red alert to user)
        UpdateErrorCode.SHA256_MISMATCH: (
            "⚠️ SECURITY ALERT: File integrity check failed!\n\n"
            "The downloaded file's checksum does not match the expected value. "
            "This could indicate:\n"
            "• The file was corrupted during transfer\n"
            "• The file may have been tampered with\n"
            "• The download was incomplete\n\n"
            "For your security, the update has been cancelled. "
            "Please try again or contact support if the problem persists."
        ),
        UpdateErrorCode.SIGNATURE_INVALID: (
            "⚠️ SECURITY ALERT: Digital signature verification failed!\n\n"
            "The update file's signature is invalid. For security reasons, "
            "this update has been rejected."
        ),
        UpdateErrorCode.INTEGRITY_CHECK_FAILED: (
            "⚠️ SECURITY ALERT: File integrity verification failed!\n\n"
            "The update file appears to be corrupted or modified. "
            "Please try downloading again."
        ),
        UpdateErrorCode.TAMPER_DETECTED: (
            "⚠️ SECURITY ALERT: Potential tampering detected!\n\n"
            "The update file may have been modified. For your protection, "
            "this update has been blocked."
        ),
        
        # Update Process Errors
        UpdateErrorCode.UPDATER_NOT_FOUND: (
            "The updater component is missing. "
            "Please reinstall the application."
        ),
        UpdateErrorCode.UPDATE_CANCELLED: (
            "The update was cancelled."
        ),
        UpdateErrorCode.INVALID_VERSION: (
            "Invalid version information. The update file may be corrupted."
        ),
        UpdateErrorCode.INCOMPATIBLE_PLATFORM: (
            "This update is not compatible with your operating system."
        ),
        
        # Generic
        UpdateErrorCode.UNKNOWN_ERROR: (
            "An unexpected error occurred. Please try again. "
            "If the problem persists, contact support."
        ),
    }
    
    return messages.get(code, messages[UpdateErrorCode.UNKNOWN_ERROR])


def get_error_title(code: UpdateErrorCode) -> str:
    """Get dialog title for an error code."""
    if code.value >= 300 and code.value < 400:
        return "Security Alert"
    elif code.value >= 200 and code.value < 300:
        return "Network Error"
    elif code.value >= 100 and code.value < 200:
        return "File Error"
    elif code.value >= 400 and code.value < 500:
        return "Update Error"
    else:
        return "Error"


APP_VERSION = "1.0.0"

# GitHub Releases Configuration
GITHUB_OWNER = "Pavankumar07s" 
GITHUB_REPO = "Shastra_Ai_release"  
GITHUB_API_BASE = "https://api.github.com"

# Token storage - In production, token is provided by user at runtime
_github_token: Optional[str] = None
APP_NAME = "Shastra Proof Yard"

# Platform-specific configuration
CURRENT_PLATFORM = platform.system().lower()  # "windows", "linux", "darwin"
IS_WINDOWS = CURRENT_PLATFORM == "windows"
IS_LINUX = CURRENT_PLATFORM == "linux"
IS_MACOS = CURRENT_PLATFORM == "darwin"

# Platform-specific file names
EXE_NAME = "Shastra_App.exe" if IS_WINDOWS else "Shastra_App"
UPDATER_NAME = "updater.exe" if IS_WINDOWS else "updater"
NEW_EXE_NAME = "Shastra_new.exe" if IS_WINDOWS else "Shastra_new"

# Platform-specific version.json names for GitHub releases
VERSION_JSON_PLATFORM = f"version_{CURRENT_PLATFORM}.json"  # version_windows.json, version_linux.json
VERSION_JSON_FALLBACK = "version.json"  # Fallback if platform-specific not found

TEMP_FOLDER = "temp"
UPDATE_MARKER_FILE = ".update_complete"

# ═══════════════════════════════════════════════════════════════════════════════
# USB/Pendrive Update Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Expected folder name on USB drive containing update files
USB_UPDATE_FOLDER_NAME = "SHASTRA_UPDATE"

# USB base paths for different platforms
if IS_WINDOWS:
    # Windows: Check all drive letters (D: through Z:)
    USB_BASE_PATHS: List[Path] = []
    for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
        USB_BASE_PATHS.append(Path(f"{letter}:\\"))
elif IS_LINUX:
    # Linux: USB drives mount under /media/<username>/ or /mnt/
    USB_BASE_PATHS = [
        Path("/media"),
        Path("/mnt"),
        Path("/run/media"),  # Some distros use this
    ]
elif IS_MACOS:
    # macOS: USB drives mount under /Volumes/
    USB_BASE_PATHS = [Path("/Volumes")]
else:
    USB_BASE_PATHS = []


# ═══════════════════════════════════════════════════════════════════════════════
# USB/Pendrive Detection Functions
# ═══════════════════════════════════════════════════════════════════════════════

def find_usb_update_directory() -> Optional[Path]:
    """
    Scan for USB/pendrive containing SHASTRA_UPDATE folder.
    
    Checks platform-specific mount points for removable drives.
    
    Returns:
        Path to SHASTRA_UPDATE folder on USB, or None if not found
    """
    print("DEBUG: Scanning for USB update drives...")
    
    if IS_WINDOWS:
        return _find_usb_update_windows()
    elif IS_LINUX:
        return _find_usb_update_linux()
    elif IS_MACOS:
        return _find_usb_update_macos()
    
    return None


def _find_usb_update_windows() -> Optional[Path]:
    """
    Find USB update directory on Windows.
    Checks removable drives (D: through Z:).
    """
    import ctypes
    
    for drive_path in USB_BASE_PATHS:
        try:
            if not drive_path.exists():
                continue
            
            # Check if it's a removable drive using Windows API
            drive_letter = str(drive_path)[0]
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive_letter}:\\")
            
            # 2 = DRIVE_REMOVABLE (USB drives, SD cards, etc.)
            # 3 = DRIVE_FIXED (could be external HDD)
            if drive_type not in [2, 3]:
                continue
            
            update_dir = drive_path / USB_UPDATE_FOLDER_NAME
            if update_dir.exists() and update_dir.is_dir():
                print(f"DEBUG: Found USB update directory: {update_dir}")
                return update_dir
                
        except Exception as e:
            print(f"DEBUG: Error checking drive {drive_path}: {e}")
            continue
    
    return None


def _find_usb_update_linux() -> Optional[Path]:
    """
    Find USB update directory on Linux.
    USB drives mount under /media/<username>/<USB_NAME>/ or /mnt/
    """
    for base_path in USB_BASE_PATHS:
        if not base_path.exists():
            continue
        
        try:
            # For /media, we need to iterate through user directories first
            if base_path == Path("/media") or base_path == Path("/run/media"):
                for user_dir in base_path.iterdir():
                    if not user_dir.is_dir():
                        continue
                    for usb_mount in user_dir.iterdir():
                        if not usb_mount.is_dir():
                            continue
                        update_dir = usb_mount / USB_UPDATE_FOLDER_NAME
                        if update_dir.exists() and update_dir.is_dir():
                            print(f"DEBUG: Found USB update directory: {update_dir}")
                            return update_dir
            else:
                # For /mnt, check direct subdirectories
                for usb_mount in base_path.iterdir():
                    if not usb_mount.is_dir():
                        continue
                    update_dir = usb_mount / USB_UPDATE_FOLDER_NAME
                    if update_dir.exists() and update_dir.is_dir():
                        print(f"DEBUG: Found USB update directory: {update_dir}")
                        return update_dir
                        
        except PermissionError:
            continue
        except Exception as e:
            print(f"DEBUG: Error scanning {base_path}: {e}")
            continue
    
    return None


def _find_usb_update_macos() -> Optional[Path]:
    """
    Find USB update directory on macOS.
    USB drives mount under /Volumes/<USB_NAME>/
    """
    volumes_path = Path("/Volumes")
    
    if not volumes_path.exists():
        return None
    
    try:
        for volume in volumes_path.iterdir():
            if not volume.is_dir():
                continue
            # Skip the main Macintosh HD
            if volume.name == "Macintosh HD":
                continue
            
            update_dir = volume / USB_UPDATE_FOLDER_NAME
            if update_dir.exists() and update_dir.is_dir():
                print(f"DEBUG: Found USB update directory: {update_dir}")
                return update_dir
                
    except Exception as e:
        print(f"DEBUG: Error scanning /Volumes: {e}")
    
    return None


def load_usb_version_info(update_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load version.json from USB update directory.
    
    Looks for platform-specific version file first, then falls back to generic.
    
    Args:
        update_dir: Path to SHASTRA_UPDATE folder on USB
        
    Returns:
        Parsed version info dictionary, or None if not found/invalid
    """
    # Try platform-specific file first
    version_files = [
        update_dir / VERSION_JSON_PLATFORM,
        update_dir / VERSION_JSON_FALLBACK
    ]
    
    for version_file in version_files:
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"DEBUG: Loaded USB version info from: {version_file}")
                return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"DEBUG: Error reading {version_file}: {e}")
                continue
    
    print("DEBUG: No valid version.json found on USB")
    return None


def get_usb_binary_path(update_dir: Path, version_data: Dict[str, Any]) -> Optional[Path]:
    """
    Get the path to the binary file on USB.
    
    Args:
        update_dir: Path to SHASTRA_UPDATE folder
        version_data: Parsed version.json data
        
    Returns:
        Path to binary file, or None if not found
    """
    # Get asset name from version data
    download_info = version_data.get("download", {})
    asset_name = download_info.get("asset_name", "")
    
    if asset_name:
        binary_path = update_dir / asset_name
        if binary_path.exists():
            return binary_path
    
    # Fallback: look for any Shastra_App* file
    for file in update_dir.iterdir():
        if file.name.startswith("Shastra_App") and file.is_file():
            # Skip version.json files
            if file.suffix == ".json":
                continue
            return file
    
    return None


def verify_usb_checksum(binary_path: Path, update_dir: Path) -> bool:
    """
    Verify binary checksum against checksum file on USB (if present).
    
    Args:
        binary_path: Path to the binary file
        update_dir: Path to SHASTRA_UPDATE folder (for checksum.sha256)
        
    Returns:
        True if checksum matches or no checksum file present, False if mismatch
    """
    checksum_file = update_dir / "checksum.sha256"
    
    if not checksum_file.exists():
        print("DEBUG: No checksum.sha256 file on USB, skipping verification")
        return True
    
    try:
        # Read expected checksum
        with open(checksum_file, "r") as f:
            content = f.read().strip()
            # Handle both formats: "hash  filename" and just "hash"
            expected_hash = content.split()[0].lower()
        
        # Calculate actual checksum
        sha256_hash = hashlib.sha256()
        with open(binary_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        actual_hash = sha256_hash.hexdigest().lower()
        
        if actual_hash == expected_hash:
            print("DEBUG: USB checksum verification passed")
            return True
        else:
            print(f"DEBUG: USB checksum mismatch! Expected: {expected_hash}, Got: {actual_hash}")
            return False
            
    except Exception as e:
        print(f"DEBUG: Error verifying USB checksum: {e}")
        return False


def check_usb_update() -> Optional[Dict[str, Any]]:
    """
    Check for updates available on USB/pendrive.
    
    Returns:
        Update info dictionary with USB-specific fields, or None if no update available
    """
    update_dir = find_usb_update_directory()
    
    if not update_dir:
        print("DEBUG: No USB update directory found")
        return None
    
    version_data = load_usb_version_info(update_dir)
    
    if not version_data:
        return None
    
    remote_version = version_data.get("version", "0.0.0")
    
    print(f"DEBUG: USB version = {remote_version}, Local version = {APP_VERSION}")
    
    try:
        if version.parse(remote_version) > version.parse(APP_VERSION):
            # Get binary path
            binary_path = get_usb_binary_path(update_dir, version_data)
            
            if not binary_path:
                print("DEBUG: USB binary file not found")
                return None
            
            # Verify checksum if available
            if not verify_usb_checksum(binary_path, update_dir):
                print("DEBUG: USB checksum verification failed")
                return None
            
            # Get SHA256 from version.json for display
            download_info = version_data.get("download", {})
            
            return {
                "current_version": APP_VERSION,
                "new_version": remote_version,
                "mandatory": version_data.get("mandatory", False),
                "changelog": version_data.get("changelog", []),
                "release_date": version_data.get("release_date", ""),
                "update_notes": version_data.get("update_notes", ""),
                "min_supported_version": version_data.get("min_supported_version", "0.0.0"),
                "source": "usb",
                "usb_update_dir": str(update_dir),
                "usb_binary_path": str(binary_path),
                "download_url": f"file://{binary_path}",
                "download_size": binary_path.stat().st_size,
                "sha256": download_info.get("sha256", ""),
                "asset_name": binary_path.name,
                "is_github_download": False,
                "is_usb_update": True
            }
    except Exception as e:
        print(f"DEBUG: Error checking USB version: {e}")
    
    return None


def copy_usb_update(
    usb_binary_path: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    sha256_expected: Optional[str] = None
) -> Union[UpdateResult, Path, None]:
    """
    Copy update binary from USB to temp folder.
    
    This is the USB equivalent of download_update() - copies locally instead of downloading.
    
    Args:
        usb_binary_path: Path to binary on USB drive
        progress_callback: Optional callback(copied_bytes, total_bytes)
        sha256_expected: Optional SHA256 hash to verify
        
    Returns:
        UpdateResult object with detailed status and error information,
        or Path for backward compatibility (deprecated)
    """
    if not usb_binary_path.exists():
        print(f"USB binary not found: {usb_binary_path}")
        return UpdateResult.error(
            UpdateErrorCode.FILE_NOT_FOUND,
            f"Update file not found on USB: {usb_binary_path.name}"
        )
    
    temp_path = get_temp_path()
    dest_path = temp_path / NEW_EXE_NAME
    
    try:
        total_size = usb_binary_path.stat().st_size
        copied = 0
        sha256_hash = hashlib.sha256()
        
        print(f"DEBUG: Copying USB update from {usb_binary_path} to {dest_path}")
        
        with open(usb_binary_path, "rb") as src, open(dest_path, "wb") as dst:
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)
                sha256_hash.update(chunk)
                copied += len(chunk)
                
                if progress_callback:
                    progress_callback(copied, total_size)
        
        # Verify SHA256 if provided
        if sha256_expected:
            calculated_hash = sha256_hash.hexdigest()
            if calculated_hash.lower() != sha256_expected.lower():
                print(f"SHA256 mismatch: expected {sha256_expected}, got {calculated_hash}")
                dest_path.unlink()
                return UpdateResult.error(
                    UpdateErrorCode.SHA256_MISMATCH,
                    details={
                        "expected_hash": sha256_expected[:16] + "...",
                        "actual_hash": calculated_hash[:16] + "...",
                        "source": "usb"
                    }
                )
        
        print(f"DEBUG: USB update copied successfully to {dest_path}")
        return UpdateResult.ok(file_path=dest_path, source="usb")
        
    except PermissionError as e:
        print(f"USB copy permission error: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return UpdateResult.error(
            UpdateErrorCode.PERMISSION_DENIED,
            f"Permission denied while copying: {e}"
        )
    except OSError as e:
        print(f"USB copy OS error: {e}")
        if dest_path.exists():
            dest_path.unlink()
        # Check for disk full error
        if "No space" in str(e) or "disk full" in str(e).lower():
            return UpdateResult.error(UpdateErrorCode.DISK_FULL)
        return UpdateResult.error(
            UpdateErrorCode.PATH_NOT_ACCESSIBLE,
            f"Failed to access path: {e}"
        )
    except Exception as e:
        print(f"USB copy failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return UpdateResult.error(
            UpdateErrorCode.UNKNOWN_ERROR,
            f"Copy failed: {e}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Update Resolution (Priority-based)
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_update(
    check_usb: bool = True,
    check_github: bool = True,
    check_local: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Resolve the best available update source.
    
    Priority order:
    1. USB/Pendrive (highest - for offline/defence environments)
    2. GitHub Releases (for production)
    3. Local version.json (for testing)
    
    Args:
        check_usb: Whether to check for USB updates
        check_github: Whether to check GitHub (requires token)
        check_local: Whether to check local version.json
        
    Returns:
        Update info dictionary with 'source' field indicating origin,
        or None if no update available
    """
    print("DEBUG: Resolving best update source...")
    
    # 1. USB (highest priority - always check first if enabled)
    if check_usb:
        print("DEBUG: Checking USB for updates...")
        usb_update = check_usb_update()
        if usb_update:
            print(f"DEBUG: USB update available: v{usb_update['new_version']}")
            return usb_update
    
    # 2. GitHub (if token is available)
    if check_github and is_github_token_set():
        print("DEBUG: Checking GitHub for updates...")
        try:
            github_update = check_for_update(use_github=True)
            if github_update:
                print(f"DEBUG: GitHub update available: v{github_update['new_version']}")
                return github_update
        except Exception as e:
            print(f"DEBUG: GitHub check failed: {e}")
    
    # 3. Local version.json (lowest priority, for testing)
    if check_local:
        print("DEBUG: Checking local version.json for updates...")
        local_update = check_for_update(use_github=False)
        if local_update:
            print(f"DEBUG: Local update available: v{local_update['new_version']}")
            return local_update
    
    print("DEBUG: No updates available from any source")
    return None


def get_update_source_display_name(update_info: Dict[str, Any]) -> str:
    """
    Get human-readable display name for the update source.
    
    Args:
        update_info: Update info dictionary
        
    Returns:
        Display name string (e.g., "USB Drive", "GitHub", "Local")
    """
    source = update_info.get("source", "unknown")
    
    if source == "usb":
        return "USB Drive (Offline)"
    elif source == "github":
        return "GitHub Releases"
    elif source == "local":
        return "Local Network"
    else:
        return "Unknown Source"


# ═══════════════════════════════════════════════════════════════════════════════
# Versioned Binary Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def extract_version_from_asset_name(asset_name: str) -> Optional[str]:
    """
    Extract version from asset name (e.g., "Shastra_App_1.1.0" -> "1.1.0").
    
    Args:
        asset_name: Asset name from GitHub release
        
    Returns:
        Extracted version string or None if no version found
    """
    # Remove file extension if present
    name_without_ext = asset_name.replace('.exe', '')
    
    # Pattern: Shastra_App_X.Y.Z
    if "Shastra_App_" in name_without_ext:
        version_part = name_without_ext.replace("Shastra_App_", "")
        # Validate it looks like a version (contains dots)
        if version_part and "." in version_part:
            return version_part
    
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# GitHub Token Management
# ═══════════════════════════════════════════════════════════════════════════════

def set_github_token(token: str) -> None:
    """
    Set the GitHub token for API access.
    
    Args:
        token: GitHub personal access token with read access to the releases repo
    """
    global _github_token
    _github_token = token


def get_github_token() -> Optional[str]:
    """
    Get the GitHub token from memory or environment variable.
    
    Returns:
        GitHub token or None if not set
    """
    global _github_token
    
    # First check if token is set in memory (from dialog input)
    if _github_token:
        return _github_token
    
    # Fallback to environment variable
    return os.environ.get("SHASTRA_GITHUB_TOKEN")


def clear_github_token() -> None:
    """Clear the GitHub token from memory."""
    global _github_token
    _github_token = None


def is_github_token_set() -> bool:
    """Check if a GitHub token is available."""
    return get_github_token() is not None


def _github_headers() -> Dict[str, str]:
    """
    Get headers for GitHub API requests.
    
    Returns:
        Dictionary of headers including authorization
        
    Raises:
        RuntimeError: If no GitHub token is set
    """
    token = get_github_token()
    if not token:
        raise RuntimeError("GitHub token not set. Please enter your GitHub token.")
    
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GitHub Releases API Functions
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_latest_github_release(include_prereleases: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch the latest release metadata from GitHub Releases API.
    
    Args:
        include_prereleases: If True, also check for pre-releases when no 
                            full release is found. GitHub's /releases/latest 
                            endpoint does NOT return pre-releases.
    
    Returns:
        Release metadata dictionary or None on failure
    """
    # First try the /releases/latest endpoint (only returns full releases, not pre-releases)
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    
    print(f"DEBUG: Fetching latest release from: {url}")
    
    try:
        response = requests.get(url, headers=_github_headers(), timeout=15)
        print(f"DEBUG: Response status code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        
        # If 404 and we should include pre-releases, try /releases endpoint
        if response.status_code == 404 and include_prereleases:
            print("DEBUG: No full release found, checking for pre-releases...")
            return _fetch_latest_from_all_releases()
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("GitHub authentication failed - invalid token")
        elif e.response.status_code == 403:
            print("GitHub access forbidden - token may lack permissions")
        else:
            print(f"GitHub API error: {e}")
        return None
    except Exception as e:
        print(f"Failed to fetch GitHub release: {e}")
        return None


def _fetch_latest_from_all_releases() -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent release (including pre-releases) from /releases endpoint.
    
    This is used as a fallback when /releases/latest returns 404 because
    the repository only has pre-releases.
    
    Returns:
        The most recent release metadata or None
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
    
    print(f"DEBUG: Fetching all releases from: {url}")
    
    try:
        response = requests.get(url, headers=_github_headers(), timeout=15)
        print(f"DEBUG: Response status code: {response.status_code}")
        response.raise_for_status()
        
        releases = response.json()
        
        if not releases:
            print(f"No releases found in the repository: {GITHUB_OWNER}/{GITHUB_REPO}")
            print("DEBUG: Make sure you have created a Release (not just pushed code)")
            return None
        
        # Return the first (most recent) release
        latest = releases[0]
        print(f"DEBUG: Found release: {latest.get('tag_name')} (pre-release: {latest.get('prerelease', False)})")
        return latest
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Repository not found or no access: {GITHUB_OWNER}/{GITHUB_REPO}")
        else:
            print(f"GitHub API error: {e}")
        return None
    except Exception as e:
        print(f"Failed to fetch GitHub releases: {e}")
        return None


def get_versioned_exe_name(remote_version: str) -> str:
    """
    Get the expected executable name for a specific version.
    
    This handles both versioned and non-versioned binary names:
    - Remote: Shastra_App_1.1.0 (or Shastra_App_1.1.0.exe on Windows)
    - Local: Shastra_App (or Shastra_App.exe on Windows)
    
    Args:
        remote_version: Version string from remote (e.g., "1.1.0")
        
    Returns:
        Expected executable name for this version
    """
    # Always use the base name without version for the local executable
    # The versioned name is only for the remote binary on GitHub
    return EXE_NAME

def fetch_version_json_from_github() -> Optional[Dict[str, Any]]:
    """
    Fetch version.json from the latest GitHub Release assets.
    
    Looks for platform-specific version files first:
    - Windows: version_windows.json
    - Linux: version_linux.json
    - macOS: version_darwin.json
    
    Falls back to version.json if platform-specific file not found.
    
    Returns:
        Parsed version.json content or None on failure
    """
    release = fetch_latest_github_release()
    if not release:
        return None
    
    assets = release.get("assets", [])
    
    # Build list of version files to try (platform-specific first, then fallback)
    version_files_to_try = [VERSION_JSON_PLATFORM, VERSION_JSON_FALLBACK]
    
    for version_filename in version_files_to_try:
        for asset in assets:
            if asset.get("name") == version_filename:
                try:
                    # Download the asset using the API URL (requires auth)
                    headers = _github_headers()
                    headers["Accept"] = "application/octet-stream"
                    
                    response = requests.get(
                        asset["url"],
                        headers=headers,
                        timeout=15,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    print(f"Loaded version info from: {version_filename}")
                    return response.json()
                except Exception as e:
                    print(f"Failed to fetch {version_filename} from GitHub: {e}")
                    continue  # Try next file
    
    print(f"No version.json found in release assets. Tried: {version_files_to_try}")
    return None


def get_github_download_info(version_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """
    Get download URL and info for the executable from GitHub Release.
    
    Args:
        version_data: Parsed version.json containing asset_name
        
    Returns:
        Dictionary with download URL and asset info, or None on failure
    """
    release = fetch_latest_github_release()
    if not release:
        return None
    
    # Get asset name from version.json
    download_info = version_data.get("download", {})
    asset_name = download_info.get("asset_name", "")
    
    if not asset_name:
        print("No asset_name specified in version.json")
        return None
    
    # Find the asset in release
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return {
                "url": asset["url"],  # API URL for authenticated download
                "browser_url": asset.get("browser_download_url", ""),
                "name": asset["name"],
                "size": asset.get("size", 0),
                "sha256": download_info.get("sha256", "")
            }
    
    print(f"Asset '{asset_name}' not found in release")
    return None


def validate_github_token(token: str) -> tuple[bool, str]:
    """
    Validate a GitHub token by making a test API call.
    
    Args:
        token: GitHub token to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, "Token is valid"
        elif response.status_code == 401:
            return False, "Invalid token - authentication failed"
        elif response.status_code == 403:
            return False, "Token doesn't have access to this repository"
        elif response.status_code == 404:
            return False, "Repository not found or token lacks access"
        else:
            return False, f"Unexpected error: {response.status_code}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def get_base_path() -> Path:
    """Get the base path of the application (works for both dev and frozen)."""
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parents[1]


def get_version_file_path() -> Path:
    """Get the path to version.json file."""
    return get_base_path() / "version.json"


def get_temp_path() -> Path:
    """Get the temp folder path for storing downloaded updates."""
    temp_path = get_base_path() / TEMP_FOLDER
    temp_path.mkdir(exist_ok=True)
    return temp_path


def get_current_version() -> str:
    """Get the current application version."""
    return APP_VERSION


def check_update_complete() -> Optional[str]:
    """
    Check if app was just updated (marker file exists).
    
    Returns:
        The version string if update just completed, None otherwise
    """
    marker_path = get_base_path() / UPDATE_MARKER_FILE
    
    if marker_path.exists():
        try:
            with open(marker_path, "r") as f:
                version = f.read().strip()
            # Delete the marker file after reading
            marker_path.unlink()
            return version if version else APP_VERSION
        except Exception:
            try:
                marker_path.unlink()
            except:
                pass
            return APP_VERSION
    
    return None


def load_version_info(version_file_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load version information from local or remote version.json.
    
    Args:
        version_file_path: Optional custom path to version.json
        
    Returns:
        Dictionary containing version info or None if file not found
    """
    if version_file_path is None:
        version_file_path = get_version_file_path()
    
    if not version_file_path.exists():
        return None
    
    try:
        with open(version_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading version.json: {e}")
        return None


def check_for_update(
    remote_version_url: Optional[str] = None,
    use_github: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Check if a new version is available.
    
    Args:
        remote_version_url: Optional URL to fetch remote version.json (for local/HTTP updates)
        use_github: If True, use GitHub Releases API instead of URL
        
    Returns:
        Dictionary with update info if available, None otherwise
    """
    remote_data = None
    github_download_info = None
    
    # ═══════════════════════════════════════════════════════════════════
    # GitHub Releases API Update Check (Production)
    # ═══════════════════════════════════════════════════════════════════
    if use_github:
        try:
            remote_data = fetch_version_json_from_github()
            if remote_data:
                # Get download info from GitHub release assets
                github_download_info = get_github_download_info(remote_data)
        except RuntimeError as e:
            # Token not set
            print(f"GitHub update check failed: {e}")
            return None
        except Exception as e:
            print(f"GitHub update check failed: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════
    # HTTP URL Update Check (Cloud/CDN)
    # ═══════════════════════════════════════════════════════════════════
    elif remote_version_url:
        try:
            response = requests.get(remote_version_url, timeout=10)
            response.raise_for_status()
            remote_data = response.json()
        except Exception as e:
            print(f"Failed to fetch remote version: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════
    # Local Version File Check (Testing/Offline)
    # ═══════════════════════════════════════════════════════════════════
    else:
        remote_data = load_version_info()
    
    if remote_data is None:
        print("DEBUG: remote_data is None - no version info fetched")
        return None
    
    remote_version = remote_data.get("version", "0.0.0")
    
    # Debug output for version comparison
    print(f"DEBUG: Local APP_VERSION = {APP_VERSION}")
    print(f"DEBUG: Remote version = {remote_version}")
    print(f"DEBUG: Update available = {version.parse(remote_version) > version.parse(APP_VERSION)}")
    
    try:
        if version.parse(remote_version) > version.parse(APP_VERSION):
            update_info = {
                "current_version": APP_VERSION,
                "new_version": remote_version,
                "mandatory": remote_data.get("mandatory", False),
                "changelog": remote_data.get("changelog", []),
                "release_date": remote_data.get("release_date", ""),
                "update_notes": remote_data.get("update_notes", ""),
                "min_supported_version": remote_data.get("min_supported_version", "0.0.0"),
                "source": "github" if use_github else "local"
            }
            
            # Handle download URL based on source
            if use_github and github_download_info:
                update_info["download_url"] = github_download_info["url"]
                update_info["download_size"] = github_download_info.get("size", 0)
                update_info["sha256"] = github_download_info.get("sha256", "")
                update_info["asset_name"] = github_download_info.get("name", "")
                update_info["is_github_download"] = True
            else:
                download = remote_data.get("download", {})
                update_info["download_url"] = download.get("url", "")
                update_info["download_size"] = download.get("size_bytes", 0)
                update_info["sha256"] = download.get("sha256", "")
                update_info["is_github_download"] = False
            
            return update_info
    except Exception as e:
        print(f"Version comparison error: {e}")
    
    return None


def is_version_supported() -> bool:
    """Check if the current version is still supported."""
    version_data = load_version_info()
    if version_data is None:
        return True
    
    min_version = version_data.get("min_supported_version", "0.0.0")
    try:
        return version.parse(APP_VERSION) >= version.parse(min_version)
    except:
        return True


def download_update(
    url: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    sha256_expected: Optional[str] = None,
    is_github_download: bool = False,
    asset_name: Optional[str] = None
) -> Optional[Path]:
    """
    Download the new executable from the given URL.
    Supports local file://, http/https URLs, and GitHub Release asset downloads.
    
    Args:
        url: Download URL for the new executable (file://, http://, https://, or GitHub API URL)
        progress_callback: Optional callback(downloaded_bytes, total_bytes)
        sha256_expected: Optional SHA256 hash to verify download
        is_github_download: If True, use GitHub API authentication for download
        asset_name: Optional original asset name from GitHub (e.g., "Shastra_App_1.1.0")
                   If provided, will be normalized to NEW_EXE_NAME after download
        
    Returns:
        Path to downloaded file or None on failure
    """
    parsed = urlparse(url)
    temp_path = get_temp_path()
    download_path = temp_path / NEW_EXE_NAME
    
    # ═══════════════════════════════════════════════════════════════════
    # LOCAL FILE UPDATE (file:// URL) - For dev testing / offline systems
    # ═══════════════════════════════════════════════════════════════════
    if parsed.scheme == "file":
        source_path = Path(parsed.path)
        
        if not source_path.exists():
            print(f"Local update file not found: {source_path}")
            return None
        
        try:
            total_size = source_path.stat().st_size
            
            # Copy with progress callback support
            sha256_hash = hashlib.sha256()
            copied = 0
            
            with open(source_path, "rb") as src, open(download_path, "wb") as dst:
                while True:
                    chunk = src.read(8192)
                    if not chunk:
                        break
                    dst.write(chunk)
                    sha256_hash.update(chunk)
                    copied += len(chunk)
                    
                    if progress_callback:
                        progress_callback(copied, total_size)
            
            # Verify SHA256 if provided
            if sha256_expected:
                calculated_hash = sha256_hash.hexdigest()
                if calculated_hash.lower() != sha256_expected.lower():
                    print(f"SHA256 mismatch: expected {sha256_expected}, got {calculated_hash}")
                    download_path.unlink()
                    return None
            
            print(f"Local file copied successfully: {source_path} -> {download_path}")
            return download_path
            
        except Exception as e:
            print(f"Local file copy failed: {e}")
            if download_path.exists():
                download_path.unlink()
            return None
    
    # ═══════════════════════════════════════════════════════════════════
    # GITHUB RELEASE ASSET DOWNLOAD - For private repo releases
    # ═══════════════════════════════════════════════════════════════════
    if is_github_download:
        try:
            headers = _github_headers()
            headers["Accept"] = "application/octet-stream"
            
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=60,
                allow_redirects=True
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            sha256_hash = hashlib.sha256()
            
            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        sha256_hash.update(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            # Verify SHA256 if provided
            if sha256_expected:
                calculated_hash = sha256_hash.hexdigest()
                if calculated_hash.lower() != sha256_expected.lower():
                    print(f"SHA256 mismatch: expected {sha256_expected}, got {calculated_hash}")
                    download_path.unlink()
                    return None
            
            print(f"GitHub asset downloaded successfully to {download_path}")            
            # If asset_name was provided and is different from NEW_EXE_NAME, rename it
            if asset_name and download_path.name != NEW_EXE_NAME:
                try:
                    final_path = temp_path / NEW_EXE_NAME
                    download_path.rename(final_path)
                    print(f"DEBUG: Renamed {download_path.name} -> {NEW_EXE_NAME}")
                    return final_path
                except Exception as e:
                    print(f"Failed to rename downloaded file: {e}")
                    return download_path
            
            return download_path
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("GitHub authentication failed - invalid token")
            elif e.response.status_code == 404:
                print("Asset not found or token lacks access")
            else:
                print(f"GitHub download failed: {e}")
            if download_path.exists():
                download_path.unlink()
            return None
        except Exception as e:
            print(f"GitHub download failed: {e}")
            if download_path.exists():
                download_path.unlink()
            return None
    
    # ═══════════════════════════════════════════════════════════════════
    # HTTP/HTTPS UPDATE - For production (public URLs, CDN, etc.)
    # ═══════════════════════════════════════════════════════════════════
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        sha256_hash = hashlib.sha256()
        
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    sha256_hash.update(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        # Verify SHA256 if provided
        if sha256_expected:
            calculated_hash = sha256_hash.hexdigest()
            if calculated_hash.lower() != sha256_expected.lower():
                print(f"SHA256 mismatch: expected {sha256_expected}, got {calculated_hash}")
                download_path.unlink()
                return None
        
        return download_path
        
    except Exception as e:
        print(f"Download failed: {e}")
        if download_path.exists():
            download_path.unlink()
        return None


def create_backup() -> Optional[Path]:
    """
    Create a backup of the current executable.
    
    Returns:
        Path to backup file or None on failure
    """
    base_path = get_base_path()
    current_exe = base_path / EXE_NAME
    backup_exe = base_path / f"{EXE_NAME}.backup"
    
    if not current_exe.exists():
        return None
    
    try:
        shutil.copy2(current_exe, backup_exe)
        return backup_exe
    except Exception as e:
        print(f"Backup failed: {e}")
        return None


def save_update_info_for_updater(update_info: Dict[str, Any]) -> bool:
    """
    Save update info to temp/update_info.json for the updater to read.
    
    This allows the updater to perform a second SHA256 verification
    before replacing the binary - a critical security step.
    
    Args:
        update_info: Dictionary containing sha256, version, etc.
        
    Returns:
        True if saved successfully, False otherwise
    """
    import time
    
    temp_path = get_temp_path()
    update_info_path = temp_path / "update_info.json"
    
    # Extract only the info needed by the updater
    updater_info = {
        "sha256": update_info.get("sha256", ""),
        "version": update_info.get("new_version", ""),
        "source": update_info.get("source", "unknown"),
        "timestamp": time.time()
    }
    
    try:
        with open(update_info_path, "w", encoding="utf-8") as f:
            json.dump(updater_info, f, indent=2)
        print(f"DEBUG: Saved update info for updater: {update_info_path}")
        print(f"DEBUG: SHA256 for verification: {updater_info['sha256'][:16]}..." if updater_info['sha256'] else "DEBUG: No SHA256 provided")
        return True
    except Exception as e:
        print(f"Failed to save update info: {e}")
        return False


def launch_updater(update_info: Optional[Dict[str, Any]] = None) -> bool:
    """
    Launch the updater.exe and exit the main application.
    
    This is the critical part - the main app MUST exit after launching
    the updater so Windows releases the file lock on the executable.
    
    Args:
        update_info: Optional update info dict to save for updater's SHA256 verification
    
    Returns:
        True if updater launched successfully, False otherwise
    """
    base_path = get_base_path()
    updater_path = base_path / UPDATER_NAME
    
    if not updater_path.exists():
        print(f"Updater not found at {updater_path}")
        return False
    
    # Save update info for updater's SHA256 verification
    if update_info:
        save_update_info_for_updater(update_info)
    
    try:
        # Launch updater as a completely separate process
        if sys.platform == "win32":
            # Windows: Use CREATE_NEW_PROCESS_GROUP to detach completely
            subprocess.Popen(
                [str(updater_path)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                close_fds=True
            )
        else:
            # Linux/Mac: Use nohup-like behavior
            subprocess.Popen(
                [str(updater_path)],
                start_new_session=True,
                close_fds=True
            )
        
        return True
        
    except Exception as e:
        print(f"Failed to launch updater: {e}")
        return False


def perform_update(
    update_info: Dict[str, Any],
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Perform the complete update process:
    1. Download/Copy new executable (from USB, GitHub, or HTTP)
    2. Launch updater
    3. Exit application
    
    Supports three update sources:
    - USB: Direct copy from pendrive (offline)
    - GitHub: Download from GitHub Releases API
    - HTTP: Download from URL
    
    Args:
        update_info: Dictionary from check_for_update() or check_usb_update()
        progress_callback: Optional progress callback for download/copy
        
    Returns:
        True if update process started, False on failure
    """
    sha256 = update_info.get("sha256", "")
    is_usb_update = update_info.get("is_usb_update", False)
    is_github_download = update_info.get("is_github_download", False)
    
    downloaded_file = None
    
    # ═══════════════════════════════════════════════════════════════════
    # USB UPDATE - Copy from pendrive (no network required)
    # ═══════════════════════════════════════════════════════════════════
    if is_usb_update:
        usb_binary_path = update_info.get("usb_binary_path", "")
        if not usb_binary_path:
            print("No USB binary path provided")
            return False
        
        print(f"DEBUG: Performing USB update from: {usb_binary_path}")
        downloaded_file = copy_usb_update(
            Path(usb_binary_path),
            progress_callback=progress_callback,
            sha256_expected=sha256 if sha256 else None
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # NETWORK UPDATE - Download from GitHub or HTTP URL
    # ═══════════════════════════════════════════════════════════════════
    else:
        download_url = update_info.get("download_url", "")
        if not download_url:
            print("No download URL provided")
            return False
        
        # Extract asset name from update info if available (for versioned binaries)
        asset_name = update_info.get("asset_name", None)
        
        downloaded_file = download_update(
            download_url,
            progress_callback=progress_callback,
            sha256_expected=sha256 if sha256 else None,
            is_github_download=is_github_download,
            asset_name=asset_name
        )
    
    if downloaded_file is None:
        return False
    
    # Step 2: Create backup (optional but recommended)
    create_backup()
    
    # Step 3: Launch updater with update info for SHA256 verification
    # The updater will verify SHA256 again before replacing the binary
    if not launch_updater(update_info=update_info):
        return False
    
    # Step 4: Exit application - CRITICAL!
    # The updater needs the main exe to be closed to replace it
    sys.exit(0)


def cleanup_temp_files():
    """Clean up temporary update files."""
    temp_path = get_temp_path()
    
    if temp_path.exists():
        try:
            shutil.rmtree(temp_path)
            temp_path.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Cleanup failed: {e}")


def cleanup_backup():
    """Remove backup file after successful update."""
    base_path = get_base_path()
    backup_exe = base_path / f"{EXE_NAME}.backup"
    
    if backup_exe.exists():
        try:
            backup_exe.unlink()
        except Exception as e:
            print(f"Failed to remove backup: {e}")


def get_changelog_text(update_info: Dict[str, Any]) -> str:
    """
    Format changelog into readable text.
    
    Args:
        update_info: Dictionary from check_for_update()
        
    Returns:
        Formatted changelog string
    """
    changelog = update_info.get("changelog", [])
    if not changelog:
        return "No changelog available."
    
    lines = []
    for entry in changelog:
        if isinstance(entry, dict):
            ver = entry.get("version", "")
            date = entry.get("date", "")
            changes = entry.get("changes", [])
            
            lines.append(f"Version {ver} ({date})")
            for change in changes:
                lines.append(f"  • {change}")
            lines.append("")
        else:
            lines.append(f"  • {entry}")
    
    return "\n".join(lines)


# PyQt5 Integration Helper Classes
class UpdateChecker:
    """
    PyQt5-friendly update checker class.
    
    Supports three update sources (in priority order):
    1. USB/Pendrive (highest - for offline/defence environments)
    2. GitHub Releases API (for production)
    3. Local version.json (for testing)
    
    Usage:
        # For USB + GitHub updates (production - USB takes priority)
        checker = UpdateChecker(use_github=True, check_usb=True)
        set_github_token("your_token")  # Optional - only for GitHub
        
        # For GitHub only updates
        checker = UpdateChecker(use_github=True, check_usb=False)
        set_github_token("your_token")
        
        # For USB only updates (fully offline)
        checker = UpdateChecker(use_github=False, check_usb=True)
        
        update_info = checker.check()
        if update_info:
            checker.download_and_install(update_info)
    """
    
    def __init__(
        self, 
        remote_url: Optional[str] = None, 
        use_github: bool = False,
        check_usb: bool = True
    ):
        """
        Initialize the update checker.
        
        Args:
            remote_url: Optional URL for remote version.json (ignored if use_github=True)
            use_github: If True, use GitHub Releases API for updates
            check_usb: If True, check USB/pendrive for updates (highest priority)
        """
        self.remote_url = remote_url
        self.use_github = use_github
        self.check_usb = check_usb
        self.current_version = APP_VERSION
    
    def check(self) -> Optional[Dict[str, Any]]:
        """
        Check for available updates from all configured sources.
        
        USB updates take highest priority if enabled.
        
        Returns:
            Update info dict or None if no update available
        """
        return resolve_update(
            check_usb=self.check_usb,
            check_github=self.use_github,
            check_local=bool(self.remote_url) or (not self.use_github and not self.check_usb)
        )
    
    def check_usb_only(self) -> Optional[Dict[str, Any]]:
        """Check only USB/pendrive for updates."""
        return check_usb_update()
    
    def check_github_only(self) -> Optional[Dict[str, Any]]:
        """Check only GitHub for updates."""
        return check_for_update(use_github=True)
    
    def download_and_install(
        self,
        update_info: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download/copy and install the update.
        
        Automatically handles USB (copy) vs network (download) updates.
        
        Args:
            update_info: Update information from check()
            progress_callback: Optional progress callback
            
        Returns:
            True if update started successfully
        """
        return perform_update(update_info, progress_callback)
    
    def is_mandatory_update(self, update_info: Dict[str, Any]) -> bool:
        """Check if the update is mandatory."""
        return update_info.get("mandatory", False)
    
    def get_update_message(self, update_info: Dict[str, Any]) -> str:
        """Get a formatted update message for display."""
        new_ver = update_info.get("new_version", "")
        current_ver = update_info.get("current_version", APP_VERSION)
        source = get_update_source_display_name(update_info)
        
        return (
            f"A new version of {APP_NAME} is available!\n\n"
            f"Current version: {current_ver}\n"
            f"New version: {new_ver}\n"
            f"Update source: {source}\n\n"
            f"Would you like to update now?"
        )
    
    def requires_token(self) -> bool:
        """Check if this checker requires a GitHub token."""
        return self.use_github and not self.check_usb
    
    def is_token_configured(self) -> bool:
        """Check if GitHub token is configured (for GitHub mode)."""
        if not self.use_github:
            return True
        return is_github_token_set()
    
    def get_update_source(self, update_info: Dict[str, Any]) -> str:
        """Get the source of the update ('usb', 'github', 'local')."""
        return update_info.get("source", "unknown")
    
    def is_usb_update(self, update_info: Dict[str, Any]) -> bool:
        """Check if this is a USB/pendrive update."""
        return update_info.get("is_usb_update", False)


if __name__ == "__main__":
    # Test the update checker
    print(f"Current version: {APP_VERSION}")
    print(f"Base path: {get_base_path()}")
    print(f"Version file: {get_version_file_path()}")
    
    update_info = check_for_update()
    if update_info:
        print(f"Update available: {update_info['new_version']}")
        print(get_changelog_text(update_info))
    else:
        print("No update available")
