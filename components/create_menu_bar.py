"""
Menu bar creation and styling for SHASTRA Proof Yard application.
"""

from PyQt5.QtWidgets import QAction, QMessageBox, QMenu, QActionGroup
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtCore import Qt, QSettings
from update_system import APP_VERSION, check_update_on_startup, show_update_dialog

from components.menu_helpers import (
    RecentFilesManager,
    export_to_csv,
    print_report,
    open_reports_folder,
    recalculate_stats,
    clear_all_shots,
    show_sensitivity_dialog,
    show_session_history,
    show_aruco_generator,
    show_image_enhancement,
    toggle_theme,
    reset_all_settings,
    show_shortcuts_dialog,
)


def create_menu_bar(self):
    menubar = self.menuBar()
    menubar.setNativeMenuBar(False)
    
    # Store actions for later reference
    self.menu_actions = {}
    
    file_menu = menubar.addMenu("&File")
    
    new_action = QAction("&New Report", self)
    new_action.setShortcut(QKeySequence.New)
    new_action.setStatusTip("Create a new report")
    new_action.triggered.connect(lambda: reset_form(self))
    
    open_action = QAction("&Open Images...", self)
    open_action.setShortcut(QKeySequence.Open)
    open_action.setStatusTip("Open images for analysis")
    open_action.triggered.connect(lambda: open_images(self))
    
    # Recent Files submenu
    self.recent_menu = QMenu("Open &Recent", self)
    update_recent_menu(self)
    
    file_menu.addAction(new_action)
    file_menu.addAction(open_action)
    file_menu.addMenu(self.recent_menu)
    file_menu.addSeparator()
    
    # Export options
    export_pdf_action = QAction("&Export Report (PDF)...", self)
    export_pdf_action.setShortcut("Ctrl+E")
    export_pdf_action.setStatusTip("Export report to PDF")
    export_pdf_action.triggered.connect(lambda: export_pdf_from_menu(self))
    
    export_csv_action = QAction("Export to &CSV...", self)
    export_csv_action.setShortcut("Ctrl+Shift+E")
    export_csv_action.setStatusTip("Export shot data to CSV file")
    export_csv_action.triggered.connect(lambda: export_to_csv(self))
    
    print_action = QAction("&Print Report...", self)
    print_action.setShortcut(QKeySequence.Print)
    print_action.setStatusTip("Print the current report")
    print_action.triggered.connect(lambda: print_report(self))
    
    file_menu.addAction(export_pdf_action)
    file_menu.addAction(export_csv_action)
    file_menu.addSeparator()
    file_menu.addAction(print_action)
    file_menu.addSeparator()
    
    open_folder_action = QAction("Open Reports &Folder", self)
    open_folder_action.setStatusTip("Open the reports folder in file explorer")
    open_folder_action.triggered.connect(lambda: open_reports_folder(self))
    
    file_menu.addAction(open_folder_action)
    file_menu.addSeparator()
    
    exit_action = QAction("E&xit", self)
    exit_action.setShortcut(QKeySequence.Quit)
    exit_action.setStatusTip("Exit the application")
    exit_action.triggered.connect(self.close)
    
    file_menu.addAction(exit_action)
    
    view_menu = menubar.addMenu("&View")
    
    form_view = QAction("&Main Form", self)
    form_view.setShortcut("Ctrl+1")
    form_view.setStatusTip("Switch to main data entry form")
    form_view.triggered.connect(lambda: self.stack.setCurrentWidget(self.main_page))
    
    preview_view = QAction("&Preview Page", self)
    preview_view.setShortcut("Ctrl+2")
    preview_view.setStatusTip("Switch to report preview")
    preview_view.triggered.connect(lambda: navigate_to_preview(self))
    
    settings_view = QAction("&Settings Page", self)
    settings_view.setShortcut("Ctrl+3")
    settings_view.setStatusTip("Switch to settings page")
    settings_view.triggered.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
    
    view_menu.addAction(form_view)
    view_menu.addAction(preview_view)
    view_menu.addAction(settings_view)
    view_menu.addSeparator()
    
    # Toggle fullscreen
    fullscreen_action = QAction("&Full Screen", self)
    fullscreen_action.setShortcut("F11")
    fullscreen_action.setCheckable(True)
    fullscreen_action.setStatusTip("Toggle full screen mode")
    fullscreen_action.triggered.connect(lambda checked: 
        self.showFullScreen() if checked else self.showNormal())
    view_menu.addAction(fullscreen_action)
    
    analysis_menu = menubar.addMenu("&Analysis")
    
    recalc_action = QAction("&Recalculate Statistics", self)
    recalc_action.setShortcut("Ctrl+R")
    recalc_action.setStatusTip("Recalculate statistics for current session")
    recalc_action.triggered.connect(lambda: recalculate_stats(self))
    
    clear_shots_action = QAction("&Clear All Shots", self)
    clear_shots_action.setShortcut("Ctrl+Shift+C")
    clear_shots_action.setStatusTip("Remove all detected shots")
    clear_shots_action.triggered.connect(lambda: clear_all_shots(self))
    
    sensitivity_action = QAction("Detection &Sensitivity...", self)
    sensitivity_action.setStatusTip("Adjust shot detection sensitivity")
    sensitivity_action.triggered.connect(lambda: show_sensitivity_dialog(self))
    
    analysis_menu.addAction(recalc_action)
    analysis_menu.addAction(clear_shots_action)
    analysis_menu.addSeparator()
    analysis_menu.addAction(sensitivity_action)
    
    reports_menu = menubar.addMenu("&Reports")
    
    history_action = QAction("&Session History...", self)
    history_action.setShortcut("Ctrl+H")
    history_action.setStatusTip("View and manage past sessions")
    history_action.triggered.connect(lambda: show_session_history(self))
    
    open_reports_action = QAction("&Open Reports Folder", self)
    open_reports_action.setStatusTip("Open the reports folder")
    open_reports_action.triggered.connect(lambda: open_reports_folder(self))
    
    reports_menu.addAction(history_action)
    reports_menu.addSeparator()
    reports_menu.addAction(open_reports_action)
    
    tools_menu = menubar.addMenu("&Tools")
    
    aruco_action = QAction("&ArUco Marker Generator...", self)
    aruco_action.setShortcut("Ctrl+M")
    aruco_action.setStatusTip("Generate printable ArUco markers")
    aruco_action.triggered.connect(lambda: show_aruco_generator(self))
    
    enhance_action = QAction("&Image Enhancement...", self)
    enhance_action.setStatusTip("Adjust brightness and contrast")
    enhance_action.triggered.connect(lambda: show_image_enhancement(self))
    
    tools_menu.addAction(aruco_action)
    tools_menu.addAction(enhance_action)
    
    settings_menu = menubar.addMenu("&Settings")
    
    system_config = QAction("&System Configuration...", self)
    system_config.setShortcut("Ctrl+,")
    system_config.setStatusTip("Configure system settings")
    system_config.triggered.connect(lambda: self.stack.setCurrentWidget(self.settings_page))
    
    # Theme submenu with action group (only one can be checked)
    theme_menu = QMenu("&Theme", self)
    theme_group = QActionGroup(self)
    theme_group.setExclusive(True)
    
    # Load saved theme preference
    theme_settings = QSettings("Shastra_Proof_Yard", "appearance")
    is_dark = theme_settings.value("dark_mode", False, type=bool)
    
    light_theme = QAction("☀ &Light Theme", self)
    light_theme.setCheckable(True)
    light_theme.setChecked(not is_dark)
    light_theme.triggered.connect(lambda: toggle_theme(self, False))
    theme_group.addAction(light_theme)
    
    dark_theme = QAction("🌙 &Dark Theme", self)
    dark_theme.setCheckable(True)
    dark_theme.setChecked(is_dark)
    dark_theme.triggered.connect(lambda: toggle_theme(self, True))
    theme_group.addAction(dark_theme)
    
    # Store references for later updates
    self.light_theme_action = light_theme
    self.dark_theme_action = dark_theme
    
    theme_menu.addAction(light_theme)
    theme_menu.addAction(dark_theme)
    
    # Apply saved theme on startup
    if is_dark:
        toggle_theme(self, True)
    
    reset_settings_action = QAction("&Reset to Defaults", self)
    reset_settings_action.setStatusTip("Reset all settings to default values")
    reset_settings_action.triggered.connect(lambda: reset_all_settings(self))
    
    settings_menu.addAction(system_config)
    settings_menu.addMenu(theme_menu)
    settings_menu.addSeparator()
    settings_menu.addAction(reset_settings_action)
    
    account_menu = menubar.addMenu("&Account")
    
    # Show current user info
    from auth.session import get_current_session
    session = get_current_session()
    if session:
        user_info = QAction(f"{session.username} ({session.role})", self)
        user_info.setEnabled(False)
        account_menu.addAction(user_info)
        account_menu.addSeparator()
    
    change_password_action = QAction("&Change Password...", self)
    change_password_action.setStatusTip("Change your password")
    change_password_action.triggered.connect(lambda: show_change_password_dialog(self))
    account_menu.addAction(change_password_action)
    
    # User Management (Admin only)
    from auth.permissions import can_manage_users, is_admin
    if can_manage_users() or is_admin():
        user_mgmt_action = QAction("&User Management...", self)
        user_mgmt_action.setStatusTip("Manage users")
        user_mgmt_action.triggered.connect(lambda: self.show_user_management())
        account_menu.addAction(user_mgmt_action)
    
    account_menu.addSeparator()
    
    logout_action = QAction("&Logout", self)
    logout_action.setShortcut("Ctrl+Shift+L")
    logout_action.setStatusTip("Log out of the application")
    logout_action.triggered.connect(lambda: self.logout())
    account_menu.addAction(logout_action)
    
    help_menu = menubar.addMenu("&Help")
    
    shortcuts_action = QAction("&Keyboard Shortcuts...", self)
    shortcuts_action.setShortcut("Ctrl+/")
    shortcuts_action.setStatusTip("View keyboard shortcuts")
    shortcuts_action.triggered.connect(lambda: show_shortcuts_dialog(self))
    
    documentation = QAction("&Documentation", self)
    documentation.setShortcut("F1")
    documentation.setStatusTip("View user documentation")
    documentation.triggered.connect(lambda: show_documentation(self))
    
    check_updates = QAction("Check for &Updates...", self)
    check_updates.setStatusTip("Check for application updates")
    check_updates.triggered.connect(lambda: check_for_updates_menu(self))
    
    about_action = QAction("&About SHASTRA", self)
    about_action.setStatusTip("About this application")
    about_action.triggered.connect(lambda: show_about(self))
    
    help_menu.addAction(shortcuts_action)
    help_menu.addAction(documentation)
    help_menu.addSeparator()
    help_menu.addAction(check_updates)
    help_menu.addSeparator()
    help_menu.addAction(about_action)
    
    menubar.setStyleSheet("""
        QMenuBar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #d0d0d0;
            padding: 4px;
            font-size: 13px;
        }
        
        QMenuBar::item {
            padding: 6px 12px;
            background: transparent;
            border-radius: 3px;
            color: #333333;
        }
        
        QMenuBar::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        
        QMenuBar::item:pressed {
            background-color: #bbdefb;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 6px 0px;
            font-size: 13px;
        }
        
        QMenu::item {
            padding: 8px 32px 8px 24px;
            color: #333333;
            background-color: transparent;
            border-radius: 4px;
            margin: 2px 6px;
        }
        
        QMenu::item:selected {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        
        QMenu::item:disabled {
            color: #999999;
            background-color: transparent;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #e0e0e0;
            margin: 6px 12px;
        }
        
        QMenu::icon {
            padding-left: 8px;
        }
        
        QMenu::indicator {
            width: 16px;
            height: 16px;
            margin-left: 6px;
        }
    """)


