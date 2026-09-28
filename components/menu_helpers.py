"""
Menu helper functions for SHASTRA Proof Yard application.
Contains implementations for all menu bar actions.
"""

import os
import csv
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QGroupBox, QFormLayout,
    QListWidget, QListWidgetItem, QDialogButtonBox, QCheckBox,
    QComboBox, QProgressDialog, QApplication
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import cv2
import numpy as np

from backend.config import SystemConfig
from utils.resource_path import resource_path


#  FILE MENU HELPERS 

class RecentFilesManager:
    """Manages recent files list in settings"""
    MAX_RECENT = 10
    
    def __init__(self):
        self.settings = QSettings("Shastra_Proof_Yard", "recent_files")
    
    def get_recent_files(self):
        """Get list of recent file pairs"""
        files = self.settings.value("recent_files", [])
        if files is None:
            return []
        return files[:self.MAX_RECENT]
    
    def add_recent_file(self, before_path, after_path):
        """Add a file pair to recent files"""
        recent = self.get_recent_files()
        entry = f"{before_path}|{after_path}"
        
        # Remove if already exists
        recent = [r for r in recent if r != entry]
        
        # Add to front
        recent.insert(0, entry)
        
        # Trim to max
        recent = recent[:self.MAX_RECENT]
        
        self.settings.setValue("recent_files", recent)
    
    def clear_recent(self):
        """Clear recent files list"""
        self.settings.setValue("recent_files", [])


def export_to_csv(main_window):
    """Export shot data to CSV file"""
    if not hasattr(main_window, 'session_manager') or main_window.session_manager.shot_warp is None:
        QMessageBox.warning(
            main_window,
            "No Data",
            "No analysis data available to export.\nPlease run an analysis first.",
            QMessageBox.Ok
        )
        return
    
    sm = main_window.session_manager
    shots = sm.get_shot_list()
    stats = sm.latest_stats
    
    if not shots:
        QMessageBox.warning(main_window, "No Data", "No shot data to export.")
        return
    
    # Get save path
    config = SystemConfig()
    default_name = f"shot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path, _ = QFileDialog.getSaveFileName(
        main_window,
        "Export to CSV",
        str(Path(config.IMG_DB_FOLDER) / default_name),
        "CSV Files (*.csv);;All Files (*)"
    )
    
    if not file_path:
        return
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header info
            writer.writerow(["SHASTRA Proof Yard - Shot Data Export"])
            writer.writerow([f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
            writer.writerow([])
            
            # Form data if available
            form_data = getattr(sm, 'form_data', {})
            if form_data:
                writer.writerow(["Session Information"])
                for key, value in form_data.items():
                    writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])
            
            # Statistics
            if stats:
                writer.writerow(["Statistics"])
                writer.writerow(["Shot Count", stats.shot_count])
                writer.writerow(["MPI X (mm)", f"{stats.mean_point_of_impact_mm[0]:.2f}"])
                writer.writerow(["MPI Y (mm)", f"{stats.mean_point_of_impact_mm[1]:.2f}"])
                writer.writerow(["Mean Radius Deviation (mm)", f"{stats.mean_radius_deviation_mm:.2f}"])
                writer.writerow(["Max Horizontal Spread (mm)", f"{stats.max_horizontal_spread_mm:.2f}"])
                writer.writerow(["Max Vertical Spread (mm)", f"{stats.max_vertical_spread_mm:.2f}"])
                writer.writerow(["Result", "PASS" if stats.passed else "FAIL"])
                writer.writerow([])
            
            # Shot details
            writer.writerow(["Shot Details"])
            writer.writerow(["Shot ID", "X (px)", "Y (px)", "X (mm)", "Y (mm)", "Manual", "Area"])
            
            for shot in shots:
                writer.writerow([
                    shot['id'],
                    f"{shot['x_px']:.2f}",
                    f"{shot['y_px']:.2f}",
                    f"{shot['x_mm']:.2f}",
                    f"{shot['y_mm']:.2f}",
                    "Yes" if shot['manual'] else "No",
                    f"{shot['area']:.2f}" if shot['area'] >= 0 else "N/A"
                ])
        
        QMessageBox.information(
            main_window,
            "Export Successful",
            f"Data exported successfully to:\n{file_path}"
        )
        
    except Exception as e:
        QMessageBox.critical(main_window, "Export Error", f"Failed to export data:\n{str(e)}")


