"""
PDF Preview Dialog Component
Provides a preview of the generated PDF with print and export functionality.
Uses QThread for non-blocking PDF generation and printing.
"""

import os
import tempfile
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QSizePolicy, QMessageBox, QProgressBar,
    QFrame, QSlider, QSpinBox, QFileDialog, QApplication, QShortcut
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QIcon, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog        

from styles.theme import (
    PRIMARY_BLUE, PRIMARY_GREEN, LIGHT_BLUE, LIGHT_BLUE_HOVER, 
    TEXT_COLOR, CARD_BG, PRIMARY_RED
)
from backend.config import SystemConfig
import fitz  # PyMuPDF
        
import subprocess
import sys


class PDFGeneratorWorker(QThread):
    """Worker thread to generate PDF preview images"""
    finished = pyqtSignal(list, object)  # List of QPixmap pages, PDF path
    progress = pyqtSignal(int, str)   # Progress percentage, status message
    error = pyqtSignal(str)

    def __init__(self, session_manager, generate_report_func):
        super().__init__()
        self.session_manager = session_manager
        self.generate_report_func = generate_report_func
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.progress.emit(10, "Preparing report data...")
            
            if self._is_cancelled:
                return
            
            self.progress.emit(30, "Generating PDF...")
            
            pdf_bytes = self.generate_report_func(self.session_manager, return_bytes=True)
            
            if self._is_cancelled:
                return
            
            self.progress.emit(60, "Rendering preview...")

            page_images = self._render_pdf_bytes_to_images(pdf_bytes)
            
            self.progress.emit(100, "Complete!")

            self.finished.emit(page_images, pdf_bytes)
            
        except Exception as e:
            self.error.emit(str(e))

    def _render_pdf_bytes_to_images(self, pdf_bytes):
        page_images = []
        try:
            # FIXED: Open from bytes stream instead of undefined path
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(doc)):
                if self._is_cancelled:
                    doc.close()
                    return []
                
                page = doc.load_page(page_num)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                page_images.append(QPixmap.fromImage(img))
            
            doc.close()
            
        except ImportError:
            # Placeholder if fitz is missing
            placeholder = self._create_placeholder_image("Preview Unavailable")
            page_images.append(placeholder)
        except Exception as e:
            print(f"Render error: {e}")
            
        return page_images

    def _create_placeholder_image(self, pdf_path):
        """Create a placeholder image when PDF rendering is not available"""
        # Create A4 sized placeholder (595 x 842 at 72 DPI, scaled up)
        width, height = 595 * 2, 842 * 2
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(255, 255, 255))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw border
        painter.setPen(QColor(200, 200, 200))
        painter.drawRect(10, 10, width - 20, height - 20)
        
        # Draw text
        painter.setPen(QColor(100, 100, 100))
        font = QFont("Helvetica", 24)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, 
                        f"PDF Preview\n\nFile: {Path(pdf_path).name}\n\n"
                        "Install PyMuPDF for full preview:\n"
                        "pip install PyMuPDF")
        
        painter.end()
        return pixmap

