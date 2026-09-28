"""
SHASTRA User Management Page

Admin-only user management interface.
Provides user CRUD operations with proper authorization.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDialog, QLineEdit, QComboBox, QMessageBox, QScrollArea,
    QSizePolicy, QAbstractItemView, QGraphicsDropShadowEffect,
    QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QIcon, QCursor
from typing import Optional, List, Dict, Any
from auth.auth_manager import get_auth_manager
from auth.permissions import (
    Permission, Roles, has_permission, can_manage_users,
    is_admin
)
from auth.session import get_current_session
from auth.passwords import validate_password_strength
from styles.theme import (
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_RED, PRIMARY_GREEN,
    LIGHT_BLUE, CARD_BG, TEXT_COLOR, BACKGROUND
)


class UserManagementPage(QWidget):
    """
    User management interface for administrators.
    
    Signals:
        back_requested: Emitted when user wants to go back
    """
    
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self._setup_ui()
        self._load_users()
    
    def _setup_ui(self):
        """Build the user management interface."""
        # Main scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: {BACKGROUND};
                border: none;
            }}
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {BACKGROUND};")
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Card container
        card = QFrame()
        card.setObjectName("userMgmtCard")
        card.setStyleSheet(f"""
            QFrame#userMgmtCard {{
                background-color: {CARD_BG};
                border-radius: 14px;
                border: 1px solid #E0E0E0;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE};
            }}
        """)
        self.back_btn.clicked.connect(self._go_back)
        header_layout.addWidget(self.back_btn)
        
        header_layout.addStretch()
        
        title = QLabel("User Management")
        title.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARY_BLUE};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add user button (Admin only)
        if has_permission(Permission.CREATE_USER):
            self.add_user_btn = QPushButton("+ Add User")
            self.add_user_btn.setCursor(Qt.PointingHandCursor)
            self.add_user_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PRIMARY_GREEN};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #2E7D32;
                }}
            """)
            self.add_user_btn.clicked.connect(self._show_add_user_dialog)
            header_layout.addWidget(self.add_user_btn)
        
        card_layout.addLayout(header_layout)
        
        # Info banner for operators
        if not is_admin():
            info_banner = QLabel("You have read-only access to this section")
            info_banner.setStyleSheet("""
                QLabel {
                    background-color: #E3F2FD;
                    color: #1565C0;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 13px;
                }
            """)
            card_layout.addWidget(info_banner)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(6)
        self.users_table.setHorizontalHeaderLabels([
            "Username", "Role", "Status", "Created", "Last Login", "Actions"
        ])
        
        # Table styling
        self.users_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                gridline-color: #F0F0F0;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QTableWidget::item:selected {{
                background-color: {LIGHT_BLUE};
                color: {TEXT_COLOR};
            }}
            QHeaderView::section {{
                background-color: #F5F7FA;
                color: {TEXT_COLOR};
                font-weight: bold;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #E0E0E0;
            }}
        """)
        
        # Table configuration
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setShowGrid(False)
        
        # Column sizing
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.users_table.setColumnWidth(5, 80)
        
        # Set row height for better button visibility
        self.users_table.verticalHeader().setDefaultSectionSize(45)
        
        self.users_table.setMinimumHeight(300)
        card_layout.addWidget(self.users_table)
        
        # Stats footer
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #78909C;
                font-size: 12px;
            }
        """)
        card_layout.addWidget(self.stats_label)
        
        layout.addWidget(card)
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def _load_users(self):
        """Load and display users from database."""
        users = self.auth_manager.get_all_users()
        self.users_table.setRowCount(len(users))
        
        current_session = get_current_session()
        current_user_id = current_session.user_id if current_session else None
        
        admin_count = 0
        active_count = 0
        
        for row, user in enumerate(users):
            # Username
            username_item = QTableWidgetItem(user['username'])
            username_item.setData(Qt.UserRole, user['id'])
            if user['id'] == current_user_id:
                username_item.setText(f"{user['username']} (You)")
            self.users_table.setItem(row, 0, username_item)
            
            # Role with badge
            role_item = QTableWidgetItem(user['role'])
            if user['role'] == 'Admin':
                role_item.setForeground(QColor(PRIMARY_BLUE))
                admin_count += 1
            else:
                role_item.setForeground(QColor("#78909C"))
            self.users_table.setItem(row, 1, role_item)
            
            # Status
            is_active = bool(user.get('is_active', False))
            status_text = "Active" if is_active else "Disabled"
            status_item = QTableWidgetItem(status_text)
            if is_active:
                status_item.setForeground(QColor(PRIMARY_GREEN))
                active_count += 1
            else:
                status_item.setForeground(QColor(PRIMARY_RED))
            self.users_table.setItem(row, 2, status_item)
            
            # Created date
            created = user.get('created_at', '')[:10] if user.get('created_at') else 'N/A'
            self.users_table.setItem(row, 3, QTableWidgetItem(created))
            
            # Last login
            last_login = user.get('last_login', '')[:10] if user.get('last_login') else 'Never'
            self.users_table.setItem(row, 4, QTableWidgetItem(last_login))
            
            # Actions button
            if can_manage_users():
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 5, 0, 5)
                actions_layout.setSpacing(0)
                actions_layout.setAlignment(Qt.AlignCenter)
                
                actions_btn = QPushButton("...")
                actions_btn.setCursor(Qt.PointingHandCursor)
                actions_btn.setFixedSize(36, 28)
                actions_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {LIGHT_BLUE};
                        border: 1px solid {PRIMARY_BLUE};
                        border-radius: 4px;
                        font-size: 14px;
                        font-weight: bold;
                        color: {PRIMARY_BLUE};
                        margin-bottom: 10px;
                        
                    }}
                    QPushButton:hover {{
                        background-color: {PRIMARY_BLUE};
                        color: white;
                    }}
                """)
                actions_btn.clicked.connect(
                    lambda checked, uid=user['id'], uname=user['username'], urole=user['role'], uactive=is_active:
                    self._show_actions_menu(uid, uname, urole, uactive)
                )
                actions_layout.addWidget(actions_btn)
                
                self.users_table.setCellWidget(row, 5, actions_widget)
            else:
                self.users_table.setItem(row, 5, QTableWidgetItem("-"))
        
        # Update stats
        self.stats_label.setText(
            f"Total: {len(users)} users • {admin_count} admins • {active_count} active"
        )
    
    def _show_actions_menu(self, user_id: int, username: str, role: str, is_active: bool):
        """Show context menu with user actions."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {LIGHT_BLUE};
            }}
        """)
        
        current_session = get_current_session()
        is_self = current_session and current_session.user_id == user_id
        
        # Edit role action
        if has_permission(Permission.MODIFY_USER) and not is_self:
            edit_role_action = QAction("Change Role", self)
            edit_role_action.triggered.connect(lambda: self._show_edit_role_dialog(user_id, username, role))
            menu.addAction(edit_role_action)
        
        # Reset password action
        if has_permission(Permission.RESET_PASSWORD):
            reset_pwd_action = QAction("Reset Password", self)
            reset_pwd_action.triggered.connect(lambda: self._show_reset_password_dialog(user_id, username))
            menu.addAction(reset_pwd_action)
        
        # Toggle status action
        if has_permission(Permission.MODIFY_USER) and not is_self:
            status_action = QAction("Disable User" if is_active else "Enable User", self)
            status_action.triggered.connect(lambda: self._toggle_user_status(user_id, username, is_active))
            menu.addAction(status_action)
        
        menu.addSeparator()
        
        # Delete action
        if has_permission(Permission.DELETE_USER) and not is_self:
            delete_action = QAction("Delete User", self)
            delete_action.triggered.connect(lambda: self._delete_user(user_id, username))
            menu.addAction(delete_action)
        
        menu.exec_(QCursor.pos())
    
    def _show_add_user_dialog(self):
        """Show dialog to add new user."""
        dialog = AddUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_users()
    
    def _show_edit_role_dialog(self, user_id: int, username: str, current_role: str):
        """Show dialog to edit user role."""
        dialog = EditRoleDialog(self, user_id, username, current_role)
        if dialog.exec_() == QDialog.Accepted:
            self._load_users()
    
    def _show_reset_password_dialog(self, user_id: int, username: str):
        """Show dialog to reset user password."""
        dialog = ResetPasswordDialog(self, user_id, username)
        if dialog.exec_() == QDialog.Accepted:
            self._load_users()
    
    def _toggle_user_status(self, user_id: int, username: str, is_active: bool):
        """Toggle user active status."""
        action = "disable" if is_active else "enable"
        
        reply = QMessageBox.question(
            self,
            f"Confirm {action.title()}",
            f"Are you sure you want to {action} user '{username}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.auth_manager.update_user_status(user_id, not is_active)
            if success:
                QMessageBox.information(self, "Success", message)
                self._load_users()
            else:
                QMessageBox.warning(self, "Error", message)
    
    def _delete_user(self, user_id: int, username: str):
        """Delete a user."""
        reply = QMessageBox.warning(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.auth_manager.delete_user(user_id)
            if success:
                QMessageBox.information(self, "Success", message)
                self._load_users()
            else:
                QMessageBox.warning(self, "Error", message)
    
    def _go_back(self):
        """Navigate back to previous page."""
        self.back_requested.emit()
    
    def refresh(self):
        """Refresh the user list."""
        self._load_users()


class AddUserDialog(QDialog):
    """Dialog for adding a new user."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the add user interface."""
        self.setWindowTitle("Add New User")
        self.setModal(True)
        self.setMinimumSize(400, 380)
        self.setMaximumSize(450, 420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Create New User")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 20px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title)
        
        # Username
        layout.addWidget(self._create_label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username (min 3 characters)")
        self.username_input.setStyleSheet(self._input_style())
        self.username_input.setMinimumHeight(40)
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(self._create_label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(self._input_style())
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)
        
        # Role
        layout.addWidget(self._create_label("Role"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(Roles.ALL_ROLES)
        self.role_combo.setCurrentText(Roles.OPERATOR)
        self.role_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #F5F7FA;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: {TEXT_COLOR};
            }}
            QComboBox:focus {{
                border-color: {PRIMARY_BLUE};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {TEXT_COLOR};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                color: {TEXT_COLOR};
                selection-background-color: {LIGHT_BLUE};
                selection-color: {TEXT_COLOR};
                border: 1px solid #E0E0E0;
                padding: 5px;
            }}
        """)
        self.role_combo.setMinimumHeight(40)
        layout.addWidget(self.role_combo)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {PRIMARY_RED}; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #ECEFF1;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create User")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setMinimumHeight(40)
        self.create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_GREEN};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: #2E7D32;
            }}
        """)
        self.create_btn.clicked.connect(self._create_user)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_label(self, text: str) -> QLabel:
        """Create a styled label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        return label
    
    def _input_style(self) -> str:
        """Get input field stylesheet."""
        return f"""
            QLineEdit {{
                background-color: #F5F7FA;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY_BLUE};
                background-color: white;
            }}
        """
    
    def _create_user(self):
        """Handle user creation."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()
        
        print(f"DEBUG: Creating user - username='{username}', role='{role}', password_len={len(password)}")
        
        success, message = self.auth_manager.create_user(username, password, role)
        
        print(f"DEBUG: Result - success={success}, message='{message}'")
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            self.error_label.setText(message)
            self.error_label.show()


class EditRoleDialog(QDialog):
    """Dialog for editing user role."""
    
    def __init__(self, parent, user_id: int, username: str, current_role: str):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self.user_id = user_id
        self.username = username
        self.current_role = current_role
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the edit role interface."""
        self.setWindowTitle("Change User Role")
        self.setModal(True)
        self.setFixedSize(350, 220)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Change Role for '{self.username}'")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title)
        
        # Role selector
        layout.addWidget(QLabel("Select new role:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(Roles.ALL_ROLES)
        self.role_combo.setCurrentText(self.current_role)
        self.role_combo.setMinimumHeight(40)
        self.role_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #F5F7FA;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(self.role_combo)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(38)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_BLUE};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
        """)
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._save_role)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save_role(self):
        """Save the new role."""
        new_role = self.role_combo.currentText()
        
        if new_role == self.current_role:
            self.reject()
            return
        
        success, message = self.auth_manager.update_user_role(self.user_id, new_role)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", message)


