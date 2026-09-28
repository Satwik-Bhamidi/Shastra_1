from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QMessageBox, QFileDialog, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QResizeEvent
from backend.config import SystemConfig
from styles.theme import *
from components.system_configs import create_system_config_settings
from components.advanced_settings import create_advanced_settings
from utils.aruco_markers import generate_aruco_markers
from auth.permissions import can_modify_settings, can_manage_users, is_admin
from auth.session import get_current_session

# Breakpoints for responsive design
BREAKPOINT_SMALL = 600   # Below this: single column, stacked buttons
BREAKPOINT_MEDIUM = 900  # Below this: single column, inline buttons
# Above MEDIUM: two columns


class ResponsiveSettingsContainer(QWidget):
    """Container that switches between 1-col and 2-col grid based on width."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.system_config_card = None
        self.advanced_settings_card = None
        self.current_layout = None
        self.columns = 2  # Track current column count
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def set_widgets(self, system_config, advanced_settings):
        self.system_config_card = system_config
        self.advanced_settings_card = advanced_settings
        # Set size policies for cards
        for card in [system_config, advanced_settings]:
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            card.setMinimumWidth(280)
        self.update_layout()
        
    def resizeEvent(self, event: QResizeEvent):
        new_width = event.size().width()
        new_columns = 2 if new_width >= BREAKPOINT_MEDIUM else 1
        if new_columns != self.columns:
            self.columns = new_columns
            self.update_layout()
        super().resizeEvent(event)
    
    def update_layout(self):
        # Remove old layout safely
        if self.current_layout:
            # Remove widgets from layout first
            while self.current_layout.count():
                item = self.current_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            QWidget().setLayout(self.current_layout)
        
        # Create grid layout
        self.current_layout = QGridLayout(self)
        self.current_layout.setSpacing(20)
        self.current_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.columns == 2:
            # Two column layout: side by side
            self.current_layout.addWidget(self.system_config_card, 0, 0)
            self.current_layout.addWidget(self.advanced_settings_card, 0, 1)
            self.current_layout.setColumnStretch(0, 1)
            self.current_layout.setColumnStretch(1, 1)
        else:
            # Single column layout: stacked vertically
            self.current_layout.addWidget(self.system_config_card, 0, 0)
            self.current_layout.addWidget(self.advanced_settings_card, 1, 0)
            self.current_layout.setColumnStretch(0, 1)
        
        # Re-parent widgets
        self.system_config_card.setParent(self)
        self.advanced_settings_card.setParent(self)
        self.system_config_card.show()
        self.advanced_settings_card.show()

class ResponsiveHeaderWidget(QWidget):
    """Responsive header that adapts button layout based on width."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_stacked = False
        self.back_btn = None
        self.title = None
        self.generate_markers_btn = None
        self.restore_default_btn = None
        self.user_mgmt_btn = None
        self.current_layout = None
        self.buttons_container = None
        
    def setup(self, back_btn, title, gen_btn, restore_btn, user_mgmt_btn=None):
        self.back_btn = back_btn
        self.title = title
        self.generate_markers_btn = gen_btn
        self.restore_default_btn = restore_btn
        self.user_mgmt_btn = user_mgmt_btn
        # Defer layout update until widget is properly sized
        QTimer.singleShot(0, self._deferred_setup)
    
    def _deferred_setup(self):
        """Called after widget is properly sized to set up the correct layout."""
        # If width is 0 or very small, assume large screen (app starts maximized)
        # Only use stacked layout if we have a real small width
        current_width = self.width()
        if current_width < 100:  # Widget not yet sized properly, assume large screen
            self.is_stacked = False
        else:
            self.is_stacked = current_width < BREAKPOINT_SMALL
        self.update_header_layout()
        
    def resizeEvent(self, event: QResizeEvent):
        new_width = event.size().width()
        should_stack = new_width < BREAKPOINT_SMALL
        if should_stack != self.is_stacked:
            self.is_stacked = should_stack
            self.update_header_layout()
        super().resizeEvent(event)
    
    def update_header_layout(self):
        # Remove old layout
        if self.current_layout:
            while self.current_layout.count():
                item = self.current_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    self._clear_layout(item.layout())
            QWidget().setLayout(self.current_layout)
        
        self.current_layout = QVBoxLayout(self)
        self.current_layout.setContentsMargins(0, 0, 0, 0)
        self.current_layout.setSpacing(10)
        
        if self.is_stacked:
            # Stacked layout for small screens
            # Row 1: Back button and title
            top_row = QHBoxLayout()
            top_row.addWidget(self.back_btn)
            top_row.addStretch()
            top_row.addWidget(self.title)
            top_row.addStretch()
            self.current_layout.addLayout(top_row)
            
            # Row 2: Action buttons centered
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            btn_row.addWidget(self.generate_markers_btn)
            btn_row.addWidget(self.restore_default_btn)
            if self.user_mgmt_btn and self.user_mgmt_btn.isVisible():
                btn_row.addWidget(self.user_mgmt_btn)
            btn_row.addStretch()
            self.current_layout.addLayout(btn_row)
        else:
            # Single row for larger screens
            header_row = QHBoxLayout()
            header_row.addWidget(self.back_btn)
            header_row.addStretch()
            header_row.addWidget(self.title)
            header_row.addStretch()
            header_row.addWidget(self.generate_markers_btn)
            if self.user_mgmt_btn and self.user_mgmt_btn.isVisible():
                header_row.addWidget(self.user_mgmt_btn)
            header_row.addWidget(self.restore_default_btn)
            self.current_layout.addLayout(header_row)
        
        # Re-parent all widgets
        widgets = [self.back_btn, self.title, self.generate_markers_btn, self.restore_default_btn]
        if self.user_mgmt_btn:
            widgets.append(self.user_mgmt_btn)
        for w in widgets:
            w.setParent(self)
            w.show()
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.layout():
                self._clear_layout(item.layout())