def print_report(main_window):
    """Print the full report with all data like PDF"""
    if not hasattr(main_window, 'session_manager') or main_window.session_manager.shot_warp is None:
        QMessageBox.warning(
            main_window,
            "No Data",
            "No analysis data available to print.\nPlease run an analysis first.",
            QMessageBox.Ok
        )
        return
    
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPrinter.A4)
    dialog = QPrintDialog(printer, main_window)
    
    if dialog.exec_() == QDialog.Accepted:
        from PyQt5.QtGui import QPainter, QFont, QColor, QPen
        from PyQt5.QtCore import QRectF
        
        sm = main_window.session_manager
        stats = sm.latest_stats
        shots = sm.get_shot_list()
        form_data = getattr(sm, 'form_data', {}) or {}
        
        painter = QPainter(printer)
        page_rect = printer.pageRect()
        
        # Margins
        margin = 50
        y_pos = margin
        content_width = page_rect.width() - 2 * margin
        
        # --- Header ---
        painter.setFont(QFont("Helvetica", 18, QFont.Bold))
        painter.drawText(QRectF(margin, y_pos, content_width, 40), Qt.AlignCenter, "SHASTRA PROOF YARD")
        y_pos += 35
        
        painter.setFont(QFont("Helvetica", 12))
        painter.drawText(QRectF(margin, y_pos, content_width, 25), Qt.AlignCenter, "Proof Test Results")
        y_pos += 45
        
        # --- Metadata Table ---
        painter.setFont(QFont("Helvetica", 10))
        metadata = [
            ("Date and Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("AMK No", form_data.get("amk_no", "N/A") or "N/A"),
            ("Nomenclature", form_data.get("name", "Session Analysis") or "Session Analysis"),
            ("Lot No", form_data.get("lot_no", "N/A") or "N/A"),
            ("Weapon Used", form_data.get("weapon_used", "N/A") or "N/A"),
            ("Sample Size", form_data.get("sample_size", str(len(shots))) or str(len(shots))),
            ("Temperature", form_data.get("temperature", "N/A") or "N/A"),
        ]
        
        row_height = 25
        col1_width = content_width * 0.35
        col2_width = content_width * 0.65
        
        for label, value in metadata:
            # Draw cell borders
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawRect(QRectF(margin, y_pos, col1_width, row_height))
            painter.drawRect(QRectF(margin + col1_width, y_pos, col2_width, row_height))
            
            # Fill label cell with light gray
            painter.fillRect(QRectF(margin + 1, y_pos + 1, col1_width - 2, row_height - 2), QColor(230, 230, 230))
            
            # Draw text
            painter.setFont(QFont("Helvetica", 9, QFont.Bold))
            painter.drawText(QRectF(margin + 5, y_pos, col1_width - 10, row_height), Qt.AlignVCenter, label)
            painter.setFont(QFont("Helvetica", 9))
            painter.drawText(QRectF(margin + col1_width + 5, y_pos, col2_width - 10, row_height), Qt.AlignVCenter, str(value))
            y_pos += row_height
        
        y_pos += 20
        
        # --- Target Image ---
        img = sm.get_display_image_annotated()
        if img is not None:
            height, width, channel = img.shape
            bytes_per_line = 3 * width
            q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            
            img_width = content_width * 0.7
            img_height = img_width * (height / width)
            x_img = margin + (content_width - img_width) / 2
            
            painter.drawPixmap(QRectF(x_img, y_pos, img_width, img_height).toRect(), pixmap)
            y_pos += img_height + 20
        
        # --- Results Summary ---
        if stats:
            painter.setFont(QFont("Helvetica", 11, QFont.Bold))
            mpi_text = f"MPI = ({stats.mean_point_of_impact_mm[0]:.2f}, {stats.mean_point_of_impact_mm[1]:.2f})"
            dev_text = f"Mean Deviation = {stats.mean_radius_deviation_mm:.2f} mm"
            painter.drawText(QRectF(margin, y_pos, content_width * 0.5, 25), Qt.AlignLeft, mpi_text)
            painter.drawText(QRectF(margin + content_width * 0.35, y_pos, content_width * 0.35, 25), Qt.AlignLeft, dev_text)
            
            # Pass/Fail status
            if stats.passed:
                painter.setPen(QColor(0, 128, 0))
                status_text = "PASS"
            else:
                painter.setPen(QColor(200, 0, 0))
                status_text = "FAIL"
            painter.drawText(QRectF(margin + content_width * 0.75, y_pos, content_width * 0.25, 25), Qt.AlignLeft, status_text)
            painter.setPen(QColor(0, 0, 0))
            y_pos += 35
        
        # --- Rounds Table ---
        painter.setFont(QFont("Helvetica", 10, QFont.Bold))
        painter.drawText(QRectF(margin, y_pos, content_width, 20), Qt.AlignLeft, "Shot Details:")
        y_pos += 25
        
        # Table header
        headers = ["Round", "Distance from MPI (mm)", "Avg. Muzzle Velocity (m/s)"]
        col_widths = [content_width * 0.2, content_width * 0.4, content_width * 0.4]
        
        x_pos = margin
        for i, header in enumerate(headers):
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawRect(QRectF(x_pos, y_pos, col_widths[i], row_height))
            painter.fillRect(QRectF(x_pos + 1, y_pos + 1, col_widths[i] - 2, row_height - 2), QColor(230, 230, 230))
            painter.setFont(QFont("Helvetica", 9, QFont.Bold))
            painter.drawText(QRectF(x_pos + 5, y_pos, col_widths[i] - 10, row_height), Qt.AlignVCenter | Qt.AlignCenter, header)
            x_pos += col_widths[i]
        y_pos += row_height
        
        # Table rows
        muzzle_velocity = form_data.get("muzzle_velocity", "N/A") or "N/A"
        if stats:
            mpi = np.array(stats.mean_point_of_impact_mm)
            for i, shot in enumerate(shots):
                p = np.array([shot['x_mm'], shot['y_mm']])
                dist = np.linalg.norm(p - mpi)
                
                row_data = [str(i + 1), f"{dist:.2f}", str(muzzle_velocity)]
                x_pos = margin
                painter.setFont(QFont("Helvetica", 9))
                for j, cell in enumerate(row_data):
                    painter.drawRect(QRectF(x_pos, y_pos, col_widths[j], row_height))
                    painter.drawText(QRectF(x_pos + 5, y_pos, col_widths[j] - 10, row_height), Qt.AlignVCenter | Qt.AlignCenter, cell)
                    x_pos += col_widths[j]
                y_pos += row_height
        
        y_pos += 30
        
        # --- Approval Line ---
        painter.setFont(QFont("Helvetica", 10, QFont.Bold))
        painter.drawText(QRectF(page_rect.width() - margin - 150, y_pos, 150, 20), Qt.AlignRight, "Approved By: _____________")
        
        painter.end()
        QMessageBox.information(main_window, "Print", "Full report sent to printer.")


def open_reports_folder(main_window):
    """Open the reports folder in file explorer"""
    config = SystemConfig()
    folder = Path(config.IMG_DB_FOLDER)
    
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
    
    # Open folder in system file manager
    if platform.system() == "Windows":
        os.startfile(str(folder))
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", str(folder)])
    else:  # Linux
        subprocess.run(["xdg-open", str(folder)])


#  ANALYSIS MENU HELPERS 

def recalculate_stats(main_window):
    """Recalculate statistics for current session"""
    if not hasattr(main_window, 'session_manager') or main_window.session_manager.shot_warp is None:
        QMessageBox.warning(main_window, "No Data", "No analysis data available.")
        return
    
    main_window.session_manager.recalculate()
    
    if hasattr(main_window, 'preview_page'):
        main_window.preview_page.update_display()
    
    QMessageBox.information(main_window, "Recalculated", "Statistics have been recalculated.")


def clear_all_shots(main_window):
    """Clear all detected shots"""
    if not hasattr(main_window, 'session_manager') or main_window.session_manager.shot_warp is None:
        QMessageBox.warning(main_window, "No Data", "No analysis data available.")
        return
    
    reply = QMessageBox.question(
        main_window,
        "Clear All Shots",
        "Are you sure you want to remove all detected shots?\nThis cannot be undone.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        main_window.session_manager.shots = []
        main_window.session_manager.next_shot_id = 0
        main_window.session_manager.recalculate()
        
        if hasattr(main_window, 'preview_page'):
            main_window.preview_page.update_display()
        
        QMessageBox.information(main_window, "Cleared", "All shots have been removed.")


class SensitivityDialog(QDialog):
    """Dialog for adjusting detection sensitivity"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SystemConfig()
        self.setWindowTitle("Detection Sensitivity")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Diff Threshold
        threshold_group = QGroupBox("Difference Threshold")
        threshold_layout = QHBoxLayout(threshold_group)
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(10, 200)
        self.threshold_slider.setValue(self.config.DIFF_THRESHOLD)
        
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(10, 200)
        self.threshold_spin.setValue(self.config.DIFF_THRESHOLD)
        
        self.threshold_slider.valueChanged.connect(self.threshold_spin.setValue)
        self.threshold_spin.valueChanged.connect(self.threshold_slider.setValue)
        
        threshold_layout.addWidget(QLabel("Low"))
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(QLabel("High"))
        threshold_layout.addWidget(self.threshold_spin)
        
        layout.addWidget(threshold_group)
        
        # Min/Max Hole Area
        area_group = QGroupBox("Hole Area Range (pixels)")
        area_layout = QFormLayout(area_group)
        
        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(10, 1000)
        self.min_area_spin.setValue(self.config.MIN_HOLE_AREA_PX)
        
        self.max_area_spin = QSpinBox()
        self.max_area_spin.setRange(100, 100000)
        self.max_area_spin.setValue(self.config.MAX_HOLE_AREA_PX)
        
        area_layout.addRow("Minimum:", self.min_area_spin)
        area_layout.addRow("Maximum:", self.max_area_spin)
        
        layout.addWidget(area_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        self.config.DIFF_THRESHOLD = self.threshold_spin.value()
        self.config.MIN_HOLE_AREA_PX = self.min_area_spin.value()
        self.config.MAX_HOLE_AREA_PX = self.max_area_spin.value()
        self.config.save()
        super().accept()


def show_sensitivity_dialog(main_window):
    """Show detection sensitivity adjustment dialog"""
    dialog = SensitivityDialog(main_window)
    if dialog.exec_() == QDialog.Accepted:
        QMessageBox.information(
            main_window,
            "Settings Saved",
            "Detection sensitivity settings have been saved.\n"
            "Re-run analysis to apply changes."
        )


#  REPORTS MENU HELPERS 

class SessionHistoryDialog(QDialog):
    """Dialog to view and manage session history"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SystemConfig()
        self.setWindowTitle("Session History")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_sessions()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self.open_session_folder)
        layout.addWidget(self.session_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Folder")
        open_btn.clicked.connect(self.open_selected_folder)
        
        delete_btn = QPushButton("Delete Session")
        delete_btn.clicked.connect(self.delete_session)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_sessions)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_sessions(self):
        self.session_list.clear()
        folder = Path(self.config.IMG_DB_FOLDER)
        
        if not folder.exists():
            return
        
        sessions = sorted(folder.iterdir(), reverse=True)
        
        for session_dir in sessions:
            if session_dir.is_dir() and session_dir.name.startswith("Session_"):
                # Parse date from folder name
                try:
                    date_str = session_dir.name.replace("Session_", "")
                    date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    display_text = f"{date.strftime('%Y-%m-%d %H:%M:%S')} - {session_dir.name}"
                except:
                    display_text = session_dir.name
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, str(session_dir))
                self.session_list.addItem(item)
    
    def open_session_folder(self, item):
        folder = item.data(Qt.UserRole)
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])
    
    def open_selected_folder(self):
        item = self.session_list.currentItem()
        if item:
            self.open_session_folder(item)
    
    def delete_session(self):
        item = self.session_list.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Session",
            "Are you sure you want to delete this session?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import shutil
            folder = item.data(Qt.UserRole)
            try:
                shutil.rmtree(folder)
                self.load_sessions()
                QMessageBox.information(self, "Deleted", "Session deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete session:\n{str(e)}")


