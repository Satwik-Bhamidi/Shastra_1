"""
Shastra Proof Yard - Updater Module

Supports three update modes (in priority order):
1. USB/Pendrive updates (highest priority - for offline/defence environments)
2. GitHub Releases API (production private repo)
3. Local/LAN updates via local version.json (testing/offline)
"""

from .update_checker import (
    APP_VERSION,
    APP_NAME,
    UpdateChecker,
    check_for_update,
    check_update_complete,
    get_current_version,
    get_changelog_text,
    perform_update,
    download_update,
    launch_updater,
    cleanup_temp_files,
    cleanup_backup,
    is_version_supported,
    # Error handling classes
    UpdateResult,
    UpdateErrorCode,
    get_error_message,
    get_error_title,
    # GitHub API functions
    GITHUB_OWNER,
    GITHUB_REPO,
    set_github_token,
    get_github_token,
    clear_github_token,
    is_github_token_set,
    validate_github_token,
    fetch_latest_github_release,
    fetch_version_json_from_github,
    get_github_download_info,
    # Platform detection
    CURRENT_PLATFORM,
    IS_WINDOWS,
    IS_LINUX,
    IS_MACOS,
    VERSION_JSON_PLATFORM,
    # USB/Pendrive update functions
    USB_UPDATE_FOLDER_NAME,
    find_usb_update_directory,
    load_usb_version_info,
    get_usb_binary_path,
    verify_usb_checksum,
    check_usb_update,
    copy_usb_update,
    resolve_update,
    get_update_source_display_name
)

from .update_dialog import (
    UpdateDialog,
    GitHubTokenDialog,
    show_update_dialog,
    check_update_on_startup,
    check_usb_update_only,
    prompt_github_token,
    get_saved_github_token,
    delete_saved_github_token,
    get_token_storage_info,
    is_keyring_available,
    SETTINGS_TOKEN_KEY,
    KEYRING_SERVICE
)

__all__ = [
    # Version info
    'APP_VERSION',
    'APP_NAME',
    
    # Core update functions
    'UpdateChecker',
    'check_for_update',
    'check_update_complete',
    'get_current_version',
    'get_changelog_text',
    'perform_update',
    'download_update',
    'launch_updater',
    'cleanup_temp_files',
    'cleanup_backup',
    'is_version_supported',
    
    # Error handling
    'UpdateResult',
    'UpdateErrorCode',
    'get_error_message',
    'get_error_title',
    
    # GitHub API
    'GITHUB_OWNER',
    'GITHUB_REPO',
    'set_github_token',
    'get_github_token',
    'clear_github_token',
    'is_github_token_set',
    'validate_github_token',
    'fetch_latest_github_release',
    'fetch_version_json_from_github',
    'get_github_download_info',
    
    # Platform detection
    'CURRENT_PLATFORM',
    'IS_WINDOWS',
    'IS_LINUX',
    'IS_MACOS',
    'VERSION_JSON_PLATFORM',
    
    # USB/Pendrive updates
    'USB_UPDATE_FOLDER_NAME',
    'find_usb_update_directory',
    'load_usb_version_info',
    'get_usb_binary_path',
    'verify_usb_checksum',
    'check_usb_update',
    'copy_usb_update',
    'resolve_update',
    'get_update_source_display_name',
    'check_usb_update_only',
    
    # Dialogs
    'UpdateDialog',
    'GitHubTokenDialog',
    'show_update_dialog',
    'check_update_on_startup',
    'prompt_github_token',
    'get_saved_github_token',
    'delete_saved_github_token',
    'get_token_storage_info',
    'is_keyring_available',
    'SETTINGS_TOKEN_KEY',
    'KEYRING_SERVICE'
]
