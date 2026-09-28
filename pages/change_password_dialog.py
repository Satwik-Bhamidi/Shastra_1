"""
SHASTRA Change Password Dialog
==
Dialog for users to change their own password.
Used for first-login mandatory password change and voluntary changes.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QGraphicsDropShadowEffect,
    QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QPen, QBrush
from auth.auth_manager import get_auth_manager
from auth.passwords import validate_password_strength
from styles.theme import (
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_RED, PRIMARY_GREEN,
    CARD_BG, TEXT_COLOR
)


class ChangePasswordDialog(QDialog):
    """
    Dialog for changing user's own password.
    
    Args:
        parent: Parent widget
        force_change: If True, dialog cannot be cancelled
    """
    
    def __init__(self, parent=None, force_change: bool = False):
        super().__init__(parent)
        self.auth_manager = get_auth_manager()
        self.force_change = force_change
        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()
    
    def _setup_dialog(self):
        """Configure dialog properties."""
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.setMinimumSize(400, 450)
        self.setMaximumSize(500, 550)
        self.resize(450, 480)
        
        if self.force_change:
            # Cannot close without changing password
            self.setWindowFlags(
                Qt.Dialog |
                Qt.WindowTitleHint |
                Qt.CustomizeWindowHint
            )
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #F5F7FA;
            }}
        """)
    
    def _add_password_toggle(self, line_edit: QLineEdit):
        """Add a clickable action to toggle password visibility."""
        
        def create_eye_icon(off=False):
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            color = QColor(TEXT_COLOR)
            color.setAlpha(150)
            painter.setPen(QPen(color, 1.5))
            
            if off:
                painter.drawEllipse(2, 5, 16, 10)
                painter.drawLine(4, 4, 16, 16)
            else:
                painter.drawEllipse(2, 5, 16, 10)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(8, 8, 4, 4)
            
            painter.end()
            return QIcon(pixmap)

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

    def _setup_ui(self):
        """Build the change password interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Card container
        card = QFrame()
        card.setObjectName("passwordCard")
        card.setStyleSheet(f"""
            QFrame#passwordCard {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }}
        """)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Change Password")
        header_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 22px;
                font-weight: bold;
            }}
        """)
        card_layout.addWidget(header_label)
        
        if self.force_change:
            notice = QLabel("You must change your password to continue")
            notice.setStyleSheet(f"""
                QLabel {{
                    color: #F57C00;
                    font-size: 12px;
                    padding: 8px;
                    background-color: #FFF3E0;
                    border-radius: 4px;
                }}
            """)
            notice.setWordWrap(True)
            card_layout.addWidget(notice)
        
        card_layout.addSpacing(10)
        
        # Current password
        current_label = QLabel("Current Password")
        current_label.setStyleSheet(self._label_style())
        card_layout.addWidget(current_label)
        
        self.current_password = QLineEdit()
        self.current_password.setPlaceholderText("Enter current password")
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setStyleSheet(self._input_style())
        self.current_password.setMinimumHeight(42)

        self._add_password_toggle(self.current_password)
        card_layout.addWidget(self.current_password)
        
        # New password
        new_label = QLabel("New Password")
        new_label.setStyleSheet(self._label_style())
        card_layout.addWidget(new_label)
        
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Enter new password")
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setStyleSheet(self._input_style())
        self.new_password.setMinimumHeight(42)

        self._add_password_toggle(self.new_password)
        card_layout.addWidget(self.new_password)
        
        # Confirm password
        confirm_label = QLabel("Confirm New Password")
        confirm_label.setStyleSheet(self._label_style())
        card_layout.addWidget(confirm_label)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm new password")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setStyleSheet(self._input_style())
        self.confirm_password.setMinimumHeight(42)

        self._add_password_toggle(self.confirm_password)
        card_layout.addWidget(self.confirm_password)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARY_RED};
                font-size: 12px;
            }}
        """)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        card_layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        if not self.force_change:
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.setCursor(Qt.PointingHandCursor)
            self.cancel_btn.setMinimumHeight(42)
            self.cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_COLOR};
                    border: 2px solid #E0E0E0;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 600;
                    padding: 0 20px;
                }}
                QPushButton:hover {{
                    background-color: #ECEFF1;
                }}
            """)
            btn_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Change Password")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setMinimumHeight(42)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_BLUE};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
            QPushButton:disabled {{
                background-color: #B0BEC5;
            }}
        """)
        btn_layout.addWidget(self.save_btn)
        
        card_layout.addLayout(btn_layout)
        
        layout.addWidget(card)
    
    def _label_style(self) -> str:
        """Get label stylesheet."""
        return f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 13px;
                font-weight: 600;
            }}
        """
    
    def _input_style(self) -> str:
        """Get input field stylesheet."""
        return f"""
            QLineEdit {{
                background-color: #F5F7FA;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{
                border-color: {PRIMARY_BLUE};
                background-color: white;
            }}
        """
    
    def _connect_signals(self):
        """Connect signals to handlers."""
        self.save_btn.clicked.connect(self._handle_change_password)
        self.confirm_password.returnPressed.connect(self._handle_change_password)
        
        if not self.force_change:
            self.cancel_btn.clicked.connect(self.reject)
    
    def _handle_change_password(self):
        """Process password change request."""
        current = self.current_password.text()
        new_pass = self.new_password.text()
        confirm = self.confirm_password.text()
        
        # Validation
        if not current:
            self._show_error("Please enter your current password")
            return
        
        if not new_pass:
            self._show_error("Please enter a new password")
            return
        
        if new_pass != confirm:
            self._show_error("New passwords do not match")
            return
        
        # Validate password strength
        is_valid, error = validate_password_strength(new_pass)
        if not is_valid:
            self._show_error(error)
            return
        
        # Attempt password change
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Changing...")
        
        try:
            success, message = self.auth_manager.change_own_password(current, new_pass)
            
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    "Your password has been changed successfully."
                )
                self.accept()
            else:
                self._show_error(message)
        finally:
            self.save_btn.setEnabled(True)
            self.save_btn.setText("Change Password")
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.show()
    
    def keyPressEvent(self, event):
        """Handle key events."""
        if event.key() == Qt.Key_Escape and self.force_change:
            event.ignore()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event."""
        if self.force_change:
            event.ignore()
        else:
            event.accept()
