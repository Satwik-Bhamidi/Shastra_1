from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFormLayout, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt
from styles.theme import *


def get_responsive_input_style():
    """Return responsive styled input CSS"""
    return f"""
        QLineEdit {{
            border: 1px solid #B0BEC5;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
            color: {TEXT_COLOR};
            background-color: #FAFAFA;
            min-width: 120px;
        }}
        QLineEdit:focus {{
            border: 1px solid {PRIMARY_BLUE};
            background-color: #FFFFFF;
        }}
    """


def get_responsive_combo_style():
    """Return responsive styled combo box CSS"""
    return f"""
        QComboBox {{
            border: 1px solid #B0BEC5;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
            color: {TEXT_COLOR};
            background-color: #FAFAFA;
            min-width: 120px;
        }}
        QComboBox:focus {{
            border: 1px solid {PRIMARY_BLUE};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
    """


def create_system_config_settings(page):
        """Create system config settings section. 'page' is the SettingsPage instance."""
        container = QWidget()
        container.setObjectName("systemConfigCard")
        container.setStyleSheet(
            f"""
            QWidget#systemConfigCard {{
                background-color: #FAFAFA;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }}
        """
        )
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # Section title
        title = QLabel("System Config Settings")
        title.setStyleSheet(
            f"""
            QLabel {{
                color: {PRIMARY_BLUE};
                font-size: 16px;
                font-weight: bold;
            }}
        """
        )
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(8)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # --- Helper to create file/folder inputs ---
        def add_path_row(label, attr_name):
            line_edit = QLineEdit()
            line_edit.setReadOnly(True)
            line_edit.setStyleSheet(get_responsive_input_style())
            
            btn = QPushButton("Browse")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PRIMARY_BLUE};
                    color: white;
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {PRIMARY_BLUE_DARK}; }}
            """)
            
            # Attach to page instance
            setattr(page, attr_name, line_edit)
            setattr(page, f"{attr_name}_btn", btn)
            
            row_layout = QHBoxLayout()
            row_layout.addWidget(line_edit)
            row_layout.addWidget(btn)
            form_layout.addRow(label, row_layout)

        # --- File Paths ---
        add_path_row("PDF Output Folder:", "pdf_output_folder")
        add_path_row("Input Image Folder:", "input_img_folder")
        add_path_row("Image DB Folder:", "img_db_folder")
        add_path_row("Generated Markers:", "gen_markers_folder")

        # --- Physical & Vision Configs ---
        
        def add_dual_input(label, attr_w, attr_h, placeholder_w="W", placeholder_h="H"):
            w_edit = QLineEdit()
            h_edit = QLineEdit()
            w_edit.setPlaceholderText(placeholder_w)
            h_edit.setPlaceholderText(placeholder_h)
            w_edit.setStyleSheet(get_responsive_input_style())
            h_edit.setStyleSheet(get_responsive_input_style())
            
            setattr(page, attr_w, w_edit)
            setattr(page, attr_h, h_edit)
            
            l = QHBoxLayout()
            l.addWidget(w_edit)
            l.addWidget(QLabel("x"))
            l.addWidget(h_edit)
            form_layout.addRow(label, l)

        # Marker Grid Size
        add_dual_input("Marker Grid Size (mm):", "grid_w", "grid_h")

        # Sheet Size
        add_dual_input("Sheet Size (mm):", "sheet_w", "sheet_h")

        # Aruco Size (Single float)
        page.aruco_size = QLineEdit()
        page.aruco_size.setStyleSheet(get_responsive_input_style())
        form_layout.addRow("ArUco marker size (mm):", page.aruco_size)

        # Max Mean Deviation
        page.max_mean_deviation = QLineEdit()
        page.max_mean_deviation.setStyleSheet(get_responsive_input_style())
        form_layout.addRow("Max Mean Deviation (mm):", page.max_mean_deviation)

        # Average Muzzle Velocity
        page.avg_muzzle_velocity = QLineEdit()
        page.avg_muzzle_velocity.setStyleSheet(get_responsive_input_style())
        form_layout.addRow("Average Muzzle Velocity (m/s):", page.avg_muzzle_velocity)

        layout.addLayout(form_layout)
        
        # --- ArUco Marker Positioning Guide ---
        guide_container = QWidget()
        guide_layout = QVBoxLayout(guide_container)
        guide_layout.setContentsMargins(0, 15, 0, 0)
        guide_layout.setSpacing(10)
        
        guide_title = QLabel("ArUco Marker Placement Guide")
        guide_title.setStyleSheet(
            f"""
            QLabel {{
                color: {PRIMARY_BLUE};
                font-size: 16px;
                font-weight: bold;
            }}
        """
        )
        guide_layout.addWidget(guide_title)
        
        guide_text = QLabel(
            "Place ArUco markers on four corners of target sheet in the following order:\n\n"
            "• Top Left (TL): ID 0\n"
            "• Top Right (TR): ID 1\n"
            "• Bottom Left (BL): ID 2\n"
            "• Bottom Right (BR): ID 3\n\n"
            "Ensure markers are aligned properly in a square grid for accurate measurements.\n" 
            "Provide some white padding to the markers for detection, keep size <= 200mm.\n"
            "Print the markers at actual size of PDFs on A4 sheets."
        )
        guide_text.setStyleSheet(
            f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-size: 14px;
                line-height: 1.5;
                padding: 10px;
                background-color: #F5F5F5;
                border-radius: 6px;
            }}
        """
        )
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)
        
        layout.addWidget(guide_container)
        layout.addStretch()
        
        return container