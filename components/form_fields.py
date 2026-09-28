from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QSizePolicy, QHBoxLayout, QComboBox, 
    QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QSettings
from components.styled_input import StyledLineEdit as make_line_edit
from styles.theme import *
import json


class FormFields(QWidget):
    """Form fields component for collecting ammunition data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_form()

    def setup_form(self):
        """Setup the form layout with all input fields"""
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        form_layout = QFormLayout(self)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(10)

        # Create input fields
        self.amk_no = make_line_edit()
        self.name = make_line_edit()
        self.lot_no = make_line_edit()
        self.weapon_used = make_line_edit()
        self.sample_size = make_line_edit()
        self.temperature = make_line_edit()

        # Add rows to form
        form_layout.addRow("AMK No", self.amk_no)
        form_layout.addRow("Nomenclature", self.name)
        form_layout.addRow("Lot No", self.lot_no)
        form_layout.addRow("Weapon Used", self.weapon_used)
        form_layout.addRow("Sample Size", self.sample_size)
        form_layout.addRow("Temperature (C)", self.temperature)

    def clear_all(self):
        """Clear all form fields"""
        self.amk_no.clear()
        self.name.clear()
        self.lot_no.clear()
        self.weapon_used.clear()
        self.sample_size.clear()
        self.temperature.clear()

    def get_fields(self):
        """Return list of field tuples for validation"""
        return [
            (self.amk_no, "AMK No"),
            (self.name, "Name"),
            (self.lot_no, "Lot No"),
            (self.weapon_used, "Weapon Used"),
            (self.sample_size, "Sample Size"),
            (self.temperature, "Temperature"),
        ]

    def get_data(self):
        """Return form data as a dictionary"""
        return {
            "amk_no": self.amk_no.text().strip(),
            "name": self.name.text().strip(),
            "lot_no": self.lot_no.text().strip(),
            "weapon_used": self.weapon_used.text().strip(),
            "sample_size": self.sample_size.text().strip(),
            "temperature": self.temperature.text().strip(),
        }