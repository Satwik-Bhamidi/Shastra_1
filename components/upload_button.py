from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from styles.theme import *
from utils.resource_path import resource_path
from backend.config import SystemConfig

class ImagePreviewWorker(QThread):
    """Worker thread to load and scale images in background to prevent UI freeze."""
    finished = pyqtSignal(QPixmap)

    def __init__(self, path, target_size):
        super().__init__()
        self.path = path
        self.size = target_size

    def run(self):
        pixmap = QPixmap(self.path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.size - QSize(20, 20), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.finished.emit(scaled)
        else:
            self.finished.emit(QPixmap())

class UploadButton(QWidget):
    """Styled upload box used for Before/After firing images."""

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.has_image = False
        self.image_path = None
        self.config = SystemConfig()
        self.worker = None

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create the main upload button
        self.upload_btn = QPushButton(label_text)
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setMinimumSize(200, 150)
        self.upload_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.upload_btn.setIcon(QIcon(resource_path("assets/photo.png")))
        self.upload_btn.setIconSize(QSize(40, 40))
        self.upload_btn.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px dashed {PRIMARY_BLUE};
                background-color: {LIGHT_BLUE};
                border-radius: 12px;
                padding: 18px;
                font-size: 14px;
                color: {TEXT_COLOR};
                text-align: center;
                white-space: pre-wrap;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE_HOVER};
            }}
        """
        )
        self.upload_btn.clicked.connect(self.open_file_dialog)
        
        # Create remove button (initially hidden)
        self.remove_btn = QPushButton("✕ Remove")
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setFixedSize(100, 36)
        self.remove_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: white;
                color: #333333;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: #fee2e2;
                color: #dc2626;
                border-color: #dc2626;
            }}
        """
        )
        self.remove_btn.clicked.connect(self.remove_image)
        self.remove_btn.hide()
        
        layout.addWidget(self.upload_btn)
        self.remove_btn.setParent(self.upload_btn)
        
        self.upload_btn.installEventFilter(self)
        
    def enterEvent(self, event):
        if self.has_image:
            self.remove_btn.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.remove_btn.hide()
        super().leaveEvent(event)
    
    def eventFilter(self, obj, event):
        if obj == self.upload_btn and event.type() == event.Resize:
            self._center_remove_button()
        return super().eventFilter(obj, event)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center_remove_button()
        # Update icon size if an image is loaded
        if self.has_image:
            self.upload_btn.setIconSize(self.upload_btn.size() - QSize(20, 20))
    
    def _center_remove_button(self):
        btn_width = self.remove_btn.width()
        btn_height = self.remove_btn.height()
        parent_width = self.upload_btn.width()
        parent_height = self.upload_btn.height()
        
        x = (parent_width - btn_width) // 2
        y = (parent_height - btn_height) // 2
        self.remove_btn.move(x, y)

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            self.config.INPUT_IMG_FOLDER,
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)",
        )

        if file_name:
            # Show loading state
            self.upload_btn.setText("Loading...")
            self.upload_btn.setEnabled(False)
            
            # Start background worker
            self.worker = ImagePreviewWorker(file_name, self.upload_btn.size())
            self.worker.finished.connect(lambda pix: self.set_preview_image(pix, file_name))
            self.worker.start()

    def set_preview_image(self, pixmap, file_path):
        """Slot to handle loaded image from worker"""
        self.upload_btn.setEnabled(True)
        if pixmap.isNull():
            self.upload_btn.setText("Error loading image")
            return

        self.has_image = True
        self.image_path = file_path
        
        # Configure button to show image as icon
        self.upload_btn.setText("")
        self.upload_btn.setIcon(QIcon(pixmap))
        self.upload_btn.setIconSize(self.upload_btn.size() - QSize(20, 20))
        self.upload_btn.setToolTip(file_path)
        
        # Update style (remove background-image approach)
        self.upload_btn.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px dashed {PRIMARY_BLUE};
                background-color: {LIGHT_BLUE};
                border-radius: 12px;
                padding: 0px;
                font-size: 14px;
                color: {TEXT_COLOR};
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE_HOVER};
            }}
            """
        )

    def remove_image(self):
        """Remove the uploaded image and restore placeholder"""
        self.has_image = False
        self.image_path = None
        self.remove_btn.hide()
        
        # Restore placeholder
        self.upload_btn.setIcon(QIcon(resource_path("assets/photo.png")))
        self.upload_btn.setIconSize(QSize(40, 40))
        self.upload_btn.setText(self.label_text)
        self.upload_btn.setStyleSheet(
            f"""
            QPushButton {{
                border: 2px dashed {PRIMARY_BLUE};
                background-color: {LIGHT_BLUE};
                border-radius: 12px;
                padding: 18px;
                font-size: 14px;
                color: {TEXT_COLOR};
                text-align: center;
                white-space: pre-wrap;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE_HOVER};
            }}
        """
        )
        self.upload_btn.setToolTip("")
    
    def toolTip(self):
        """Return the image path for compatibility"""
        return self.image_path