# HELPER FUNCTIONS

def update_recent_menu(self):
    """Update the recent files menu"""
    self.recent_menu.clear()
    
    manager = RecentFilesManager()
    recent_files = manager.get_recent_files()
    
    if not recent_files:
        no_recent = QAction("No recent files", self)
        no_recent.setEnabled(False)
        self.recent_menu.addAction(no_recent)
    else:
        for entry in recent_files:
            parts = entry.split("|")
            if len(parts) == 2:
                before, after = parts
                # Show just filename
                from pathlib import Path
                display = f"{Path(before).name} / {Path(after).name}"
                action = QAction(display, self)
                action.setData(entry)
                action.triggered.connect(lambda checked, e=entry: open_recent_files(self, e))
                self.recent_menu.addAction(action)
    
    self.recent_menu.addSeparator()
    
    clear_action = QAction("Clear Recent", self)
    clear_action.triggered.connect(lambda: clear_recent_files(self))
    self.recent_menu.addAction(clear_action)


def open_recent_files(self, entry):
    """Open a recent file pair"""
    parts = entry.split("|")
    if len(parts) != 2:
        return
    
    before_path, after_path = parts
    
    # Check if files exist
    from pathlib import Path
    if not Path(before_path).exists() or not Path(after_path).exists():
        QMessageBox.warning(
            self,
            "Files Not Found",
            "One or more of the recent files no longer exist."
        )
        return
    
    # Switch to main page and set images
    self.stack.setCurrentWidget(self.main_page)
    
    # Set images in upload buttons
    if hasattr(self.main_page, 'before_btn'):
        self.main_page.before_btn.upload_btn.setToolTip(before_path)
        self.main_page.before_btn.has_image = True
        self.main_page.before_btn.image_path = before_path
    
    if hasattr(self.main_page, 'after_btn'):
        self.main_page.after_btn.upload_btn.setToolTip(after_path)
        self.main_page.after_btn.has_image = True
        self.main_page.after_btn.image_path = after_path


