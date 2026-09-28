"""
SHASTRA Proof Yard - Main Entry Point
Application initialization with authentication flow.
"""

import sys


def main():
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    
    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Shastra Proof Yard")
    app.setOrganizationName("Shastra")
    
    # Import auth components
    from auth.auth_manager import get_auth_manager
    from pages.login_dialog import LoginDialog
    
    # Initialize authentication system
    auth_manager = get_auth_manager()
    bootstrap_result = auth_manager.initialize()
    
    if not bootstrap_result.success:
        QMessageBox.critical(
            None,
            "Initialization Error",
            f"Failed to initialize application:\n{bootstrap_result.error}"
        )
        return 1
    
    # Show login dialog
    login_dialog = LoginDialog(
        parent=None,
        show_first_run_info=bootstrap_result.is_first_run
    )
    
    if login_dialog.exec_() != LoginDialog.Accepted:
        # User closed login dialog without authenticating
        return 0
    
    # Authentication successful - show main window
    from app.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())