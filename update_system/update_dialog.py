"""
Shastra Proof Yard - Update Dialog
PyQt5 dialog for showing update information and managing the update process.

Supports three update sources (in priority order):
1. USB/Pendrive (highest priority - for offline/defence environments)
2. GitHub Releases API (for production private repo updates)
3. Local/LAN updates (for testing)

Security: Uses OS keyring for secure token storage (industry standard).
- Linux: Secret Service (GNOME Keyring / KWallet)
- Windows: Windows Credential Manager
- macOS: Keychain
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QMessageBox, QFrame, QWidget,
    QLineEdit, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QIcon
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import logging

from .update_checker import (
    UpdateChecker, get_changelog_text, perform_update, 
    download_update, launch_updater, APP_VERSION,
    set_github_token, get_github_token, validate_github_token,
    is_github_token_set, clear_github_token,
    # USB update functions
    check_usb_update, resolve_update, copy_usb_update,
    find_usb_update_directory, get_update_source_display_name,
    # Error handling classes
    UpdateResult, UpdateErrorCode, get_error_message, get_error_title
)

# Try to import keyring for secure storage
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring not available - token will be stored in plain text")


# ═══════════════════════════════════════════════════════════════════════════════
# Secure Token Storage Configuration
# ═══════════════════════════════════════════════════════════════════════════════
SETTINGS_ORG = "ShastraProofYard"
SETTINGS_APP = "ShastraApp"
SETTINGS_TOKEN_KEY = "github_update_token"

# Keyring service name (appears in OS credential manager)
KEYRING_SERVICE = "ShastraProofYard"
KEYRING_USERNAME = "github_token"


# ═══════════════════════════════════════════════════════════════════════════════
# Secure Token Storage Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _save_token_secure(token: str) -> bool:
    """
    Save token securely using OS keyring.
    Falls back to QSettings if keyring unavailable.
    
    Args:
        token: GitHub token to save
        
    Returns:
        True if saved successfully
    """
    if KEYRING_AVAILABLE:
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
            logging.info("Token saved securely to OS keyring")
            return True
        except Exception as e:
            logging.warning(f"Keyring save failed, using fallback: {e}")
    
    # Fallback to QSettings (less secure, but functional)
    try:
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        settings.setValue(SETTINGS_TOKEN_KEY, token)
        logging.warning("Token saved to QSettings (not encrypted)")
        return True
    except Exception as e:
        logging.error(f"Failed to save token: {e}")
        return False


def _load_token_secure() -> Optional[str]:
    """
    Load token from secure storage.
    Checks keyring first, then falls back to QSettings.
    
    Returns:
        Token string or None if not found
    """
    # Try keyring first
    if KEYRING_AVAILABLE:
        try:
            token = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if token:
                logging.info("Token loaded from OS keyring")
                return token
        except Exception as e:
            logging.warning(f"Keyring load failed: {e}")
    
    # Fallback to QSettings
    try:
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        token = settings.value(SETTINGS_TOKEN_KEY, None)
        if token:
            logging.info("Token loaded from QSettings")
            # Migrate to keyring if available
            if KEYRING_AVAILABLE:
                _migrate_token_to_keyring(token)
            return token
    except Exception as e:
        logging.error(f"Failed to load token: {e}")
    
    return None


def _delete_token_secure() -> bool:
    """
    Delete token from all storage locations.
    
    Returns:
        True if deleted successfully
    """
    success = True
    
    # Delete from keyring
    if KEYRING_AVAILABLE:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            logging.info("Token deleted from OS keyring")
        except keyring.errors.PasswordDeleteError:
            pass  # Token wasn't in keyring
        except Exception as e:
            logging.warning(f"Keyring delete failed: {e}")
            success = False
    
    # Delete from QSettings
    try:
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        settings.remove(SETTINGS_TOKEN_KEY)
        logging.info("Token deleted from QSettings")
    except Exception as e:
        logging.warning(f"QSettings delete failed: {e}")
        success = False
    
    return success


def _migrate_token_to_keyring(token: str) -> None:
    """
    Migrate token from plain QSettings to secure keyring.
    Called automatically when token is loaded from QSettings but keyring is available.
    """
    if not KEYRING_AVAILABLE:
        return
    
    try:
        # Save to keyring
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
        
        # Remove from QSettings
        settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        settings.remove(SETTINGS_TOKEN_KEY)
        
        logging.info("Token migrated from QSettings to secure keyring")
    except Exception as e:
        logging.warning(f"Token migration failed: {e}")


def is_keyring_available() -> bool:
    """
    Check if secure keyring storage is available.
    
    Returns:
        True if keyring is available and functional
    """
    if not KEYRING_AVAILABLE:
        return False
    
    try:
        # Test keyring functionality
        keyring.get_keyring()
        return True
    except Exception:
        return False


class GitHubTokenDialog(QDialog):
    """
    Dialog for entering GitHub personal access token.
    Required for downloading updates from private GitHub repositories.
    """
    
    def __init__(self, parent=None, show_remember: bool = True):
        super().__init__(parent)
        self.token = ""
        self.remember = False
        self.show_remember = show_remember
        
        self.setup_ui()
        self.apply_styles()
        self.load_saved_token()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("GitHub Authentication Required")
        self.setMinimumSize(450, 280)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🔐 GitHub Token Required")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Info text
        info_text = QLabel(
            "To download updates from the private repository,\n"
            "please enter your GitHub Personal Access Token.\n\n"
            "The token needs 'Contents: Read' permission for\n"
            "the releases repository."
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setFont(QFont("Segoe UI", 9))
        layout.addWidget(info_text)
        
        # Token input group
        token_group = QGroupBox("Personal Access Token")
        token_layout = QVBoxLayout(token_group)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("ghp_xxxxxxxxxxxxxxxxxxxx")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.textChanged.connect(self.on_token_changed)
        token_layout.addWidget(self.token_input)
        
        # Show/hide password
        self.show_token_cb = QCheckBox("Show token")
        self.show_token_cb.toggled.connect(self.toggle_token_visibility)
        token_layout.addWidget(self.show_token_cb)
        
        layout.addWidget(token_group)
        
        # Remember token checkbox
        if self.show_remember:
            self.remember_cb = QCheckBox("Remember token for future updates")
            # Update tooltip based on keyring availability
            if KEYRING_AVAILABLE:
                self.remember_cb.setToolTip(
                    "Token will be stored securely in your OS credential manager.\n"
                    "(GNOME Keyring / Windows Credential Manager / macOS Keychain)"
                )
            else:
                self.remember_cb.setToolTip(
                    "⚠️ Secure storage unavailable.\n"
                    "Token will be stored locally (less secure).\n"
                    "Only use on trusted devices."
                )
            layout.addWidget(self.remember_cb)
        
        # Validation status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.reject)
        
        self.validate_button = QPushButton("Validate & Continue")
        self.validate_button.setMinimumWidth(150)
        self.validate_button.setObjectName("validateButton")
        self.validate_button.setEnabled(False)
        self.validate_button.clicked.connect(self.validate_and_accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.validate_button)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        """Apply CSS styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QPushButton#validateButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#validateButton:hover {
                background-color: #45a049;
            }
            QPushButton#validateButton:disabled {
                background-color: #2d5a2d;
                color: #888888;
            }
        """)
    
    def load_saved_token(self):
        """Load previously saved token from secure storage."""
        saved_token = _load_token_secure()
        
        if saved_token:
            self.token_input.setText(saved_token)
            if self.show_remember:
                self.remember_cb.setChecked(True)
    
    def save_token(self, token: str):
        """Save token to secure storage (keyring or fallback)."""
        _save_token_secure(token)
    
    def clear_saved_token(self):
        """Clear saved token from all storage locations."""
        _delete_token_secure()
    
    def on_token_changed(self, text: str):
        """Handle token input change."""
        # Enable validate button if token looks valid (starts with ghp_ or github_pat_)
        is_valid_format = (
            text.startswith("ghp_") or 
            text.startswith("github_pat_") or
            len(text) > 20
        )
        self.validate_button.setEnabled(is_valid_format)
        self.status_label.setText("")
    
    def toggle_token_visibility(self, show: bool):
        """Toggle token visibility."""
        self.token_input.setEchoMode(
            QLineEdit.Normal if show else QLineEdit.Password
        )
    
    def validate_and_accept(self):
        """Validate token and accept dialog if valid."""
        token = self.token_input.text().strip()
        
        if not token:
            self.status_label.setText("⚠️ Please enter a token")
            self.status_label.setStyleSheet("color: #FF5722;")
            return
        
        self.status_label.setText("🔄 Validating token...")
        self.status_label.setStyleSheet("color: #2196F3;")
        self.validate_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Process events to update UI
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Validate the token
        is_valid, message = validate_github_token(token)
        
        if is_valid:
            self.token = token
            self.remember = self.show_remember and self.remember_cb.isChecked()
            
            # Save or clear token based on checkbox
            if self.remember:
                self.save_token(token)
            else:
                self.clear_saved_token()
            
            # Set the token globally
            set_github_token(token)
            
            self.status_label.setText("✅ Token validated successfully!")
            self.status_label.setStyleSheet("color: #4CAF50;")
            
            # Small delay to show success message
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, self.accept)
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #FF5722;")
            self.validate_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
    
    def get_token(self) -> str:
        """Get the validated token."""
        return self.token


def get_saved_github_token() -> Optional[str]:
    """Get saved GitHub token from secure storage."""
    return _load_token_secure()


def delete_saved_github_token() -> bool:
    """Delete saved GitHub token from secure storage."""
    return _delete_token_secure()


def get_token_storage_info() -> Dict[str, Any]:
    """
    Get information about token storage security.
    
    Returns:
        Dictionary with storage info:
        - is_secure: True if using keyring
        - backend: Name of storage backend
        - has_token: True if token is stored
    """
    info = {
        "is_secure": False,
        "backend": "QSettings (plain text)",
        "has_token": False
    }
    
    if KEYRING_AVAILABLE:
        try:
            kr = keyring.get_keyring()
            info["is_secure"] = True
            info["backend"] = f"OS Keyring ({type(kr).__name__})"
        except Exception:
            pass
    
    info["has_token"] = get_saved_github_token() is not None
    
    return info


class DownloadThread(QThread):
    """
    Background thread for downloading/copying updates.
    
    Supports:
    - USB updates (direct copy from pendrive)
    - GitHub downloads (authenticated API)
    - HTTP downloads (public URLs)
    
    Emits detailed error information for user-friendly notifications.
    """
    
    progress = pyqtSignal(int, int)  # downloaded/copied, total
    finished = pyqtSignal(bool, str, object)  # success, message, UpdateResult/error_code
    
    def __init__(self, update_info: Dict[str, Any]):
        super().__init__()
        self.update_info = update_info
    
    def run(self):
        """Run the download/copy in background."""
        try:
            is_usb_update = self.update_info.get("is_usb_update", False)
            sha256 = self.update_info.get("sha256", "")
            
            # ═══════════════════════════════════════════════════════════════
            # USB UPDATE - Copy from pendrive (no network)
            # ═══════════════════════════════════════════════════════════════
            if is_usb_update:
                usb_binary_path = self.update_info.get("usb_binary_path", "")
                if not usb_binary_path:
                    self.finished.emit(
                        False, 
                        "No USB binary path provided",
                        UpdateErrorCode.FILE_NOT_FOUND
                    )
                    return
                
                result = copy_usb_update(
                    Path(usb_binary_path),
                    progress_callback=self._progress_callback,
                    sha256_expected=sha256 if sha256 else None
                )
                
                # Handle UpdateResult object
                if isinstance(result, UpdateResult):
                    if result.success:
                        self.finished.emit(True, str(result.file_path), result)
                    else:
                        self.finished.emit(False, result.error_message, result)
                # Legacy Path return (backward compatibility)
                elif result:
                    self.finished.emit(True, str(result), None)
                else:
                    self.finished.emit(
                        False, 
                        "USB copy failed - unknown error",
                        UpdateErrorCode.UNKNOWN_ERROR
                    )
                return
            
            # ═══════════════════════════════════════════════════════════════
            # NETWORK UPDATE - Download from GitHub or HTTP
            # ═══════════════════════════════════════════════════════════════
            download_url = self.update_info.get("download_url", "")
            is_github_download = self.update_info.get("is_github_download", False)
            
            if not download_url:
                self.finished.emit(
                    False, 
                    "No download URL provided",
                    UpdateErrorCode.DOWNLOAD_FAILED
                )
                return
            
            result = download_update(
                download_url,
                progress_callback=self._progress_callback,
                sha256_expected=sha256 if sha256 else None,
                is_github_download=is_github_download
            )
            
            # Handle UpdateResult object (future-proof)
            if isinstance(result, UpdateResult):
                if result.success:
                    self.finished.emit(True, str(result.file_path), result)
                else:
                    self.finished.emit(False, result.error_message, result)
            # Legacy Path return
            elif result:
                self.finished.emit(True, str(result), None)
            else:
                # Determine if it was likely a SHA256 error
                # (download_update currently returns None for SHA256 failures)
                if sha256:
                    # If SHA256 was provided and result is None, likely a hash mismatch
                    self.finished.emit(
                        False,
                        get_error_message(UpdateErrorCode.SHA256_MISMATCH),
                        UpdateErrorCode.SHA256_MISMATCH
                    )
                else:
                    self.finished.emit(
                        False, 
                        "Download failed",
                        UpdateErrorCode.DOWNLOAD_FAILED
                    )
                
        except Exception as e:
            self.finished.emit(
                False, 
                str(e),
                UpdateErrorCode.UNKNOWN_ERROR
            )
    
    def _progress_callback(self, downloaded: int, total: int):
        """Emit progress signal."""
        self.progress.emit(downloaded, total)


class UpdateDialog(QDialog):
    """
    Modern update dialog for Shastra Proof Yard.
    
    Shows:
    - Current and new version
    - Update source (USB/GitHub/Local)
    - Changelog
    - Download/Copy progress
    - Update/Skip buttons
    """
    
    def __init__(self, update_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_thread: Optional[DownloadThread] = None
        self.download_completed = False
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Update Available")
        self.setMinimumSize(520, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🚀 A New Version is Available!")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Version info
        version_frame = QFrame()
        version_frame.setObjectName("versionFrame")
        version_layout = QVBoxLayout(version_frame)
        
        # Version numbers row
        version_row = QHBoxLayout()
        
        current_ver = self.update_info.get("current_version", APP_VERSION)
        new_ver = self.update_info.get("new_version", "")
        
        current_label = QLabel(f"Current: v{current_ver}")
        current_label.setFont(QFont("Segoe UI", 11))
        
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        arrow_label.setStyleSheet("color: #4CAF50;")
        
        new_label = QLabel(f"New: v{new_ver}")
        new_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        new_label.setStyleSheet("color: #4CAF50;")
        
        version_row.addStretch()
        version_row.addWidget(current_label)
        version_row.addWidget(arrow_label)
        version_row.addWidget(new_label)
        version_row.addStretch()
        
        version_layout.addLayout(version_row)
        
        # Update source row
        source = self.update_info.get("source", "unknown")
        source_display = get_update_source_display_name(self.update_info)
        
        # Choose icon based on source
        if source == "usb":
            source_icon = "💾"  # USB/disk icon
            source_color = "#2196F3"  # Blue for USB
        elif source == "github":
            source_icon = "☁️"  # Cloud icon
            source_color = "#9C27B0"  # Purple for GitHub
        else:
            source_icon = "📁"  # Folder icon
            source_color = "#FF9800"  # Orange for local
        
        source_label = QLabel(f"{source_icon} Update source: {source_display}")
        source_label.setFont(QFont("Segoe UI", 10))
        source_label.setStyleSheet(f"color: {source_color};")
        source_label.setAlignment(Qt.AlignCenter)
        version_layout.addWidget(source_label)
        
        # For USB updates, show the USB path
        if source == "usb":
            usb_dir = self.update_info.get("usb_update_dir", "")
            if usb_dir:
                # Extract just the USB drive name for cleaner display
                try:
                    usb_path = Path(usb_dir)
                    usb_name = usb_path.parent.name  # Get USB drive name
                    usb_hint = QLabel(f"📍 Drive: {usb_name}")
                    usb_hint.setFont(QFont("Segoe UI", 9))
                    usb_hint.setStyleSheet("color: #888888;")
                    usb_hint.setAlignment(Qt.AlignCenter)
                    version_layout.addWidget(usb_hint)
                except:
                    pass
        
        layout.addWidget(version_frame)
        
        # Changelog
        changelog_label = QLabel("What's New:")
        changelog_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(changelog_label)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setPlainText(get_changelog_text(self.update_info))
        self.changelog_text.setMaximumHeight(150)
        layout.addWidget(self.changelog_text)
        
        # Progress section (hidden initially)
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_label = QLabel("Preparing download...")
        self.progress_label.setFont(QFont("Segoe UI", 9))
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_widget.setVisible(False)
        layout.addWidget(self.progress_widget)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Mandatory update warning
        if self.update_info.get("mandatory", False):
            mandatory_label = QLabel("⚠️ This is a mandatory update")
            mandatory_label.setStyleSheet("color: #FF5722; font-weight: bold;")
            mandatory_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(mandatory_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.skip_button = QPushButton("Skip for Now")
        self.skip_button.setMinimumWidth(120)
        self.skip_button.clicked.connect(self.reject)
        
        # Disable skip for mandatory updates
        if self.update_info.get("mandatory", False):
            self.skip_button.setEnabled(False)
            self.skip_button.setToolTip("This update is mandatory")
        
        self.update_button = QPushButton("Update Now")
        self.update_button.setMinimumWidth(120)
        self.update_button.setObjectName("updateButton")
        self.update_button.clicked.connect(self.start_update)
        
        button_layout.addStretch()
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.update_button)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        """Apply CSS styles to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QFrame#versionFrame {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 10px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 5px;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
            QPushButton#updateButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#updateButton:hover {
                background-color: #45a049;
            }
        """)
    
    def start_update(self):
        """Start the update download/copy process."""
        self.update_button.setEnabled(False)
        self.skip_button.setEnabled(False)
        self.progress_widget.setVisible(True)
        
        # Set appropriate status message based on update source
        is_usb = self.update_info.get("is_usb_update", False)
        if is_usb:
            self.status_label.setText("💾 Copying update from USB...")
        else:
            self.status_label.setText("☁️ Downloading update...")
        
        self.download_thread = DownloadThread(self.update_info)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()
    
    def on_download_progress(self, downloaded: int, total: int):
        """Handle download/copy progress updates."""
        is_usb = self.update_info.get("is_usb_update", False)
        action = "Copying" if is_usb else "Downloading"
        
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)
            
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.progress_label.setText(
                f"{action}: {downloaded_mb:.1f} MB / {total_mb:.1f} MB"
            )
        else:
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_label.setText(f"{action}...")
    
    def on_download_finished(self, success: bool, message: str, error_info: object = None):
        """
        Handle download/copy completion with detailed error handling.
        
        Args:
            success: Whether the operation succeeded
            message: Status message or error description
            error_info: UpdateResult object or UpdateErrorCode enum for detailed error handling
        """
        self.download_thread = None
        is_usb = self.update_info.get("is_usb_update", False)
        
        if success:
            self.download_completed = True
            self.progress_bar.setValue(100)
            self.progress_label.setText("Copy complete!" if is_usb else "Download complete!")
            self.status_label.setText("Installing update... The application will restart.")
            self.status_label.setStyleSheet("color: #4CAF50;")
            
            # Launch updater and exit
            if launch_updater(update_info=self.update_info):
                source_text = "USB drive" if is_usb else "server"
                QMessageBox.information(
                    self,
                    "Update Starting",
                    f"Update copied from {source_text} successfully!\n\n"
                    "The application will now close to complete the update.\n"
                    "It will restart automatically after the update is installed."
                )
                sys.exit(0)
            else:
                self.status_label.setText("Failed to launch updater")
                self.status_label.setStyleSheet("color: #FF5722;")
                self.update_button.setEnabled(True)
                if not self.update_info.get("mandatory", False):
                    self.skip_button.setEnabled(True)
        else:
            # ═══════════════════════════════════════════════════════════════
            # Enhanced Error Handling with User-Friendly Dialogs
            # ═══════════════════════════════════════════════════════════════
            
            error_code = None
            
            # Extract error code from error_info
            if isinstance(error_info, UpdateResult):
                error_code = error_info.error_code
            elif isinstance(error_info, UpdateErrorCode):
                error_code = error_info
            
            # Show appropriate error dialog based on error type
            if error_code:
                self._show_error_dialog(error_code, message, is_usb)
            else:
                # Generic error fallback
                QMessageBox.warning(
                    self,
                    "Update Failed",
                    f"The update could not be completed.\n\n"
                    f"Error: {message}\n\n"
                    "Please try again later."
                )
            
            # Update UI
            self.progress_widget.setVisible(False)
            self.status_label.setText("Update failed")
            self.status_label.setStyleSheet("color: #FF5722;")
            self.update_button.setEnabled(True)
            if not self.update_info.get("mandatory", False):
                self.skip_button.setEnabled(True)
    
    def _show_error_dialog(self, error_code: UpdateErrorCode, message: str, is_usb: bool):
        """
        Show an appropriate error dialog based on the error code.
        
        Different error types get different visual treatments:
        - Security errors (SHA256): Critical warning with red styling
        - Network errors: Standard warning
        - File errors: Standard warning with troubleshooting tips
        """
        source_name = "USB drive" if is_usb else "server"
        
        # ═══════════════════════════════════════════════════════════════
        # SECURITY ERRORS - Critical (red alert, prominent warning)
        # ═══════════════════════════════════════════════════════════════
        if error_code == UpdateErrorCode.SHA256_MISMATCH:
            # Create a custom critical dialog for security issues
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("⚠️ Security Alert - Update Cancelled")
            msg_box.setText(
                "<b style='color: #FF5722; font-size: 14px;'>"
                "File Integrity Verification Failed!"
                "</b>"
            )
            msg_box.setInformativeText(
                f"The update file from {source_name} failed security verification.\n\n"
                "<b>What this means:</b>\n"
                "• The file may have been corrupted during transfer\n"
                "• The file may have been tampered with\n"
                "• The download may have been incomplete\n\n"
                "<b>What to do:</b>\n"
                f"{'• Try ejecting and reinserting the USB drive' if is_usb else '• Check your internet connection'}\n"
                "• Try the update again\n"
                "• If the problem persists, contact support\n\n"
                "<b>Your current version remains unchanged and secure.</b>"
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1e1e1e;
                }
                QLabel {
                    color: #ffffff;
                    min-width: 400px;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 20px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
            """)
            msg_box.exec_()
            
        # ═══════════════════════════════════════════════════════════════
        # NETWORK ERRORS
        # ═══════════════════════════════════════════════════════════════
        elif error_code in [
            UpdateErrorCode.NETWORK_ERROR,
            UpdateErrorCode.DOWNLOAD_FAILED,
            UpdateErrorCode.CONNECTION_TIMEOUT,
            UpdateErrorCode.AUTHENTICATION_FAILED
        ]:
            QMessageBox.warning(
                self,
                get_error_title(error_code),
                f"{get_error_message(error_code)}\n\n"
                "Tips:\n"
                "• Check your internet connection\n"
                "• Try again in a few minutes\n"
                "• If using GitHub, verify your access token"
            )
            
        # ═══════════════════════════════════════════════════════════════
        # FILE ERRORS
        # ═══════════════════════════════════════════════════════════════
        elif error_code in [
            UpdateErrorCode.FILE_NOT_FOUND,
            UpdateErrorCode.PATH_NOT_ACCESSIBLE,
            UpdateErrorCode.PERMISSION_DENIED,
            UpdateErrorCode.DISK_FULL
        ]:
            tips = "Tips:\n"
            if is_usb:
                tips += "• Ensure the USB drive is properly connected\n"
                tips += "• Check that SHASTRA_UPDATE folder exists on the drive\n"
                tips += "• Verify the update files are not corrupted\n"
            else:
                tips += "• Check available disk space\n"
                tips += "• Ensure you have write permissions to the app folder\n"
            
            QMessageBox.warning(
                self,
                get_error_title(error_code),
                f"{get_error_message(error_code)}\n\n{tips}"
            )
            
        # ═══════════════════════════════════════════════════════════════
        # OTHER ERRORS
        # ═══════════════════════════════════════════════════════════════
        else:
            QMessageBox.warning(
                self,
                "Update Failed",
                f"{get_error_message(error_code)}\n\n"
                f"Error details: {message}"
            )
    
    def closeEvent(self, event):
        """Handle dialog close."""
        if self.download_thread and self.download_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Cancel Download?",
                "A download is in progress. Are you sure you want to cancel?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()