def show_session_history(main_window):
    """Show session history dialog"""
    dialog = SessionHistoryDialog(main_window)
    dialog.exec_()


#  TOOLS MENU HELPERS 

class ArucoGeneratorDialog(QDialog):
    """Dialog for generating ArUco markers"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SystemConfig()
        self.setWindowTitle("ArUco Marker Generator")
        self.setMinimumWidth(450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Marker settings
        settings_group = QGroupBox("Marker Settings")
        settings_layout = QFormLayout(settings_group)
        
        self.dict_combo = QComboBox()
        self.dict_combo.addItems([
            "DICT_4X4_50",
            "DICT_4X4_100",
            "DICT_4X4_250",
            "DICT_5X5_50",
            "DICT_5X5_100",
            "DICT_6X6_50",
            "DICT_6X6_100"
        ])
        self.dict_combo.setCurrentText("DICT_4X4_50")
        
        self.marker_id_spin = QSpinBox()
        self.marker_id_spin.setRange(0, 49)
        self.marker_id_spin.setValue(0)
        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(100, 2000)
        self.size_spin.setValue(500)
        self.size_spin.setSuffix(" px")
        
        self.generate_set = QCheckBox("Generate marker set (IDs 0-3)")
        self.generate_set.setChecked(True)
        
        settings_layout.addRow("Dictionary:", self.dict_combo)
        settings_layout.addRow("Marker ID:", self.marker_id_spin)
        settings_layout.addRow("Size:", self.size_spin)
        settings_layout.addRow("", self.generate_set)
        
        layout.addWidget(settings_group)
        
        # Preview
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self.preview_label)
        
        # Generate preview
        self.update_preview()
        self.marker_id_spin.valueChanged.connect(self.update_preview)
        self.dict_combo.currentTextChanged.connect(self.update_preview)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Generate && Save")
        generate_btn.clicked.connect(self.generate_markers)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        buttons_layout.addWidget(generate_btn)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)
    
    def get_aruco_dict(self):
        """Get the ArUco dictionary based on selection"""
        dict_map = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
            "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
        }
        return cv2.aruco.getPredefinedDictionary(dict_map[self.dict_combo.currentText()])
    
    def update_preview(self):
        """Update the marker preview"""
        try:
            aruco_dict = self.get_aruco_dict()
            marker_id = self.marker_id_spin.value()
            marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 150)
            
            h, w = marker_img.shape
            q_img = QImage(marker_img.data, w, h, w, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_img)
            self.preview_label.setPixmap(pixmap)
        except Exception as e:
            self.preview_label.setText(f"Preview error: {e}")
    
    def generate_markers(self):
        """Generate and save ArUco markers"""
        output_folder = Path(self.config.GENERATED_MARKERS_FOLDER)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        aruco_dict = self.get_aruco_dict()
        size = self.size_spin.value()
        
        try:
            if self.generate_set.isChecked():
                # Generate set of 4 markers
                for marker_id in range(4):
                    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size)
                    output_path = output_folder / f"aruco_marker_{marker_id}.png"
                    cv2.imwrite(str(output_path), marker_img)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Generated 4 markers (IDs 0-3) in:\n{output_folder}"
                )
            else:
                # Generate single marker
                marker_id = self.marker_id_spin.value()
                marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size)
                output_path = output_folder / f"aruco_marker_{marker_id}.png"
                cv2.imwrite(str(output_path), marker_img)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Marker saved to:\n{output_path}"
                )
            
            # Open folder
            if platform.system() == "Windows":
                os.startfile(str(output_folder))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(output_folder)])
            else:
                subprocess.run(["xdg-open", str(output_folder)])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate markers:\n{str(e)}")


def show_aruco_generator(main_window):
    """Show ArUco marker generator dialog"""
    dialog = ArucoGeneratorDialog(main_window)
    dialog.exec_()


class ImageEnhancementDialog(QDialog):
    """Dialog for image enhancement adjustments"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setWindowTitle("Image Enhancement")
        self.setMinimumWidth(400)
        self.original_image = None
        self.setup_ui()
        self.load_image()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Brightness
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QHBoxLayout(brightness_group)
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.apply_enhancement)
        
        self.brightness_label = QLabel("0")
        
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_label)
        layout.addWidget(brightness_group)
        
        # Contrast
        contrast_group = QGroupBox("Contrast")
        contrast_layout = QHBoxLayout(contrast_group)
        
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.apply_enhancement)
        
        self.contrast_label = QLabel("100%")
        
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        layout.addWidget(contrast_group)
        
        # Preview
        self.preview_label = QLabel("No image loaded")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        layout.addWidget(self.preview_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_sliders)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
    
    def load_image(self):
        """Load current session image"""
        if hasattr(self.main_window, 'session_manager') and self.main_window.session_manager.shot_warp is not None:
            self.original_image = self.main_window.session_manager.shot_warp.copy()
            self.apply_enhancement()
        else:
            self.preview_label.setText("No image loaded.\nRun analysis first.")
    
    def apply_enhancement(self):
        """Apply brightness/contrast adjustments"""
        if self.original_image is None:
            return
        
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value() / 100.0
        
        self.brightness_label.setText(str(brightness))
        self.contrast_label.setText(f"{int(contrast * 100)}%")
        
        # Apply adjustments
        enhanced = cv2.convertScaleAbs(self.original_image, alpha=contrast, beta=brightness)
        
        # Show preview
        h, w, c = enhanced.shape
        bytes_per_line = 3 * w
        
        # Scale down for preview
        max_preview = 280
        scale = min(max_preview / w, max_preview / h)
        new_w, new_h = int(w * scale), int(h * scale)
        preview_img = cv2.resize(enhanced, (new_w, new_h))
        
        h, w, c = preview_img.shape
        bytes_per_line = 3 * w
        q_img = QImage(preview_img.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.preview_label.setPixmap(QPixmap.fromImage(q_img))
        
        # Store enhanced image
        self.enhanced_image = enhanced
    
    def reset_sliders(self):
        """Reset to default values"""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)
    
    def accept(self):
        """Apply enhancement to session"""
        if hasattr(self, 'enhanced_image') and self.main_window.session_manager:
            self.main_window.session_manager.shot_warp = self.enhanced_image
            if hasattr(self.main_window, 'preview_page'):
                self.main_window.preview_page.update_display(reset_zoom=True)
        super().accept()


