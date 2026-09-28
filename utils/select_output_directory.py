from PyQt5.QtWidgets import QFileDialog, QPushButton, QHBoxLayout

def select_output_directory(self):
    """Open dialog to select output directory"""
    directory = QFileDialog.getExistingDirectory(
        self,
        "Select Output Directory",
        "",
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
    )
    if directory:
        self.output_dir.setText(directory)