def show_update_dialog(
    parent=None, 
    remote_url: Optional[str] = None,
    use_github: bool = False,
    check_usb: bool = True
) -> bool:
    """
    Check for updates and show dialog if available.
    
    Checks all configured sources in priority order:
    1. USB/Pendrive (if check_usb=True)
    2. GitHub (if use_github=True and token available)
    3. Local/URL (if remote_url provided)
    
    Args:
        parent: Parent widget
        remote_url: Optional remote version.json URL
        use_github: If True, use GitHub Releases API
        check_usb: If True, check USB/pendrive first (highest priority)
        
    Returns:
        True if update was started, False otherwise
    """
    # For GitHub updates, ensure token is set (only needed if USB check fails)
    if use_github:
        # Try to load saved token first
        saved_token = get_saved_github_token()
        if saved_token:
            set_github_token(saved_token)
    
    # Use the UpdateChecker which handles priority (USB > GitHub > Local)
    checker = UpdateChecker(remote_url, use_github=use_github, check_usb=check_usb)
    update_info = checker.check()
    
    # If no update found but GitHub is enabled and no token, prompt for token
    if not update_info and use_github and not is_github_token_set():
        token_dialog = GitHubTokenDialog(parent)
        if token_dialog.exec_() == QDialog.Accepted:
            # Re-check with the new token
            update_info = checker.check_github_only()
    
    if update_info:
        dialog = UpdateDialog(update_info, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted
    
    return False


def check_update_on_startup(
    parent=None, 
    remote_url: Optional[str] = None, 
    silent: bool = True,
    use_github: bool = False,
    check_usb: bool = True
):
    """
    Check for updates on application startup.
    
    Checks all configured sources in priority order:
    1. USB/Pendrive (if check_usb=True) - NO NETWORK REQUIRED
    2. GitHub (if use_github=True and token available)
    3. Local/URL (if remote_url provided)
    
    Args:
        parent: Parent widget
        remote_url: Optional remote version.json URL
        silent: If True, don't show "no update" message
        use_github: If True, use GitHub Releases API
        check_usb: If True, check USB/pendrive first (highest priority, offline)
    """
    # For GitHub updates, try to use saved token silently
    if use_github:
        saved_token = get_saved_github_token()
        if saved_token:
            set_github_token(saved_token)
    
    # Use UpdateChecker which handles priority (USB > GitHub > Local)
    checker = UpdateChecker(remote_url, use_github=use_github, check_usb=check_usb)
    
    try:
        update_info = checker.check()
    except Exception as e:
        if not silent:
            QMessageBox.warning(
                parent,
                "Update Check Failed",
                f"Failed to check for updates:\n{str(e)}"
            )
        return
    
    # If no USB update found and GitHub enabled but no token, optionally prompt
    if not update_info and use_github and not is_github_token_set() and not silent:
        # Only prompt for token in non-silent mode
        token_dialog = GitHubTokenDialog(parent)
        if token_dialog.exec_() == QDialog.Accepted:
            # Re-check with the new token
            try:
                update_info = checker.check_github_only()
            except Exception:
                pass
    
    if update_info:
        dialog = UpdateDialog(update_info, parent)
        dialog.exec_()
    elif not silent:
        QMessageBox.information(
            parent,
            "No Updates",
            f"You are running the latest version (v{APP_VERSION})."
        )


def check_usb_update_only(parent=None, silent: bool = True) -> bool:
    """
    Check only USB/pendrive for updates.
    
    Use this for fully offline environments where no network is available.
    No token or network required.
    
    Args:
        parent: Parent widget
        silent: If True, don't show "no update" message
        
    Returns:
        True if update was started, False otherwise
    """
    update_info = check_usb_update()
    
    if update_info:
        dialog = UpdateDialog(update_info, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted
    elif not silent:
        QMessageBox.information(
            parent,
            "No USB Update Found",
            "No update found on connected USB drives.\n\n"
            "Make sure your USB drive contains a folder named:\n"
            "SHASTRA_UPDATE\n\n"
            "With the update files inside."
        )
    
    return False


def prompt_github_token(parent=None) -> bool:
    """
    Show GitHub token dialog and return whether a valid token was entered.
    
    Args:
        parent: Parent widget
        
    Returns:
        True if valid token was entered, False otherwise
    """
    dialog = GitHubTokenDialog(parent)
    return dialog.exec_() == QDialog.Accepted