def show_image_enhancement(main_window):
    """Show image enhancement dialog"""
    if not hasattr(main_window, 'session_manager') or main_window.session_manager.shot_warp is None:
        QMessageBox.warning(main_window, "No Image", "No image loaded.\nPlease run an analysis first.")
        return
    
    dialog = ImageEnhancementDialog(main_window)
    dialog.exec_()


#  SETTINGS MENU HELPERS 

def toggle_theme(main_window, dark_mode):
    """Toggle between light and dark theme - applies globally to all pages"""
    settings = QSettings("Shastra_Proof_Yard", "appearance")
    settings.setValue("dark_mode", dark_mode)
    
    # Store the theme state on main window
    main_window.is_dark_mode = dark_mode
    
    if dark_mode:
        # Comprehensive dark theme stylesheet
        dark_stylesheet = """
            /* Main Window and base widgets */
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e8e8e8;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #16213e;
                border-bottom: 1px solid #0f3460;
                padding: 4px;
            }
            QMenuBar::item {
                color: #e8e8e8;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #0f3460;
                color: #4fc3f7;
            }
            
            /* Menus */
            QMenu {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                color: #e8e8e8;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0f3460;
                color: #4fc3f7;
            }
            QMenu::separator {
                height: 1px;
                background-color: #0f3460;
                margin: 6px 12px;
            }
            
            /* Scroll Areas */
            QScrollArea {
                background-color: #1a1a2e;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1a1a2e;
            }
            
            /* Cards */
            QWidget#card {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 14px;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #0f3460;
                color: #e8e8e8;
                border: 1px solid #1a4a7a;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a4a7a;
                border-color: #4fc3f7;
            }
            QPushButton:pressed {
                background-color: #0d2d4d;
            }
            QPushButton:disabled {
                background-color: #2a2a3e;
                color: #666;
                border-color: #333;
            }
            
            /* Primary action buttons */
            QPushButton[primary="true"], QPushButton#primary_btn {
                background-color: #4fc3f7;
                color: #1a1a2e;
                border: none;
            }
            QPushButton[primary="true"]:hover, QPushButton#primary_btn:hover {
                background-color: #81d4fa;
            }
            
            /* Input Fields */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background-color: #0f3460;
                color: #e8e8e8;
                border: 1px solid #1a4a7a;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #4fc3f7;
                selection-color: #1a1a2e;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #4fc3f7;
            }
            QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
                background-color: #2a2a3e;
                color: #666;
            }
            
            /* Combo Box dropdown */
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                color: #e8e8e8;
                border: 1px solid #0f3460;
                selection-background-color: #0f3460;
            }
            
            /* Labels */
            QLabel {
                color: #e8e8e8;
                background-color: transparent;
            }
            
            /* Group Boxes */
            QGroupBox {
                color: #4fc3f7;
                border: 1px solid #0f3460;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #4fc3f7;
            }
            
            /* Frames */
            QFrame {
                background-color: transparent;
            }
            QFrame[frameShape="4"], QFrame[frameShape="5"] {
                background-color: #0f3460;
            }
            
            /* Scroll Bars */
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 50px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #0f3460;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #1a4a7a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1a1a2e;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #0f3460;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #1a4a7a;
            }
            
            /* Tab Widgets */
            QTabWidget::pane {
                border: 1px solid #0f3460;
                background-color: #16213e;
            }
            QTabBar::tab {
                background-color: #0f3460;
                color: #e8e8e8;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #4fc3f7;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                background-color: #0f3460;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #4fc3f7;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #81d4fa;
            }
            
            /* Progress Bars */
            QProgressBar {
                background-color: #0f3460;
                border-radius: 4px;
                text-align: center;
                color: #e8e8e8;
            }
            QProgressBar::chunk {
                background-color: #4fc3f7;
                border-radius: 4px;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #1a1a2e;
            }
            
            /* Message Boxes */
            QMessageBox {
                background-color: #16213e;
            }
            QMessageBox QLabel {
                color: #e8e8e8;
            }
            
            /* List Widgets */
            QListWidget {
                background-color: #0f3460;
                color: #e8e8e8;
                border: 1px solid #1a4a7a;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #1a4a7a;
            }
            QListWidget::item:hover {
                background-color: #16213e;
            }
            
            /* Tool Tips */
            QToolTip {
                background-color: #16213e;
                color: #e8e8e8;
                border: 1px solid #0f3460;
                border-radius: 4px;
                padding: 4px;
            }
        """
        main_window.setStyleSheet(dark_stylesheet)
    else:
        # Reset to default light theme
        main_window.setStyleSheet("")
    
    # Update menu actions to reflect current state
    if hasattr(main_window, 'light_theme_action') and hasattr(main_window, 'dark_theme_action'):
        main_window.light_theme_action.setChecked(not dark_mode)
        main_window.dark_theme_action.setChecked(dark_mode)


