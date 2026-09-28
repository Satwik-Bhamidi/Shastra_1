from PyQt5.QtWidgets import QLineEdit, QSizePolicy
from styles.theme import *

class StyledLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #B0BEC5;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 14px;
                color: {TEXT_COLOR};
                background-color: #FAFAFA;
            }}
            QLineEdit:focus {{
                border: 1px solid {PRIMARY_BLUE};
                background-color: #FFFFFF;
            }}
        """)