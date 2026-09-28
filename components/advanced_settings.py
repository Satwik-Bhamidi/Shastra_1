from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QFormLayout, QLineEdit
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


def create_advanced_settings(page):
        """Create advanced settings section. 'page' is the SettingsPage instance."""
        container = QWidget()
        container.setObjectName("advancedSettingsCard")
        container.setStyleSheet(
            f"""
            QWidget#advancedSettingsCard {{
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
        title = QLabel("Advanced Settings")
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

        def add_input(label, attr_name, placeholder=""):
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setStyleSheet(get_responsive_input_style())
            setattr(page, attr_name, le)
            form_layout.addRow(label, le)

        # --- Tuning Parameters ---
        
        # Thresholds
        add_input("Diff Threshold (0-255):", "diff_threshold")
        add_input("Dist Transform Threshold (0.0-1.0):", "dist_transform_thresh")
        
        # Kernels
        add_input("Median Blur Kernel (Odd Int):", "median_blur")
        add_input("Dilate Iterations:", "dilate_iter")

        # Morph Kernel (Tuple)
        page.morph_w = QLineEdit()
        page.morph_h = QLineEdit()
        page.morph_w.setStyleSheet(get_responsive_input_style())
        page.morph_h.setStyleSheet(get_responsive_input_style())
        
        morph_layout = QHBoxLayout()
        morph_layout.addWidget(page.morph_w)
        morph_layout.addWidget(QLabel("x"))
        morph_layout.addWidget(page.morph_h)
        form_layout.addRow("Morph Kernel Size:", morph_layout)

        # Areas
        add_input("Min Hole Area (px):", "min_hole_area")
        add_input("Max Hole Area (px):", "max_hole_area")
        
        # Output px
        page.out_w = QLineEdit()
        page.out_h = QLineEdit()
        page.out_w.setStyleSheet(get_responsive_input_style())
        page.out_h.setStyleSheet(get_responsive_input_style())

        out_layout = QHBoxLayout()
        out_layout.addWidget(page.out_w)
        out_layout.addWidget(QLabel("x"))
        out_layout.addWidget(page.out_h)
        form_layout.addRow("Output px size:", out_layout)

        layout.addLayout(form_layout)
        layout.addStretch()
        
        return container