class ResetPasswordDialog(QDialog):
    """Dialog for resetting user password."""
    
    def __init__(self, parent, user_id: int, username: str):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self.user_id = user_id
        self.username = username
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the reset password interface."""
        self.setWindowTitle("Reset Password")
        self.setModal(True)
        self.setFixedSize(400, 280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"Reset Password for '{self.username}'")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(title)
        
        # New password
        layout.addWidget(QLabel("New Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter new password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #F5F7FA;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY_BLUE};
            }}
        """)
        layout.addWidget(self.password_input)
        
        # Confirm password
        layout.addWidget(QLabel("Confirm Password:"))
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm new password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(40)
        self.confirm_input.setStyleSheet(self.password_input.styleSheet())
        layout.addWidget(self.confirm_input)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {PRIMARY_RED}; font-size: 12px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumHeight(38)
        btn_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("Reset Password")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_BLUE};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
        """)
        reset_btn.setMinimumHeight(38)
        reset_btn.clicked.connect(self._reset_password)
        btn_layout.addWidget(reset_btn)
        
        layout.addLayout(btn_layout)
    
    def _reset_password(self):
        """Reset the password."""
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if password != confirm:
            self.error_label.setText("Passwords do not match")
            self.error_label.show()
            return
        
        # Validate password strength
        is_valid, error = validate_password_strength(password)
        if not is_valid:
            self.error_label.setText(error)
            self.error_label.show()
            return
        
        success, message = self.auth_manager.reset_user_password(self.user_id, password)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            self.error_label.setText(message)
            self.error_label.show()
