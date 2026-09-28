from styles.theme import *
from PyQt5.QtWidgets import QMessageBox
def show_error_message(parent, title, message):
    """Display a styled error message box"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setStandardButtons(QMessageBox.Ok)
    
    # Style the message box
    msg_box.setStyleSheet(
        f"""
        QMessageBox {{
            background-color: {CARD_BG};
        }}
        QMessageBox QLabel {{
            color: {TEXT_COLOR};
            font-size: 14px;
            padding: 10px;
        }}
        QPushButton {{
            background-color: {PRIMARY_BLUE};
            color: white;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            padding: 8px 20px;
            border: none;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_BLUE_DARK};
        }}
    """
    )
    
    msg_box.exec_()
