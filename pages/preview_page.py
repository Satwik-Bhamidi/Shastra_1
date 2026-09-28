import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QSizePolicy, QMessageBox, QSplitter
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

from styles.theme import *
from backend.config import SystemConfig
from backend.session_manager import SessionManager

# Refactored Components
from components.ui_shared import LoadingOverlay, InteractiveLabel
from components.preview_controls import PreviewControlPanel
from components.pdf_preview_dialog import PDFPreviewDialog
from components.muzzle_velocity_dialog import MuzzleVelocityEntryPanel
from utils.workers import SessionWorker, ReportWorker
from utils.report_generator import generate_session_report

class PreviewPage(QWidget):
    processing_complete = pyqtSignal()
    processing_error = pyqtSignal(str)

    def __init__(self, parent=None, session_manager=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.scale_factor = 0.8
        self.worker = None
        self.original_pixmap = None
        self.cfg = SystemConfig()
        self.muzzle_velocity_panel = None
        self.muzzle_velocity_panel_visible = False
        
        self.setup_ui()
        
        self.processing_complete.connect(self._on_processing_complete)
        self.processing_error.connect(self._on_processing_error)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Top Bar ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 10, 20, 10)
        self.back_btn = QPushButton("← Back")
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setFixedSize(100, 38)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {PRIMARY_BLUE};
                border: 1px solid {PRIMARY_BLUE};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {LIGHT_BLUE}; }}
        """)
        self.back_btn.clicked.connect(self.go_back)
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # --- Main Content ---
        main_content = QWidget()
        main_content.setStyleSheet(f"background: {BACKGROUND};")
        
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {PRIMARY_BLUE}; width: 3px; }}")

        # Left Side: Image Display
        self.image_label = InteractiveLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)
        self.image_label.clicked.connect(self.handle_interaction)
        
        image_scroll_area = QScrollArea()
        image_scroll_area.setWidgetResizable(False)
        image_scroll_area.setAlignment(Qt.AlignCenter)
        image_scroll_area.setWidget(self.image_label)
        image_scroll_area.setStyleSheet(f"""
            QScrollArea {{ 
                border: none; 
                background: #f5f7fa; 
                border-radius: 8px;
            }}
            
            /* Vertical Scrollbar */
            QScrollBar:vertical {{
                background: transparent;
                width: 18px;
                margin: 4px 2px 4px 2px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_BLUE}, stop:1 #64B5F6);
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0, stop:1 {PRIMARY_BLUE});
            }}
            QScrollBar::handle:vertical:pressed {{
                background: #0D47A1;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: rgba(200, 200, 200, 0.3);
                border-radius: 5px;
                margin: 2px;
            }}
            
            /* Horizontal Scrollbar */
            QScrollBar:horizontal {{
                background: transparent;
                height: 18px;
                margin: 2px 4px 2px 4px;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PRIMARY_BLUE}, stop:1 #64B5F6);
                min-width: 30px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1565C0, stop:1 {PRIMARY_BLUE});
            }}
            QScrollBar::handle:horizontal:pressed {{
                background: #0D47A1;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
                background: none;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: rgba(200, 200, 200, 0.3);
                border-radius: 5px;
                margin: 2px;
            }}
            
            /* Corner widget where scrollbars meet */
            QScrollArea > QWidget > QWidget {{
                background: #f5f7fa;
            }}
        """)

        self.splitter.addWidget(image_scroll_area)

        # Right Side: Control Panel
        self.controls = PreviewControlPanel()
        self.controls.zoom_requested.connect(self.zoom_image)
        self.controls.print_preview_requested.connect(self.open_print_preview)
        self.controls.enter_muzzle_velocity_requested.connect(self.open_muzzle_velocity_panel)
        self.splitter.addWidget(self.controls)
        
        # Muzzle Velocity Panel (initially hidden)
        shot_count = 0
        if self.session_manager and self.session_manager.get_shot_list():
            shot_count = len(self.session_manager.get_shot_list())
        self.muzzle_velocity_panel = MuzzleVelocityEntryPanel(parent=self, shot_count=shot_count)
        self.muzzle_velocity_panel.shot_highlighted.connect(self.highlight_shot)
        self.muzzle_velocity_panel.velocities_complete.connect(self._on_velocities_entered)
        self.muzzle_velocity_panel.panel_closed.connect(self._on_panel_closed)
        self.muzzle_velocity_panel.hide()
        self.splitter.addWidget(self.muzzle_velocity_panel)
        
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setCollapsible(2, False)
        self.splitter.setSizes([int(self.width() * 0.7), int(self.width() * 0.3)])

        content_layout = QHBoxLayout(main_content)
        content_layout.setContentsMargins(20, 0, 20, 20)
        content_layout.addWidget(self.splitter)
        main_layout.addWidget(main_content)

        self.loading_overlay = LoadingOverlay(self)

    def start_processing(self, before_path, after_path):
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.set_message("Analyzing images", "Detecting shot impacts...")
        self.loading_overlay.start_animation()
        
        self.worker = SessionWorker(self.session_manager, before_path, after_path)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error.connect(self._on_worker_error)
        self.worker.start()
    
    def _on_worker_finished(self):
        self.loading_overlay.stop_animation()
        self.processing_complete.emit()
    
    def _on_worker_error(self, error_msg):
        self.loading_overlay.stop_animation()
        self.processing_error.emit(error_msg)
    
    def _on_processing_complete(self):
        self.update_display(reset_zoom=True)
    
    def _on_processing_error(self, error_msg):
        self.go_back()
        QMessageBox.critical(self, "Processing Error", f"Analysis Failed:\n{error_msg}")

    def open_muzzle_velocity_panel(self):
        """Open side-by-side panel for entering muzzle velocities"""
        if not self.session_manager or self.session_manager.shot_warp is None:
            QMessageBox.warning(self, "Warning", "No analysis results available.")
            return
        
        shot_count = len(self.session_manager.get_shot_list())
        if shot_count == 0:
            QMessageBox.warning(self, "Warning", "No shots detected. Please add shots first.")
            return
        
        # Reinitialize panel if shot count changed
        if self.muzzle_velocity_panel.shot_count != shot_count:
            self.muzzle_velocity_panel.hide()
            self.muzzle_velocity_panel.deleteLater()
            self.muzzle_velocity_panel = MuzzleVelocityEntryPanel(parent=self, shot_count=shot_count)
            self.muzzle_velocity_panel.shot_highlighted.connect(self.highlight_shot)
            self.muzzle_velocity_panel.velocities_complete.connect(self._on_velocities_entered)
            self.muzzle_velocity_panel.panel_closed.connect(self._on_panel_closed)
            self.splitter.addWidget(self.muzzle_velocity_panel)

            # collapse fix
            self.splitter.setCollapsible(self.splitter.indexOf(self.muzzle_velocity_panel), False)
        
        # Show the panel and start velocity entry
        self.muzzle_velocity_panel_visible = True
        self.muzzle_velocity_panel.show()
        self.muzzle_velocity_panel.start()
    
    def highlight_shot(self, shot_index):
        """Highlight a specific shot on the image"""
        if not self.session_manager or self.original_pixmap is None:
            return
        
        display_img = self.session_manager.get_display_image().copy()
        height, width, _ = display_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(display_img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap_to_draw = QPixmap.fromImage(q_img)
        
        painter = QPainter(pixmap_to_draw)
        shots = self.session_manager.get_shot_list()
        
        for i, s in enumerate(shots):
            cx, cy = int(s['x_px']), int(s['y_px'])
            
            if i == shot_index:
                # Highlight current shot with yellow circle
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(255, 255, 0), 5))  # Thick yellow border
                painter.drawEllipse(QPoint(cx, cy), 15, 15)
            else:
                # Draw other shots normally
                color = QColor(255, 125, 0) if s['manual'] else QColor(255, 0, 0)
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(color, 3))
                painter.drawEllipse(QPoint(cx, cy), 8, 8)
        
        painter.end()
        
        scaled_pixmap = pixmap_to_draw.scaled(
            int(self.original_pixmap.width() * self.scale_factor),
            int(self.original_pixmap.height() * self.scale_factor),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.update()
    
    def _on_velocities_entered(self, velocities):
        """Handle the completion of muzzle velocity entry"""
        self.session_manager.set_muzzle_velocities(velocities)
        
        # Update display with the new velocities
        self.update_display()
        
        QMessageBox.information(
            self,
            "Success",
            f"Muzzle velocities entered successfully!\n"
            f"Average: {self.session_manager.get_avg_muzzle_velocity():.2f} m/s"
        )
    
    def _on_panel_closed(self):
        """Handle muzzle velocity panel being closed"""
        self.muzzle_velocity_panel_visible = False

    def update_display(self, reset_zoom=False):
        if not self.session_manager or self.session_manager.shot_warp is None:
            return

        if reset_zoom or self.original_pixmap is None:
            display_img = self.session_manager.get_display_image().copy()
            height, width, _ = display_img.shape
            bytes_per_line = 3 * width
            q_img = QImage(display_img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.original_pixmap = QPixmap.fromImage(q_img)
            self.scale_factor = 0.8

        pixmap_to_draw = self.original_pixmap.copy()
        painter = QPainter(pixmap_to_draw)
        shots = self.session_manager.get_shot_list()
        
        for s in shots:
            cx, cy = int(s['x_px']), int(s['y_px'])
            color = QColor(255, 125, 0) if s['manual'] else QColor(255, 0, 0)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(color, 3))
            painter.drawEllipse(QPoint(cx, cy), 8, 8)
        painter.end()
        
        scaled_pixmap = pixmap_to_draw.scaled(
            int(self.original_pixmap.width() * self.scale_factor),
            int(self.original_pixmap.height() * self.scale_factor),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.adjustSize()
        self.image_label.update()
        self.image_label.repaint()
        
        if self.session_manager.latest_stats:
            avg_muzzle_velocity = self.session_manager.get_avg_muzzle_velocity()
            self.controls.update_stats(self.session_manager.latest_stats, self.cfg, avg_muzzle_velocity)
        else:
            self.controls.set_status_processing()

    def handle_interaction(self, x, y, is_left_click):
        if self.scale_factor == 0 or self.image_label.pixmap() is None:
            return
        
        pixmap = self.image_label.pixmap()
        offset_x = max(0, (self.image_label.width() - pixmap.width()) // 2)
        offset_y = max(0, (self.image_label.height() - pixmap.height()) // 2)
        pixmap_x = x - offset_x
        pixmap_y = y - offset_y
        
        if 0 <= pixmap_x < pixmap.width() and 0 <= pixmap_y < pixmap.height():
            orig_x = pixmap_x / self.scale_factor
            orig_y = pixmap_y / self.scale_factor
            
            if is_left_click:
                self.session_manager.add_manual_shot(orig_x, orig_y)
            else:
                self._delete_shot_at(orig_x, orig_y)
            
            self.update_display()

    def _delete_shot_at(self, x, y):
        CLICK_RADIUS = 15.0
        closest_id = None
        min_dist = float('inf')
        
        for s in self.session_manager.get_shot_list():
            dist = ((s['x_px'] - x)**2 + (s['y_px'] - y)**2)**0.5
            if dist < CLICK_RADIUS and dist < min_dist:
                min_dist = dist
                closest_id = s['id']
        
        if closest_id is not None:
            self.session_manager.delete_shot(closest_id)

    def zoom_image(self, factor):
        self.scale_factor *= factor
        self.scale_factor = max(0.1, min(self.scale_factor, 5.0)) 
        self.update_display()
    
    def _on_report_finished(self, output_path):
        """Handle successful report generation"""
        self.loading_overlay.stop_animation()
        if output_path:
            QMessageBox.information(self, "Success", f"Report generated successfully:\n{output_path}")
        else:
            QMessageBox.warning(self, "Warning", "Report generation cancelled or failed.")
    
    def _on_report_error(self, error_msg):
        """Handle report generation error"""
        self.loading_overlay.stop_animation()
        QMessageBox.critical(self, "Error", f"Failed to generate report:\n{error_msg}")

    def open_print_preview(self):
        """Open PDF preview dialog with print and export options"""
        if not self.session_manager or not self.session_manager.latest_stats:
            QMessageBox.warning(self, "Warning", "No analysis results available. Please process images first.")
            return
        
        # Create and show the PDF preview dialog
        dialog = PDFPreviewDialog(
            parent=self,
            session_manager=self.session_manager,
            generate_report_func=generate_session_report
        )
        dialog.exec_()

    def go_back(self):
        if self.parent():
            main_window = self.parent().parent()
            if hasattr(main_window, 'stack') and hasattr(main_window, 'main_page'):
                main_window.stack.setCurrentWidget(main_window.main_page)

    def resizeEvent(self, event):
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.rect())
        super().resizeEvent(event)