class SettingsPage(QWidget):
    def __init__(self, parent=None, config: SystemConfig = None):
        super().__init__(parent)
        self.config = SystemConfig()
        self.qt_settings = QSettings("Shastra_Proof_Yard", "config_settings")
        self._can_modify = can_modify_settings()
        self.setup_ui()
        self.load_settings()
        self._apply_permission_restrictions()

    def setup_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ 
                background: {BACKGROUND}; 
                border: none; 
            }}
            QScrollBar:vertical {{
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar:horizontal {{
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background: #c0c0c0;
                border-radius: 5px;
                min-width: 30px;
            }}
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background: {BACKGROUND};")
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- Card & Header ---
        card = QWidget()
        card.setObjectName("settingsCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card.setStyleSheet(f"QWidget#settingsCard {{ background-color: {CARD_BG}; border-radius: 14px; border: 1px solid #E0E0E0; }}")

        # Create header buttons
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{ 
                color: {PRIMARY_BLUE}; 
                border: 1px solid {PRIMARY_BLUE}; 
                border-radius: 6px; 
                padding: 6px 12px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE};
            }}
        """)
        self.back_btn.clicked.connect(self.go_back)
        
        title = QLabel("Settings")
        title.setStyleSheet(f"color: {PRIMARY_BLUE}; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        self.generate_markers_btn = QPushButton("Generate Markers")
        self.generate_markers_btn.setCursor(Qt.PointingHandCursor)
        self.generate_markers_btn.setStyleSheet(f"""
            QPushButton {{
                color: {PRIMARY_BLUE}; 
                border: 1px solid {PRIMARY_BLUE}; 
                border-radius: 6px; 
                padding: 8px 12px; 
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE};
            }}
        """)
        self.generate_markers_btn.clicked.connect(lambda: generate_aruco_markers(self))

        self.restore_default_btn = QPushButton("Restore Default")
        self.restore_default_btn.setCursor(Qt.PointingHandCursor)
        self.restore_default_btn.setStyleSheet(f"""
            QPushButton {{
                color: {PRIMARY_RED}; 
                border: 1px solid {PRIMARY_RED}; 
                border-radius: 6px; 
                padding: 8px 12px; 
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #FFEBEE;
            }}
        """)
        self.restore_default_btn.clicked.connect(self.restore_defaults)
        
        # Responsive header widget
        self.header_widget = ResponsiveHeaderWidget()
        self.header_widget.setup(self.back_btn, title, self.generate_markers_btn, self.restore_default_btn)
        card_layout.addWidget(self.header_widget)

        # --- Settings Components ---
        self.settings_container = ResponsiveSettingsContainer()
        system_config_card = create_system_config_settings(self)
        advanced_settings_card = create_advanced_settings(self)
        self.settings_container.set_widgets(system_config_card, advanced_settings_card)
        card_layout.addWidget(self.settings_container, 1)

        # --- Bind Browse Buttons ---
        self.bind_browser(self.pdf_output_folder_btn, self.pdf_output_folder)
        self.bind_browser(self.input_img_folder_btn, self.input_img_folder)
        self.bind_browser(self.img_db_folder_btn, self.img_db_folder)
        self.bind_browser(self.gen_markers_folder_btn, self.gen_markers_folder)

        # --- Save Footer ---
        save_row = QHBoxLayout()
        save_row.setAlignment(Qt.AlignCenter)
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setMinimumSize(140, 45)
        self.save_btn.setMaximumWidth(200)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {PRIMARY_BLUE}; 
                color: white; 
                border-radius: 8px; 
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_BLUE_DARK};
            }}
        """)
        self.save_btn.clicked.connect(self.save_settings)
        save_row.addWidget(self.save_btn)
        card_layout.addLayout(save_row)

        layout.addWidget(card)
        scroll_area.setWidget(content_widget)
        
        # Set minimum size for scroll area content
        content_widget.setMinimumWidth(320)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # Set minimum window size
        self.setMinimumSize(350, 400)

    def bind_browser(self, btn, line_edit):
        """Helper to connect a button to a directory browser dialog."""
        btn.clicked.connect(lambda: self.browse_directory(line_edit))

    def browse_directory(self, line_edit):
        last_dir = self.qt_settings.value("ui/last_browse_dir", "")
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", last_dir)
        if directory:
            line_edit.setText(directory)
            self.qt_settings.setValue("ui/last_browse_dir", directory)

    def load_settings(self):
        c = self.config
        
        # --- System Configs ---
        self.pdf_output_folder.setText(c.PDF_OUTPUT_FOLDER)
        self.input_img_folder.setText(c.INPUT_IMG_FOLDER)
        self.img_db_folder.setText(c.IMG_DB_FOLDER)
        self.gen_markers_folder.setText(c.GENERATED_MARKERS_FOLDER)
        
        self.grid_w.setText(str(c.MARKER_GRID_SIZE_MM[0]))
        self.grid_h.setText(str(c.MARKER_GRID_SIZE_MM[1]))
        
        self.sheet_w.setText(str(c.SHEET_SIZE_MM[0]))
        self.sheet_h.setText(str(c.SHEET_SIZE_MM[1]))

        self.aruco_size.setText(str(c.ARUCO_SIZE_MM))
        self.max_mean_deviation.setText(str(c.MAX_MEAN_DEVIATION_MM))
        self.avg_muzzle_velocity.setText(str(c.AVG_MUZZLE_VELOCITY))

        # --- Advanced Settings ---
        self.diff_threshold.setText(str(c.DIFF_THRESHOLD))
        self.dist_transform_thresh.setText(str(c.DIST_TRANSFORM_THRESHOLD))
        self.median_blur.setText(str(c.MEDIAN_BLUR_KERNEL))
        self.dilate_iter.setText(str(c.DILATE_ITERATIONS))
        
        self.morph_w.setText(str(c.MORPH_KERNEL_SIZE[0]))
        self.morph_h.setText(str(c.MORPH_KERNEL_SIZE[1]))
        
        self.min_hole_area.setText(str(c.MIN_HOLE_AREA_PX))
        self.max_hole_area.setText(str(c.MAX_HOLE_AREA_PX))
        
        self.out_w.setText(str(c.OUTPUT_PX[0]))
        self.out_h.setText(str(c.OUTPUT_PX[1]))

    def save_settings(self):
        # Check permission before saving
        if not self._can_modify:
            QMessageBox.warning(
                self,
                "Access Denied",
                "You don't have permission to modify settings."
            )
            return
        
        c = self.config
        
        try:
            # System
            c.PDF_OUTPUT_FOLDER = self.pdf_output_folder.text()
            c.INPUT_IMG_FOLDER = self.input_img_folder.text()
            c.IMG_DB_FOLDER = self.img_db_folder.text()
            c.GENERATED_MARKERS_FOLDER = self.gen_markers_folder.text()
            
            c.MARKER_GRID_SIZE_MM = (float(self.grid_w.text()), float(self.grid_h.text()))
            c.SHEET_SIZE_MM = (float(self.sheet_w.text()), float(self.sheet_h.text()))
            c.ARUCO_SIZE_MM = float(self.aruco_size.text())
            c.MAX_MEAN_DEVIATION_MM = float(self.max_mean_deviation.text())
            c.AVG_MUZZLE_VELOCITY = float(self.avg_muzzle_velocity.text())
            
            # Advanced
            c.DIFF_THRESHOLD = int(self.diff_threshold.text())
            c.DIST_TRANSFORM_THRESHOLD = float(self.dist_transform_thresh.text())
            c.MEDIAN_BLUR_KERNEL = int(self.median_blur.text())
            c.DILATE_ITERATIONS = int(self.dilate_iter.text())
            c.MORPH_KERNEL_SIZE = (int(self.morph_w.text()), int(self.morph_h.text()))
            c.MIN_HOLE_AREA_PX = int(self.min_hole_area.text())
            c.MAX_HOLE_AREA_PX = int(self.max_hole_area.text())
            c.OUTPUT_PX = (int(self.out_w.text()), int(self.out_h.text()))

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Please check your inputs. Numeric values required.\nError: {e}")
            return

        c.save() # Sync
        
        # Log settings modification
        from auth.auth_manager import get_auth_manager
        auth_mgr = get_auth_manager()
        if auth_mgr.current_session:
            from db.db_init import get_db
            db = get_db()
            db.log_audit(
                action="SETTINGS_MODIFIED",
                user_id=auth_mgr.current_session.user_id,
                username=auth_mgr.current_session.username,
                details="Application settings modified"
            )
        
        QMessageBox.information(self, "Success", "Settings saved successfully.")

    def restore_defaults(self):
        if not self._can_modify:
            QMessageBox.warning(
                self,
                "Access Denied",
                "You don't have permission to modify settings."
            )
            return
        
        if QMessageBox.question(self, "Confirm", "Reset all settings?") == QMessageBox.Yes:
            self.qt_settings.clear() # Clear UI memory
            self.config.settings.clear() # Clear backend memory
            self.load_settings()
            QMessageBox.information(self, "Restored", "Default settings restored.")

    def go_back(self):
        if self.parent() and hasattr(self.parent().parent(), 'stack'):
            self.parent().parent().stack.setCurrentWidget(self.parent().parent().main_page)
    
    def _apply_permission_restrictions(self):
        """Apply UI restrictions based on user permissions."""
        if not self._can_modify:
            # Disable editing for operators
            self._set_inputs_readonly(True)
            
            # Update save button appearance
            self.save_btn.setEnabled(False)
            self.save_btn.setText("View Only")
            self.save_btn.setStyleSheet(f"""
                QPushButton {{ 
                    background-color: #B0BEC5; 
                    color: white; 
                    border-radius: 8px; 
                    font-weight: bold;
                    font-size: 14px;
                    padding: 10px 20px;
                }}
            """)
            
            # Disable restore defaults
            self.restore_default_btn.setEnabled(False)
    
    def _set_inputs_readonly(self, readonly: bool):
        """Set all input fields to read-only mode."""
        # Line edits
        line_edits = [
            self.pdf_output_folder, self.input_img_folder, 
            self.img_db_folder, self.gen_markers_folder,
            self.grid_w, self.grid_h, self.sheet_w, self.sheet_h,
            self.aruco_size, self.max_mean_deviation,
            self.diff_threshold, self.dist_transform_thresh,
            self.median_blur, self.dilate_iter,
            self.morph_w, self.morph_h,
            self.min_hole_area, self.max_hole_area,
            self.out_w, self.out_h
        ]
        
        for edit in line_edits:
            if hasattr(edit, 'setReadOnly'):
                edit.setReadOnly(readonly)
        
        # Browse buttons
        browse_btns = [
            self.pdf_output_folder_btn, self.input_img_folder_btn,
            self.img_db_folder_btn, self.gen_markers_folder_btn
        ]
        for btn in browse_btns:
            if hasattr(btn, 'setEnabled'):
                btn.setEnabled(not readonly)