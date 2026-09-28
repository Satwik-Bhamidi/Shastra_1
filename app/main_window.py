from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from pages.main_page import MainPage
from pages.preview_page import PreviewPage
from pages.settings_page import SettingsPage
from pages.user_management_page import UserManagementPage
from utils.resource_path import resource_path
from backend.config import SystemConfig
from backend.vision_core import VisionCore
from backend.session_manager import SessionManager
from components.create_menu_bar import create_menu_bar
from update_system import check_update_complete, APP_VERSION
from auth.auth_manager import get_auth_manager
from auth.permissions import is_admin, can_manage_users, can_modify_settings
from auth.session import get_current_session

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = SystemConfig.load()
        
        self.vision_core = VisionCore(self.config)
        
        self.session_manager = SessionManager(self.config, self.vision_core)
        
        # Auth manager reference
        self.auth_manager = get_auth_manager()
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setWindowTitle(self._get_window_title())
        create_menu_bar(self)
        
        icon_path = resource_path("assets/AOC_app_logo.png")
        self.setWindowIcon(QIcon(icon_path))

        self.setMinimumSize(600, 400) 
        self.showMaximized() 


        self.main_page = MainPage(self, self.session_manager)
        self.preview_page = PreviewPage(self, self.session_manager)
        self.settings_page = SettingsPage(self, self.config)
        self.user_management_page = UserManagementPage(self)

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.preview_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.user_management_page)
        
        # Connect user management back signal
        self.user_management_page.back_requested.connect(self._show_settings_page)
        
        # Check if app was just updated and show confirmation
        QTimer.singleShot(500, self.check_for_update_complete)
    
    def _get_window_title(self) -> str:
        """Get window title with current user info."""
        session = get_current_session()
        if session:
            return f"Shastra Proof Yard - {session.username} ({session.role})"
        return "Shastra Proof Yard"
    
    def show_user_management(self):
        """Navigate to user management page."""
        if can_manage_users() or is_admin():
            self.user_management_page.refresh()
            self.stack.setCurrentWidget(self.user_management_page)
        else:
            QMessageBox.warning(
                self,
                "Access Denied",
                "You don't have permission to access User Management."
            )
    
    def _show_settings_page(self):
        """Navigate back to settings page."""
        self.stack.setCurrentWidget(self.settings_page)
    
    def logout(self):
        """Log out current user and return to login screen."""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_manager.logout()
            self.close()
            
            # Restart application with login dialog
            from pages.login_dialog import LoginDialog
            from PyQt5.QtWidgets import QApplication
            
            login_dialog = LoginDialog()
            if login_dialog.exec_() == LoginDialog.Accepted:
                # Create new main window
                new_window = MainWindow()
                new_window.show()

    def check_for_update_complete(self):
        updated_version = check_update_complete()
        
        if updated_version:
            QMessageBox.information(
                self,
                "Update Complete",
                f"<b>Shastra Proof Yard</b> has been successfully updated!<br><br>"
                f"<b>New Version:</b> v{APP_VERSION}<br><br>"
                f"Thank you for keeping your software up to date."
            )
