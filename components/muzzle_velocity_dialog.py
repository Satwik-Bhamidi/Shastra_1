"""
Muzzle Velocity Entry Panel
Allows users to enter muzzle velocity for each shot one by one with visual feedback.
Non-blocking panel that runs side-by-side with the preview.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

from styles.theme import (
    PRIMARY_BLUE, PRIMARY_GREEN, PRIMARY_RED, LIGHT_BLUE, 
    LIGHT_BLUE_HOVER, TEXT_COLOR, CARD_BG
)


class MuzzleVelocityEntryPanel(QWidget):
    """
    Non-blocking panel for entering muzzle velocity for each shot.
    Runs side-by-side with the preview and emits signals to highlight shots.
    Keeps track of current_shot_index and manages shot highlighting.
    """
    
    velocities_complete = pyqtSignal(list)  # Emits list of velocities when complete
    shot_highlighted = pyqtSignal(int)  # Emits current shot index to highlight
    panel_closed = pyqtSignal()  # Emitted when panel is closed
    
    def __init__(self, parent=None, shot_count=0):
        super().__init__(parent)
        self.shot_count = shot_count
        self.current_shot_index = 0
        self.velocities = [None] * shot_count
        self.is_active = False
        
        self.setMinimumWidth(380)
        self.setMaximumWidth(420)
        self.setObjectName("MuzzlePanel")
        self.setStyleSheet(f"""
            #MuzzleEntryPanel {{
                background-color: {CARD_BG};
                border: 1px solid #E0E0E0;
            }}
        """)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Muzzle Velocity Entry")
        header.setFont(QFont("Helvetica", 15, QFont.Bold))
        header.setStyleSheet(f"color: {PRIMARY_BLUE};")
        layout.addWidget(header)
        
        # Progress Info
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 15px; font-weight: bold;")
        layout.addWidget(self.progress_label)
        
        # Input Section
        input_label = QLabel("Enter velocity (m/s):")
        input_label.setStyleSheet(f"color: {TEXT_COLOR}; font-weight: bold; font-size: 15px;")
        layout.addWidget(input_label)
        
        self.velocity_input = QLineEdit()
        self.velocity_input.setPlaceholderText("e.g., 825.5")
        self.velocity_input.setFixedHeight(36)
        self.velocity_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {PRIMARY_BLUE};
                border-radius: 6px;
                padding: 7px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {PRIMARY_GREEN};
                background-color: rgba(25, 118, 210, 0.05);
            }}
        """)
        self.velocity_input.returnPressed.connect(self.on_next_shot)
        layout.addWidget(self.velocity_input)
        
        # Instructions
        instructions = QLabel(
            "Press Enter or click 'Next' for the next shot.\n"
            "Click 'Finish' when done to enable print."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 12px; font-style: italic;")
        layout.addWidget(instructions)
        
        layout.addStretch()
        
        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.cancel_btn = QPushButton("Close")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_RED};
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton:hover {{ background-color: #C62828; }}
        """)
        self.cancel_btn.clicked.connect(self.close_panel)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setFixedHeight(36)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BLUE};
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 5px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton:hover {{ background-color: {LIGHT_BLUE_HOVER}; }}
        """)
        self.next_btn.clicked.connect(self.on_next_shot)
        
        self.finish_btn = QPushButton("Finish")
        self.finish_btn.setCursor(Qt.PointingHandCursor)
        self.finish_btn.setFixedHeight(36)
        self.finish_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_GREEN};
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton:hover {{ background-color: #2E7D32; }}
        """)
        self.finish_btn.clicked.connect(self.finish_entry)
        
        # Set auto default to false
        self.next_btn.setAutoDefault(False)
        self.next_btn.setDefault(False)
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.setDefault(False)
        self.finish_btn.setAutoDefault(False)
        self.finish_btn.setDefault(False)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.next_btn)
        button_layout.addWidget(self.finish_btn)
        layout.addLayout(button_layout)
    
    def start(self):
        """Start the velocity entry process"""
        self.is_active = True
        self.current_shot_index = 0
        self.velocities = [None] * self.shot_count
        self.show_current_shot()
    
    def get_current_shot_index(self):
        """Return the current shot index being edited"""
        return self.current_shot_index
    
    def show_current_shot(self):
        """Display the current shot and emit signal to highlight it"""
        if self.current_shot_index >= self.shot_count:
            self.finish_entry()
            return
        
        shot_num = self.current_shot_index + 1
        self.progress_label.setText(f"Shot {shot_num} of {self.shot_count}")
        
        # Update velocity input with existing value if any
        if self.velocities[self.current_shot_index] is not None:
            self.velocity_input.setText(str(self.velocities[self.current_shot_index]))
        else:
            self.velocity_input.clear()
        
        self.velocity_input.setFocus()
        self.velocity_input.selectAll()
        
        # Emit signal to highlight the current shot in the image
        self.shot_highlighted.emit(self.current_shot_index)
    
    def on_next_shot(self):
        """Handle next shot button or Enter key"""
        velocity_text = self.velocity_input.text().strip()
        
        if not velocity_text:
            QMessageBox.warning(
                self,
                "Input Required",
                "Please enter a muzzle velocity value."
            )
            return
        
        try:
            velocity = float(velocity_text)
            if velocity <= 0:
                raise ValueError("Velocity must be positive")
            
            self.velocities[self.current_shot_index] = velocity
            self.current_shot_index += 1
            self.show_current_shot()
            
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a valid positive number for velocity."
            )
    
    def finish_entry(self):
        """Complete the velocity entry and emit signal"""
        # Check if all velocities are entered
        if any(v is None for v in self.velocities):
            reply = QMessageBox.question(
                self,
                "Incomplete Entries",
                f"You have not entered velocity for all shots.\n"
                f"Fill remaining with average of entered values?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                entered_velocities = [v for v in self.velocities if v is not None]
                if entered_velocities:
                    avg_velocity = sum(entered_velocities) / len(entered_velocities)
                    for i in range(len(self.velocities)):
                        if self.velocities[i] is None:
                            self.velocities[i] = avg_velocity
                else:
                    QMessageBox.warning(self, "Error", "No velocities entered.")
                    return
            else:
                return
        
        self.is_active = False
        self.velocities_complete.emit(self.velocities)
        self.hide()
    
    def close_panel(self):
        """Close the panel without completing"""
        self.is_active = False
        self.panel_closed.emit()
        self.hide()
