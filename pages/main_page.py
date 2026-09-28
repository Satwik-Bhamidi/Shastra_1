from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QSizePolicy, QSpacerItem, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from components.upload_button import UploadButton
from utils.resource_path import resource_path
from components.form_fields import FormFields
from utils.generate_result import generate_result
from styles.theme import *

class MainPage(QWidget):
    def __init__(self, parent=None, session_manager=None):
        super().__init__(parent)
        self.session_manager = session_manager
        
        self.before_image_path = None
        self.after_image_path = None
        
        self.setup_ui()

    def setup_ui(self):
        # Main layout for the page
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"QScrollArea {{ background: {BACKGROUND}; border: none; }}")
        
        # Central content widget inside scroll area
        central = QWidget()
        central.setStyleSheet(f"background: {BACKGROUND};")
        central.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Card container
        card = QWidget()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(20)

        card.setStyleSheet(
            f"""
            QWidget#card {{
                background-color: {CARD_BG};
                border-radius: 14px;
                border: 1px solid #E0E0E0;
            }}
        """
        )

        outer_layout.addWidget(card)
        scroll_area.setWidget(central)
        main_layout.addWidget(scroll_area)

        # --- Top row with New Session and Settings buttons ---
        top_buttons_row = QHBoxLayout()
        top_buttons_row.setSpacing(10)
        
        self.new_session_btn = QPushButton("+ New Session")
        self.new_session_btn.setCursor(Qt.PointingHandCursor)
        self.new_session_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE};
            }}
        """
        )
        self.new_session_btn.clicked.connect(self.clear_session)
        
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_COLOR};
                border: 1px solid #B0BEC5;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #ECEFF1;
            }}
        """
        )
        self.settings_btn.clicked.connect(self.open_settings)
        
        top_buttons_row.addWidget(self.new_session_btn)
        top_buttons_row.addStretch()
        top_buttons_row.addWidget(self.settings_btn)
        
        card_layout.addLayout(top_buttons_row)

        # --- Title Row with Logos ---
        title_row = QHBoxLayout()
        title_row.setSpacing(15)
        
        # Left logo
        left_logo = QLabel()
        left_pixmap = QPixmap(resource_path("assets/left.png"))
        if not left_pixmap.isNull():
            left_logo.setPixmap(left_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        left_logo.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("SHASTRA PROOF YARD")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 1.5px;
                margin-left: 20px;
                margin-right: 20px;
            }}
        """
        )
        
        # Right logo
        right_logo = QLabel()
        right_pixmap = QPixmap(resource_path("assets/right.png"))
        if not right_pixmap.isNull():
            right_logo.setPixmap(right_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        right_logo.setAlignment(Qt.AlignCenter)
        
        title_row.addStretch()
        title_row.addWidget(left_logo)
        title_row.addWidget(title)
        title_row.addWidget(right_logo)
        title_row.addStretch()
        
        card_layout.addLayout(title_row)

        # --- Main upper area: uploads + form ---
        main_row = QHBoxLayout()
        main_row.setSpacing(20)
        card_layout.addLayout(main_row, 1)

        # Left: two upload boxes (Before / After)
        uploads_layout = QVBoxLayout()
        uploads_layout.setSpacing(12)

        self.before_btn = UploadButton("Upload Before\nFiring Image")
        self.after_btn = UploadButton("Upload After\nFiring Image")
        
        self.before_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.after_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        uploads_layout.addWidget(self.before_btn, 1)
        uploads_layout.addWidget(self.after_btn, 1)

        main_row.addLayout(uploads_layout, 1)

        # Right: form fields component
        self.form_fields = FormFields()
        main_row.addWidget(self.form_fields, 1)

        # Spacer
        card_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Bottom buttons ---
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(15)
        buttons_row.setAlignment(Qt.AlignCenter)

        self.generate_btn = QPushButton("Generate Result")
        # self.print_btn = QPushButton("Print Result")

        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setMinimumWidth(140)
        self.generate_btn.setMinimumHeight(38)
        self.generate_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.generate_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {PRIMARY_BLUE};
                color: white;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
        """
        )

        buttons_row.addWidget(self.generate_btn)
        # buttons_row.addWidget(self.print_btn)

        card_layout.addLayout(buttons_row)

        # Connect signals
        self.generate_btn.clicked.connect(self.on_generate_result)

    def on_generate_result(self):
        """Handle generate result button click"""
        # Logic delegate to utils function, which now has access to self.session_manager
        generate_result(self)

    def clear_session(self):
        """Clear all images and form data for a new session"""
        self.before_btn.remove_image()
        self.after_btn.remove_image()
        self.form_fields.clear_all()
        self.before_image_path = None
        self.after_image_path = None
        
        # Clear session manager data to prevent navigation to preview with stale data
        if self.session_manager:
            self.session_manager.clear_session()

    def open_settings(self):
        """Switch to settings page via MainWindow stack"""
        if self.parent():
            # parent is the StackedWidget, parent.parent is MainWindow
            main_window = self.parent().parent() 
            if hasattr(main_window, 'stack') and hasattr(main_window, 'settings_page'):
                main_window.stack.setCurrentWidget(main_window.settings_page)