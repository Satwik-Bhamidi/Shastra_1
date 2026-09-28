from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from styles.theme import PRIMARY_BLUE, LIGHT_BLUE, LIGHT_BLUE_HOVER, TEXT_COLOR, PRIMARY_GREEN, PRIMARY_RED

class PreviewControlPanel(QWidget):
    zoom_requested = pyqtSignal(float)
    print_preview_requested = pyqtSignal()
    enter_muzzle_velocity_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMaximumWidth(450)
        self.muzzle_velocity_complete = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        # Instructions
        title = QLabel("Instructions")
        title.setStyleSheet(f"color: {PRIMARY_BLUE}; font-size: 18px; font-weight: bold;")
        
        text = QLabel("• Left-click on the image to add a shot.\n"
                      "• Right-click on a shot to delete it.")
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")

        # Zoom Controls
        zoom_title = QLabel("Image Zoom")
        zoom_title.setStyleSheet(f"color: {PRIMARY_BLUE}; font-size: 16px; font-weight: bold;")
        
        zoom_layout = QHBoxLayout()
        zoom_in = QPushButton("+ Zoom In")
        zoom_out = QPushButton("- Zoom Out")
        
        btn_style = f"""
            QPushButton {{
                background-color: {LIGHT_BLUE};
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 6px;
                font-weight: bold;
                padding: 8px;
            }}
            QPushButton:hover {{ background-color: {LIGHT_BLUE_HOVER}; }}
        """
        zoom_in.setStyleSheet(btn_style)
        zoom_out.setStyleSheet(btn_style)
        
        zoom_in.setCursor(Qt.PointingHandCursor)
        zoom_out.setCursor(Qt.PointingHandCursor)
        
        zoom_in.clicked.connect(lambda: self.zoom_requested.emit(1.2))
        zoom_out.clicked.connect(lambda: self.zoom_requested.emit(0.8))
        
        zoom_layout.addWidget(zoom_in)
        zoom_layout.addWidget(zoom_out)

        # Session Stats
        stats_title = QLabel("Session Statistics")
        stats_title.setStyleSheet(f"color: {PRIMARY_BLUE}; font-size: 18px; font-weight: bold;")
        
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")
        self.set_status_processing()

        # Print and Export Button (above Save button)
        self.print_btn = QPushButton("🖨️ Print and Export")
        self.print_btn.setCursor(Qt.PointingHandCursor)
        self.print_btn.setFixedHeight(45)
        self.print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BLUE};
                color: {PRIMARY_BLUE};
                border: 2px solid {PRIMARY_BLUE};
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background-color: {LIGHT_BLUE_HOVER}; 
            }}
        """)
        self.print_btn.clicked.connect(self.print_preview_requested.emit)

        # Muzzle Velocity Button
        self.muzzle_velocity_btn = QPushButton("Enter Muzzle Velocity")
        self.muzzle_velocity_btn.setCursor(Qt.PointingHandCursor)
        self.muzzle_velocity_btn.setFixedHeight(45)
        self.muzzle_velocity_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {LIGHT_BLUE};
                color: {PRIMARY_BLUE};
                border: 2px solid {PRIMARY_BLUE};
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background-color: {LIGHT_BLUE_HOVER}; 
            }}
        """)
        self.muzzle_velocity_btn.clicked.connect(self.enter_muzzle_velocity_requested.emit)

        # Add to layout
        layout.addWidget(title)
        layout.addWidget(text)
        layout.addSpacing(15)
        layout.addWidget(zoom_title)
        layout.addLayout(zoom_layout)
        layout.addSpacing(20)
        layout.addWidget(stats_title)
        layout.addWidget(self.stats_label)
        layout.addStretch()
        layout.addWidget(self.muzzle_velocity_btn)
        layout.addWidget(self.print_btn)
        layout.addSpacing(8)

    def set_status_processing(self):
        self.stats_label.setText("Processing... No statistics to display yet.")

    def update_stats(self, stats, cfg, avg_muzzle_velocity=None):
        if avg_muzzle_velocity is None:
            muzzle_passed = True
        else:
            muzzle_passed = avg_muzzle_velocity >= cfg.AVG_MUZZLE_VELOCITY
        passed_both = stats.passed and muzzle_passed

        status = "PASSED" if passed_both else "FAILED"
        status_color = PRIMARY_GREEN if passed_both else "#D32F2F"

        # Format muzzle velocity display
        muzzle_velocity_text = f"{avg_muzzle_velocity:.2f} m/s" if avg_muzzle_velocity else "Not entered"
        muzzle_velocity_row = f"""
            <tr>
                <td>Avg Muzzle Velocity</td>
                <td>{muzzle_velocity_text}</td>
            </tr>
        """
        
        html = f"""
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: {PRIMARY_BLUE}; color: white; font-weight: bold;">
                <th align="left">Metric</th>
                <th align="left">Value</th>
            </tr>
            <tr>
                <td>Total Shots</td>
                <td>{stats.shot_count}</td>
            </tr>
            <tr>
                <td>Mean Point of Impact (MPI)</td>
                <td>({(stats.mean_point_of_impact_mm[0] + cfg.OFFSET_X):.2f}, {(stats.mean_point_of_impact_mm[1] + cfg.OFFSET_Y):.2f}) mm</td>
            </tr>
            <tr>
                <td>Mean Radius Deviation</td>
                <td>{stats.mean_radius_deviation_mm:.2f} mm</td>
            </tr>
            <tr>
                <td>Max Horizontal Spread</td>
                <td>{stats.max_horizontal_spread_mm:.2f} mm</td>
            </tr>
            <tr>
                <td>Max Vertical Spread</td>
                <td>{stats.max_vertical_spread_mm:.2f} mm</td>
            </tr>
            <tr>
                <td>Performance Required</td>
                <td>{cfg.MAX_MEAN_DEVIATION_MM:.2f} mm</td>
            </tr>
            {muzzle_velocity_row}
            <tr style="background-color: {status_color}; color: white; font-weight: bold;">
                <td>Final Result</td>
                <td>{status}</td>
            </tr>
        </table>
        """
        self.stats_label.setText(html)