def reset_all_settings(main_window):
    """Reset all settings to defaults"""
    reply = QMessageBox.question(
        main_window,
        "Reset Settings",
        "Are you sure you want to reset all settings to defaults?\n"
        "This includes detection parameters, paths, and preferences.",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        # Clear all QSettings
        QSettings("Shastra_Proof_Yard", "config_settings").clear()
        QSettings("Shastra_Proof_Yard", "recent_files").clear()
        QSettings("Shastra_Proof_Yard", "appearance").clear()
        
        QMessageBox.information(
            main_window,
            "Settings Reset",
            "All settings have been reset to defaults.\n"
            "Please restart the application for changes to take effect."
        )


#  KEYBOARD SHORTCUTS DIALOG 

class ShortcutsDialog(QDialog):
    """Dialog showing keyboard shortcuts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setMinimumSize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        shortcuts = [
            ("File", [
                ("Ctrl+N", "New Report"),
                ("Ctrl+O", "Open Images"),
                ("Ctrl+S", "Save Report"),
                ("Ctrl+E", "Export Report"),
                ("Ctrl+Shift+E", "Export to CSV"),
                ("Ctrl+P", "Print Report"),
                ("Ctrl+Q", "Exit"),
            ]),
            ("View", [
                ("Ctrl+1", "Main Form"),
                ("Ctrl+2", "Preview Page"),
                ("F11", "Full Screen"),
            ]),
            ("Analysis", [
                ("Ctrl+R", "Recalculate Stats"),
                ("Ctrl+Shift+C", "Clear All Shots"),
            ]),
            ("Tools", [
                ("Ctrl+M", "ArUco Generator"),
            ]),
            ("Settings", [
                ("Ctrl+,", "System Configuration"),
            ]),
            ("Help", [
                ("F1", "Documentation"),
            ]),
        ]
        
        for category, items in shortcuts:
            group = QGroupBox(category)
            group_layout = QFormLayout(group)
            
            for shortcut, description in items:
                shortcut_label = QLabel(f"<b>{shortcut}</b>")
                shortcut_label.setStyleSheet("color: #1976D2;")
                group_layout.addRow(shortcut_label, QLabel(description))
            
            layout.addWidget(group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


def show_shortcuts_dialog(main_window):
    """Show keyboard shortcuts dialog"""
    dialog = ShortcutsDialog(main_window)
    dialog.exec_()