def clear_recent_files(self):
    """Clear the recent files list"""
    manager = RecentFilesManager()
    manager.clear_recent()
    update_recent_menu(self)


def export_pdf_from_menu(self):
    """Export PDF from menu - same as save results from preview"""
    if not hasattr(self, 'session_manager') or self.session_manager.shot_warp is None:
        QMessageBox.warning(
            self,
            "No Data",
            "No analysis data available to export.\nPlease run an analysis first."
        )
        return
    
    # Navigate to preview and trigger save
    self.stack.setCurrentWidget(self.preview_page)
    self.preview_page.save_results()


def reset_form(self):
    """Reset all form fields to empty state"""
    reply = QMessageBox.question(
        self,
        "New Report",
        "Are you sure you want to create a new report?\nAll unsaved changes will be lost.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        if hasattr(self, 'main_page') and hasattr(self.main_page, 'clear_session'):
            self.main_page.clear_session()
        
        if hasattr(self, 'stack') and hasattr(self, 'main_page'):
            self.stack.setCurrentWidget(self.main_page)
        
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage("New report created", 3000)


def navigate_to_preview(self):
    """Navigate to preview page only if analysis has been done"""
    if hasattr(self, 'session_manager') and self.session_manager.shot_warp is not None:
        self.stack.setCurrentWidget(self.preview_page)
    else:
        QMessageBox.warning(
            self,
            "No Analysis Data",
            "Please upload before and after images and click 'Generate Result' first.\n\n"
            "The preview page requires processed analysis data to display.",
            QMessageBox.Ok
        )


def open_images(self):
    """Guide user to upload images"""
    self.stack.setCurrentWidget(self.main_page)
    QMessageBox.information(
        self,
        "Open Images",
        "Use the upload buttons to add images:\n\n"
        "• Before Firing: Upload the initial target image\n"
        "• After Firing: Upload the post-firing target image\n\n"
        "Supported formats: JPG, PNG, BMP",
        QMessageBox.Ok
    )


def show_documentation(self):
    """Show documentation"""
    QMessageBox.information(
        self,
        "Documentation",
        "<b>SHASTRA Proof Yard - User Guide</b><br><br>"
        "<b>Quick Start:</b><br>"
        "1. Upload Before and After firing images<br>"
        "2. Fill in the session details form<br>"
        "3. Click 'Generate Result' to analyze<br>"
        "4. Review detected shots in Preview page<br>"
        "5. Click to add/remove shots manually<br>"
        "6. Export your report as PDF or CSV<br><br>"
        "<b>Keyboard Shortcuts:</b><br>"
        "Press Ctrl+/ to view all shortcuts<br><br>"
        "<b>Tips:</b><br>"
        "• Left-click on image to add manual shot<br>"
        "• Right-click on shot to remove it<br>"
        "• Use zoom controls to inspect details"
    )


def show_change_password_dialog(self):
    """Show the change password dialog."""
    from pages.change_password_dialog import ChangePasswordDialog
    dialog = ChangePasswordDialog(self, force_change=False)
    dialog.exec_()


def show_about(self):
    """Show about dialog"""
    msg = QMessageBox(self)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("About SHASTRA")
    msg.setText("<b>SHASTRA Proof Yard System</b>")
    msg.setInformativeText(
        f"<p><b>Automated Target Detection & Analysis System</b></p>"
        f"<p>Version {APP_VERSION}</p>"
        "<p>Developed for controlled proof testing and ammunition evaluation.</p>"
        "<hr>"
        "<p><b>Features:</b></p>"
        "<ul>"
        "<li>Automatic shot detection using computer vision</li>"
        "<li>ArUco marker-based image alignment</li>"
        "<li>Statistical analysis (MPI, deviation, spread)</li>"
        "<li>PDF report generation</li>"
        "<li>CSV data export</li>"
        "</ul>"
        "<hr>"
        "<p><small>© 2025 SHASTRA Proof Yard<br>"
        "All rights reserved.</small></p>"
    )
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()


def check_for_updates_menu(self):
    """Check for updates from menu"""
    check_update_on_startup(self, silent=False, use_github=True)