class PDFPreviewDialog(QDialog):   
    def __init__(self, parent=None, session_manager=None, generate_report_func=None, save_func=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.cfg = SystemConfig()
        self.generate_report_func = generate_report_func
        self.save_func = save_func
        self.page_images = []
        self.page_widgets = []  # Keep track of label widgets
        self.zoom_level = 0.7
        self.pdf_path = None
        self.worker = None
        
        self.setWindowTitle("Print & Export Preview")
        self.setModal(True)
        self.resize(1100, 900)
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.setup_shortcuts()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Toolbar ---
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-bottom: 1px solid #E0E0E0;
            }}
        """)
        toolbar.setFixedHeight(50)
        
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(15, 5, 15, 5)
        toolbar_layout.setSpacing(10)
        
        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(f"color: {TEXT_COLOR}; font-weight: bold;")
        
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(32, 32)
        self.zoom_out_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_out_btn.clicked.connect(lambda: self.change_zoom(-0.1))
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.setRange(25, 300)
        self.zoom_slider.setValue(70)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(32, 32)
        self.zoom_in_btn.setCursor(Qt.PointingHandCursor)
        self.zoom_in_btn.clicked.connect(lambda: self.change_zoom(0.1))
        
        self.zoom_percent_label = QLabel(f"{int(self.zoom_level * 100)}%")
        self.zoom_percent_label.setFixedWidth(50)
        self.zoom_percent_label.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.fit_width_btn = QPushButton("Fit Width")
        self.fit_width_btn.setCursor(Qt.PointingHandCursor)
        self.fit_width_btn.clicked.connect(self.fit_to_width)
        
        # Apply toolbar button style
        toolbar_btn_style = f"""
            QPushButton {{
                background-color: {LIGHT_BLUE};
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {LIGHT_BLUE_HOVER};
            }}
        """
        for btn in [self.zoom_out_btn, self.zoom_in_btn, self.fit_width_btn]:
            btn.setStyleSheet(toolbar_btn_style)
        
        # Page navigation
        self.page_label = QLabel("Page:")
        self.page_label.setStyleSheet(f"color: {TEXT_COLOR}; font-weight: bold;")
        
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.setFixedWidth(60)
        self.page_spin.valueChanged.connect(self.on_page_changed)
        
        self.total_pages_label = QLabel("/ 1")
        self.total_pages_label.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.prev_page_btn = QPushButton("◀")
        self.prev_page_btn.setFixedSize(32, 32)
        self.prev_page_btn.setCursor(Qt.PointingHandCursor)
        self.prev_page_btn.setStyleSheet(toolbar_btn_style)
        self.prev_page_btn.clicked.connect(self.prev_page)
        
        self.next_page_btn = QPushButton("▶")
        self.next_page_btn.setFixedSize(32, 32)
        self.next_page_btn.setCursor(Qt.PointingHandCursor)
        self.next_page_btn.setStyleSheet(toolbar_btn_style)
        self.next_page_btn.clicked.connect(self.next_page)
        
        toolbar_layout.addWidget(zoom_label)
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.zoom_slider)
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_percent_label)
        toolbar_layout.addWidget(self.fit_width_btn)
        toolbar_layout.addSpacing(20)
        toolbar_layout.addWidget(self.prev_page_btn)
        toolbar_layout.addWidget(self.page_label)
        toolbar_layout.addWidget(self.page_spin)
        toolbar_layout.addWidget(self.total_pages_label)
        toolbar_layout.addWidget(self.next_page_btn)
        toolbar_layout.addStretch()
        
        main_layout.addWidget(toolbar)
        
        # --- Preview Area ---
        preview_frame = QWidget()
        preview_frame.setStyleSheet("background-color: #505050;")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #505050; }
            QScrollBar { background: #404040; border-radius: 6px; }
            QScrollBar::handle { background: #808080; border-radius: 6px; }
        """)
        
        self.pages_container = QWidget()
        self.pages_container.setStyleSheet("background-color: transparent;")
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setContentsMargins(30, 30, 30, 30)
        self.pages_layout.setSpacing(20)
        self.pages_layout.setAlignment(Qt.AlignHCenter)
        
        self.scroll_area.setWidget(self.pages_container)
        
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.check_current_page_from_scroll)
        
        preview_layout.addWidget(self.scroll_area)
        
        self.loading_widget = QWidget(preview_frame)
        self.loading_widget.setStyleSheet("background-color: rgba(80, 80, 80, 0.9);")
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        self.loading_label = QLabel("Generating Preview...")
        self.loading_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.loading_label.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {PRIMARY_BLUE};
                border-radius: 8px;
                text-align: center;
                background-color: #404040;
                color: white;
            }}
            QProgressBar::chunk {{ background-color: {PRIMARY_BLUE}; border-radius: 6px; }}
        """)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.progress_bar)
        loading_layout.addWidget(self.status_label)
        
        main_layout.addWidget(preview_frame, 1)
        
        # --- Bottom Action Bar ---
        action_bar = QFrame()
        action_bar.setStyleSheet(f"background-color: {CARD_BG}; border-top: 1px solid #E0E0E0;")
        action_bar.setFixedHeight(70)
        
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(20, 10, 20, 10)
        
        self.open_location_btn = QPushButton("Open Location")
        self.open_location_btn.setCursor(Qt.PointingHandCursor)
        self.open_location_btn.setFixedHeight(40)
        self.open_location_btn.clicked.connect(self.open_file_location)
        
        self.save_as_btn = QPushButton("Save as PDF")
        self.save_as_btn.setCursor(Qt.PointingHandCursor)
        self.save_as_btn.setFixedHeight(40)
        self.save_as_btn.clicked.connect(self.save_as)
        
        # Apply styles (Simplified for brevity)
        btn_style = f"background-color: {LIGHT_BLUE}; color: {PRIMARY_BLUE}; border: 1px solid {PRIMARY_BLUE}; border-radius: 6px; font-weight: bold; padding: 0 15px;"
        save_style = f"background-color: {PRIMARY_GREEN}; color: white; border: none; border-radius: 6px; font-weight: bold; padding: 0 15px;"
        
        self.open_location_btn.setStyleSheet(btn_style)
        self.save_as_btn.setStyleSheet(save_style)

        action_layout.addStretch()
        action_layout.addWidget(self.open_location_btn)
        action_layout.addWidget(self.save_as_btn)
        
        main_layout.addWidget(action_bar)
        self.set_controls_enabled(False)
        
    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl++"), self, lambda: self.change_zoom(0.1))
        QShortcut(QKeySequence("Ctrl+-"), self, lambda: self.change_zoom(-0.1))
        QShortcut(QKeySequence("Ctrl+0"), self, lambda: self.set_zoom(1.0))
        QShortcut(QKeySequence("Escape"), self, self.close)

    def set_controls_enabled(self, enabled):
        for widget in [self.zoom_out_btn, self.zoom_in_btn, self.zoom_slider,
                       self.fit_width_btn, self.prev_page_btn, self.next_page_btn,
                       self.page_spin, self.save_as_btn, self.open_location_btn]:
            widget.setEnabled(enabled)

    def show_loading(self, show=True):
        self.loading_widget.setVisible(show)
        if show:
            self.loading_widget.setGeometry(self.scroll_area.geometry())

    def start_preview_generation(self):
        self.show_loading(True)
        self.progress_bar.setValue(0)
        
        self.worker = PDFGeneratorWorker(self.session_manager, self.generate_report_func)
        self.worker.finished.connect(self.on_preview_generated)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_progress_update(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        
    def on_generation_error(self, error_msg):
        self.show_loading(False)
        QMessageBox.critical(self, "Error", f"Failed to generate preview:\n{error_msg}")
        self.close()

    def on_preview_generated(self, page_images, pdf_data):
        """Handle successful preview generation"""
        self.page_images = page_images
        self.pdf_data = pdf_data
        self.pdf_path = None
        self.page_widgets = []

        # Clear existing layout
        while self.pages_layout.count():
            child = self.pages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create a Label for EACH page
        for i in range(len(page_images)):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background-color: transparent;")
            # Add a small margin to label to render shadow correctly
            lbl.setContentsMargins(0,0,0,0) 
            self.pages_layout.addWidget(lbl)
            self.page_widgets.append(lbl)
        
        # Update controls
        total_pages = len(page_images)
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(1)
        self.total_pages_label.setText(f"/ {total_pages}")
        
        self.update_preview()
        self.set_controls_enabled(True)
        self.show_loading(False)

    def update_preview(self):
        """Render all pages with current zoom level"""
        if not self.page_images: return
        
        for i, pixmap in enumerate(self.page_images):
            # Scale
            scaled_width = int(pixmap.width() * self.zoom_level)
            scaled_height = int(pixmap.height() * self.zoom_level)
            
            scaled_pixmap = pixmap.scaled(
                scaled_width, scaled_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # Draw Shadow
            shadow_pixmap = QPixmap(scaled_pixmap.width() + 20, scaled_pixmap.height() + 20)
            shadow_pixmap.fill(Qt.transparent)
            
            painter = QPainter(shadow_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(10, 10, scaled_pixmap.width(), scaled_pixmap.height(), QColor(0, 0, 0, 50))
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()
            
            # Update the specific widget in the stack
            if i < len(self.page_widgets):
                self.page_widgets[i].setPixmap(shadow_pixmap)

    def check_current_page_from_scroll(self):
        """Calculate which page is currently centered in view"""
        if not self.page_widgets: return
        
        scroll_val = self.scroll_area.verticalScrollBar().value()
        viewport_h = self.scroll_area.viewport().height()
        center_y = scroll_val + (viewport_h / 2)
        
        # Find widget that covers the center point (relative to container)
        # Note: In a QVBoxLayout, we can estimate by position
        
        closest_page = 0
        min_dist = float('inf')
        
        for i, widget in enumerate(self.page_widgets):
            # Widget y position relative to the container
            wy = widget.y()
            wh = widget.height()
            
            # Center of the widget
            widget_center = wy + (wh / 2)
            
            dist = abs(center_y - widget_center)
            if dist < min_dist:
                min_dist = dist
                closest_page = i
                
        # Update spinner without triggering the scroll-to signal
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(closest_page + 1)
        self.page_spin.blockSignals(False)

    def change_zoom(self, delta):
        new_zoom = self.zoom_level + delta
        self.set_zoom(max(0.25, min(3.0, new_zoom)))

    def set_zoom(self, level):
        self.zoom_level = level
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(level * 100))
        self.zoom_slider.blockSignals(False)
        self.zoom_percent_label.setText(f"{int(level * 100)}%")
        self.update_preview()

    def on_zoom_slider_changed(self, value):
        self.zoom_level = value / 100.0
        self.zoom_percent_label.setText(f"{value}%")
        self.update_preview()

    def fit_to_width(self):
        if not self.page_images: return
        pixmap = self.page_images[0] # Base on first page
        # Subtract margin and scrollbar width
        available_width = self.scroll_area.viewport().width() - 80 
        
        if pixmap.width() > 0:
            new_zoom = available_width / pixmap.width()
            self.set_zoom(max(0.25, min(3.0, new_zoom)))

    def prev_page(self):
        val = self.page_spin.value()
        if val > 1:
            self.go_to_page(val - 2) # 0-indexed

    def next_page(self):
        val = self.page_spin.value()
        if val < len(self.page_images):
            self.go_to_page(val) # 0-indexed is val (next one)

    def on_page_changed(self, value):
        self.go_to_page(value - 1)

    def go_to_page(self, page_index):
        """Scroll to the specific page widget"""
        if 0 <= page_index < len(self.page_widgets):
            widget = self.page_widgets[page_index]
            # Ensure the widget is visible
            self.scroll_area.ensureWidgetVisible(widget, 0, 0)
            
            # Sync spinner if called programmatically (e.g. via prev/next buttons)
            self.page_spin.blockSignals(True)
            self.page_spin.setValue(page_index + 1)
            self.page_spin.blockSignals(False)

    # ... [save_as, open_file_location, resizeEvent, closeEvent, showEvent SAME AS BEFORE] ...
    def save_as(self):
        if not hasattr(self, 'pdf_data') or not self.pdf_data:
            QMessageBox.warning(self, "Warning", "No PDF data available.")
            return
        
        cfg = SystemConfig()
        default_folder = cfg.PDF_OUTPUT_FOLDER
        os.makedirs(default_folder, exist_ok=True)
        
        session_id = self.session_manager.session_id if self.session_manager else "report"
        default_name = f"report_{session_id}.pdf"
        default_path = os.path.join(default_folder, default_name)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", default_path, "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                if self.save_func:
                    self.save_func(self.pdf_data, file_path)
                else:
                    with open(file_path, 'wb') as f:
                        f.write(self.pdf_data)
                self.pdf_path = file_path
                QMessageBox.information(self, "Success", f"PDF saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{str(e)}")

    def open_file_location(self):
        if not self.cfg.PDF_OUTPUT_FOLDER or not os.path.exists(self.cfg.PDF_OUTPUT_FOLDER):
            QMessageBox.warning(self, "Warning", "No PDF file available.")
            return
        folder_path = os.path.dirname(self.cfg.PDF_OUTPUT_FOLDER)
        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'explorer /select,"{self.cfg.PDF_OUTPUT_FOLDER}"')
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '-R', self.cfg.PDF_OUTPUT_FOLDER])
            else:
                subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not open location:\n{str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'loading_widget'):
            self.loading_widget.setGeometry(self.scroll_area.geometry())
            
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1000)
        event.accept()
        
    def showEvent(self, event):
        super().showEvent(event)
        if self.session_manager and self.generate_report_func:
            self.start_preview_generation()
