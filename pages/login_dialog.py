"""
SHASTRA Login & Signup Dialog
=
Professional enterprise-style authentication dialog with two-column layout.
Supports both Sign In and Sign Up functionality.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget, QMessageBox, QSizePolicy,
    QGraphicsDropShadowEffect, QStackedWidget, QApplication,
    QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor, QIcon, QPainter, QPen, QBrush
from typing import Optional
from auth.auth_manager import get_auth_manager
from auth.passwords import validate_password_strength
from db.db_init import get_db
from utils.resource_path import resource_path
from styles.theme import (
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_RED, PRIMARY_GREEN,
    LIGHT_BLUE, CARD_BG, TEXT_COLOR
)


class LoginDialog(QDialog):
    """
    Professional login/signup dialog with branding and authentication.
    
    Signals:
        login_successful: Emitted when login succeeds
    """
    
    login_successful = pyqtSignal()
    
    def __init__(self, parent=None, show_first_run_info: bool = False):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self.show_first_run_info = show_first_run_info
        self._is_first_user = not get_db().has_users()
        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_dialog(self):
        """Configure dialog properties."""
        self.setWindowTitle("Shastra Proof Yard")
        self.setModal(True)
        self.setMinimumSize(900, 550)
        self.resize(950, 580)
        
        # Enable standard window controls
        self.setWindowFlags(
            Qt.Dialog |
            Qt.WindowTitleHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        
        # Set window icon
        try:
            icon_path = resource_path("assets/AOC_app_logo.png")
            self.setWindowIcon(QIcon(icon_path))
        except:
            pass
        
        # Dialog styling
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
        """)
    
    def _setup_ui(self):
        """Build the two-column interface."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel - Branding
        left_panel = self._create_branding_panel()
        main_layout.addWidget(left_panel, 45)
        
        # Right panel - Auth forms
        right_panel = self._create_auth_panel()
        main_layout.addWidget(right_panel, 55)
    
    def _create_branding_panel(self) -> QWidget:
        """Create the left branding panel with logo and app name."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0.5, y2:1,
                    stop:0 #1565C0,
                    stop:0.5 #0D47A1,
                    stop:1 #002171
                );
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Center the logo vertically and horizontally
        layout.addStretch(1)
        
        # Logo - just the image, larger and centered
        logo_label = QLabel()
        logo_label.setStyleSheet("QLabel { background: transparent; }")
        logo_label.setAlignment(Qt.AlignCenter)
        try:
            logo_pixmap = QPixmap(resource_path("assets/AOC_app_logo.png"))
            if not logo_pixmap.isNull():
                scaled_logo = logo_pixmap.scaled(
                    200, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                logo_label.setPixmap(scaled_logo)
        except:
            pass
        layout.addWidget(logo_label)
        
        # App name below the logo
        app_name = QLabel("SHASTRA")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 4px;
                background-color: transparent;
            }
        """)
        layout.addWidget(app_name)
        
        # Subtitle
        subtitle = QLabel("Proof Yard")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                letter-spacing: 2px;
                background: transparent;
            }
        """)
        layout.addWidget(subtitle)
        
        layout.addStretch(1)
        
        return panel
    
    def _create_auth_panel(self) -> QWidget:
        """Create the right authentication panel with login/signup forms."""
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #F5F7FA; }")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)
        
        # Stacked widget for login/signup forms
        self.auth_stack = QStackedWidget()
        
        # Create login form
        login_form = self._create_login_form()
        self.auth_stack.addWidget(login_form)
        
        # Create signup form
        signup_form = self._create_signup_form()
        self.auth_stack.addWidget(signup_form)
        
        layout.addWidget(self.auth_stack)
        
        return panel
    
    def _add_password_toggle(self, line_edit: QLineEdit):
        """Add a clickable action to toggle password visibility."""
        
        def create_eye_icon(off=False):
            """Generate a simple eye icon programmatically."""
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            color = QColor(TEXT_COLOR)
            color.setAlpha(150) # Semi-transparent
            painter.setPen(QPen(color, 1.5))
            
            # Draw eye outline (almond shape approximation)
            if off:
                # Eye with slash
                painter.drawEllipse(2, 5, 16, 10)
                painter.drawLine(4, 4, 16, 16)
            else:
                # Open eye with pupil
                painter.drawEllipse(2, 5, 16, 10)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(8, 8, 4, 4)
            
            painter.end()
            return QIcon(pixmap)

        # Create the action
        action = line_edit.addAction(create_eye_icon(off=False), QLineEdit.TrailingPosition)
        action.setCheckable(True)
        
        def on_toggle(checked):
            if checked:
                line_edit.setEchoMode(QLineEdit.Normal)
                action.setIcon(create_eye_icon(off=True))
            else:
                line_edit.setEchoMode(QLineEdit.Password)
                action.setIcon(create_eye_icon(off=False))
        
        action.toggled.connect(on_toggle)
    
    def _create_login_form(self) -> QWidget:
        """Create the login form widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top spacer
        layout.addStretch(1)
        
        # Login card
        card = self._create_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(45, 40, 45, 40)
        card_layout.setSpacing(18)
        
        # Header
        header_label = QLabel("Welcome Back")
        header_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 26px;
                font-weight: bold;
                background-color: transparent;
            }}
        """)
        card_layout.addWidget(header_label)
        
        subtitle = QLabel("Sign in to access your account")
        subtitle.setStyleSheet("QLabel { color: #78909C; font-size: 13px; background: transparent; }")
        card_layout.addWidget(subtitle)
        
        card_layout.addSpacing(15)
        
        # Username field
        card_layout.addWidget(self._create_field_label("Username"))
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.login_username.setStyleSheet(self._get_input_style())
        self.login_username.setMinimumHeight(44)
        card_layout.addWidget(self.login_username)
        
        # Password field
        card_layout.addWidget(self._create_field_label("Password"))
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setStyleSheet(self._get_input_style())
        self.login_password.setMinimumHeight(44)

        self._add_password_toggle(self.login_password)
        card_layout.addWidget(self.login_password)
        
        # Error label
        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"QLabel {{ color: {PRIMARY_RED}; font-size: 12px; background: transparent; }}")
        self.login_error.setWordWrap(True)
        self.login_error.hide()
        card_layout.addWidget(self.login_error)
        
        card_layout.addSpacing(10)
        
        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setStyleSheet(self._get_primary_button_style())
        card_layout.addWidget(self.login_btn)
        
        # Signup link
        card_layout.addSpacing(15)
        
        signup_container = QHBoxLayout()
        signup_container.setAlignment(Qt.AlignCenter)
        
        signup_text = QLabel("Don't have an account?")
        signup_text.setStyleSheet("QLabel { color: #78909C; font-size: 13px; background: transparent; }")
        signup_container.addWidget(signup_text)
        
        self.goto_signup_btn = QPushButton("Sign Up")
        self.goto_signup_btn.setCursor(Qt.PointingHandCursor)
        self.goto_signup_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARY_BLUE};
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0 5px;
            }}
            QPushButton:hover {{
                color: {PRIMARY_BLUE_DARK};
                text-decoration: underline;
            }}
        """)
        signup_container.addWidget(self.goto_signup_btn)
        
        card_layout.addLayout(signup_container)
        
        layout.addWidget(card)
        
        # Bottom spacer
        layout.addStretch(1)
        
        return container
    
    def _create_signup_form(self) -> QWidget:
        """Create the signup form widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top spacer
        layout.addStretch(1)
        
        # Signup card
        card = self._create_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(45, 35, 45, 35)
        card_layout.setSpacing(14)
        
        # Header
        header_label = QLabel("Create Account")
        header_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 26px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        card_layout.addWidget(header_label)
        
        # Role indicator
        if self._is_first_user:
            role_text = "You will be registered as Administrator"
            role_color = PRIMARY_BLUE
        else:
            role_text = "You will be registered as Operator"
            role_color = "#78909C"
        
        self.role_indicator = QLabel(role_text)
        self.role_indicator.setStyleSheet(f"""
            QLabel {{
                color: {role_color};
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }}
        """)
        card_layout.addWidget(self.role_indicator)
        
        card_layout.addSpacing(10)
        
        # Username field
        card_layout.addWidget(self._create_field_label("Username"))
        self.signup_username = QLineEdit()
        self.signup_username.setPlaceholderText("Choose a username (min 3 characters)")
        self.signup_username.setStyleSheet(self._get_input_style())
        self.signup_username.setMinimumHeight(42)
        card_layout.addWidget(self.signup_username)
        
        # Password field
        card_layout.addWidget(self._create_field_label("Password"))
        self.signup_password = QLineEdit()
        self.signup_password.setPlaceholderText("Create a strong password")
        self.signup_password.setEchoMode(QLineEdit.Password)
        self.signup_password.setStyleSheet(self._get_input_style())
        self.signup_password.setMinimumHeight(42)
        card_layout.addWidget(self.signup_password)
        
        # Confirm Password field
        card_layout.addWidget(self._create_field_label("Confirm Password"))
        self.signup_confirm = QLineEdit()
        self.signup_confirm.setPlaceholderText("Confirm your password")
        self.signup_confirm.setEchoMode(QLineEdit.Password)
        self.signup_confirm.setStyleSheet(self._get_input_style())
        self.signup_confirm.setMinimumHeight(42)

        self._add_password_toggle(self.signup_confirm)
        card_layout.addWidget(self.signup_confirm)
        
        # Password requirements hint
        hint = QLabel("Password: 8+ chars, uppercase, lowercase, number")
        hint.setStyleSheet("QLabel { color: #90A4AE; font-size: 11px; background: transparent; }")
        card_layout.addWidget(hint)
        
        # Error label
        self.signup_error = QLabel("")
        self.signup_error.setStyleSheet(f"QLabel {{ color: {PRIMARY_RED}; font-size: 12px; background: transparent; }}")
        self.signup_error.setWordWrap(True)
        self.signup_error.hide()
        card_layout.addWidget(self.signup_error)
        
        card_layout.addSpacing(5)
        
        # Signup button
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setCursor(Qt.PointingHandCursor)
        self.signup_btn.setMinimumHeight(48)
        self.signup_btn.setStyleSheet(self._get_success_button_style())
        card_layout.addWidget(self.signup_btn)
        
        # Login link
        card_layout.addSpacing(12)
        
        login_container = QHBoxLayout()
        login_container.setAlignment(Qt.AlignCenter)
        
        login_text = QLabel("Already have an account?")
        login_text.setStyleSheet("QLabel { color: #78909C; font-size: 13px; background: transparent; }")
        login_container.addWidget(login_text)
        
        self.goto_login_btn = QPushButton("Sign In")
        self.goto_login_btn.setCursor(Qt.PointingHandCursor)
        self.goto_login_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {PRIMARY_BLUE};
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0 5px;
            }}
            QPushButton:hover {{
                color: {PRIMARY_BLUE_DARK};
                text-decoration: underline;
            }}
        """)
        login_container.addWidget(self.goto_login_btn)
        
        card_layout.addLayout(login_container)
        
        layout.addWidget(card)
        
        # Bottom spacer
        layout.addStretch(1)
        
        return container
    
    def _create_card(self) -> QFrame:
        """Create a styled card container."""
        card = QFrame()
        card.setObjectName("authCard")
        card.setStyleSheet(f"""
            QFrame#authCard {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)
        
        return card
    
    def _create_field_label(self, text: str) -> QLabel:
        """Create a styled field label."""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        return label
    
    def _get_input_style(self) -> str:
        """Get stylesheet for input fields."""
        return f"""
            QLineEdit {{
                background-color: #F8F9FA;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY_BLUE};
                background-color: white;
            }}
            QLineEdit::placeholder {{
                color: #B0BEC5;
            }}
        """
    
    def _get_primary_button_style(self) -> str:
        """Get stylesheet for primary button."""
        return f"""
            QPushButton {{
                background-color: {PRIMARY_BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
            QPushButton:pressed {{
                background-color: #0D47A1;
            }}
            QPushButton:disabled {{
                background-color: #B0BEC5;
            }}
        """
    
    def _get_success_button_style(self) -> str:
        """Get stylesheet for success/signup button."""
        return f"""
            QPushButton {{
                background-color: {PRIMARY_GREEN};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2E7D32;
            }}
            QPushButton:pressed {{
                background-color: #1B5E20;
            }}
            QPushButton:disabled {{
                background-color: #B0BEC5;
            }}
        """
    
    def _connect_signals(self):
        """Connect UI signals to handlers."""
        # Login form
        self.login_btn.clicked.connect(self._handle_login)
        self.login_password.returnPressed.connect(self._handle_login)
        self.login_username.returnPressed.connect(lambda: self.login_password.setFocus())
        
        # Signup form
        self.signup_btn.clicked.connect(self._handle_signup)
        self.signup_confirm.returnPressed.connect(self._handle_signup)
        
        # Navigation
        self.goto_signup_btn.clicked.connect(self._show_signup)
        self.goto_login_btn.clicked.connect(self._show_login)
    
    def _show_signup(self):
        """Switch to signup form."""
        self._clear_forms()
        self._update_role_indicator()
        self.auth_stack.setCurrentIndex(1)
    
    def _show_login(self):
        """Switch to login form."""
        self._clear_forms()
        self.auth_stack.setCurrentIndex(0)
    
    def _update_role_indicator(self):
        """Update the role indicator based on current user count."""
        db = get_db()
        self._is_first_user = not db.has_users()
        
        if self._is_first_user:
            self.role_indicator.setText("You will be registered as Administrator")
            self.role_indicator.setStyleSheet(f"""
                QLabel {{
                    color: {PRIMARY_BLUE};
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                }}
            """)
        else:
            self.role_indicator.setText("You will be registered as Operator")
            self.role_indicator.setStyleSheet("""
                QLabel {
                    color: #78909C;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                }
            """)
    
    def _clear_forms(self):
        """Clear all form fields and errors."""
        self.login_username.clear()
        self.login_password.clear()
        self.login_error.hide()
        
        self.signup_username.clear()
        self.signup_password.clear()
        self.signup_confirm.clear()
        self.signup_error.hide()
    
    def _handle_login(self):
        """Process login attempt."""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            self._show_login_error("Please enter both username and password")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        
        try:
            success, message, session = self.auth_manager.login(username, password)
            
            if success:
                self.login_error.hide()
                
                if session and session.must_change_password:
                    self._prompt_password_change()
                else:
                    self.login_successful.emit()
                    self.accept()
            else:
                self._show_login_error(message)
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Sign In")
    
    def _handle_signup(self):
        """Process signup attempt."""
        username = self.signup_username.text().strip()
        password = self.signup_password.text()
        confirm = self.signup_confirm.text()
        
        # Validation
        if not username or len(username) < 3:
            self._show_signup_error("Username must be at least 3 characters")
            return
        
        if not password:
            self._show_signup_error("Please enter a password")
            return
        
        if password != confirm:
            self._show_signup_error("Passwords do not match")
            return
        
        # Validate password strength
        is_valid, error = validate_password_strength(password)
        if not is_valid:
            self._show_signup_error(error)
            return
        
        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Creating account...")
        
        try:
            # Determine role: first user is Admin, others are Operator
            db = get_db()
            role = "Admin" if not db.has_users() else "Operator"
            
            # Create user directly via database (signup doesn't require auth)
            from auth.passwords import hash_password
            password_hash = hash_password(password)
            
            user_id = db.create_user(
                username=username,
                password_hash=password_hash,
                role=role,
                must_change_password=False
            )
            
            if user_id:
                # Log the signup
                db.log_audit(
                    action="USER_SIGNUP",
                    user_id=user_id,
                    username=username,
                    details=f"New user registered with role: {role}"
                )
                
                QMessageBox.information(
                    self,
                    "Account Created",
                    f"Your account has been created successfully.\n\n"
                    f"Username: {username}\n"
                    f"Role: {role}\n\n"
                    f"You can now sign in with your credentials."
                )
                
                # Switch to login form with username pre-filled
                self._show_login()
                self.login_username.setText(username)
                self.login_password.setFocus()
                
                # Update first user flag
                self._is_first_user = False
            else:
                self._show_signup_error("Username already exists")
        except Exception as e:
            self._show_signup_error(f"Error creating account: {str(e)}")
        finally:
            self.signup_btn.setEnabled(True)
            self.signup_btn.setText("Create Account")
    
    def _show_login_error(self, message: str):
        """Display login error message."""
        self.login_error.setText(message)
        self.login_error.show()
    
    def _show_signup_error(self, message: str):
        """Display signup error message."""
        self.signup_error.setText(message)
        self.signup_error.show()
    
    def _prompt_password_change(self):
        """Prompt user to change their password."""
        from pages.change_password_dialog import ChangePasswordDialog
        
        dialog = ChangePasswordDialog(self, force_change=True)
        if dialog.exec_() == QDialog.Accepted:
            self.login_successful.emit()
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Password Change Required",
                "You must change your password before continuing."
            )
    
    def closeEvent(self, event):
        """Handle close event - confirm exit if not authenticated."""
        if not self.auth_manager.is_authenticated:
            reply = QMessageBox.question(
                self,
                "Exit Application",
                "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                QApplication.quit()
            else:
                event.ignore()
        else:
            event.accept()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
