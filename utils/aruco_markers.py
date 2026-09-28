import os
import cv2
import tempfile
from PyQt5.QtWidgets import QMessageBox

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

DOT_THICKNESS = 5
DOT_GAP = 12
PAD_PX = 50


def draw_dotted_rect(img, thickness=DOT_THICKNESS, gap=DOT_GAP):
    h, w = img.shape[:2]
    color = 0

    # Top & Bottom
    for x in range(0, w, gap * 2):
        cv2.line(img, (x, 0), (min(x + gap, w - 1), 0), color, thickness)
        cv2.line(img, (x, h - 1), (min(x + gap, w - 1), h - 1), color, thickness)

    # Left & Right
    for y in range(0, h, gap * 2):
        cv2.line(img, (0, y), (0, min(y + gap, h - 1)), color, thickness)
        cv2.line(img, (w - 1, y), (w - 1, min(y + gap, h - 1)), color, thickness)


def generate_aruco_markers(self):
    """Generate ArUco markers as PDF files."""
    output_dir = self.config.GENERATED_MARKERS_FOLDER
    size_mm = self.config.ARUCO_SIZE_MM

    if not output_dir:
        QMessageBox.warning(self, "Missing Folder", "Output folder is not set in configuration.")
        return

    try:
        os.makedirs(output_dir, exist_ok=True)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        
        size_px = int(size_mm * (300 / 25.4))
        marker_physical_size_mm = size_mm + (2 * PAD_PX * 25.4 / 300)
        draw_size = marker_physical_size_mm * mm
        
        page_w, page_h = A4
        x = (page_w - draw_size) / 2
        y = (page_h - draw_size) / 2
        
        ids_to_gen = [0, 1, 2, 3]
        
        for marker_id in ids_to_gen:
            # Generate marker with padding and border
            img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)
            marker_padded = cv2.copyMakeBorder(
                img, PAD_PX, PAD_PX, PAD_PX, PAD_PX,
                cv2.BORDER_CONSTANT, value=255
            )
            draw_dotted_rect(marker_padded)
            
            # Save to temporary PNG for PDF generation
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                png_path = tmp.name
                cv2.imwrite(png_path, marker_padded)
            
            try:
                # Generate PDF
                pdf_path = os.path.join(output_dir, f"marker_id_{marker_id}.pdf")
                c = canvas.Canvas(pdf_path, pagesize=A4)
                
                img_reader = ImageReader(png_path)
                c.drawImage(
                    img_reader, x, y,
                    width=draw_size, height=draw_size,
                    preserveAspectRatio=True, mask='auto'
                )
                
                c.showPage()
                c.save()
            finally:
                # Clean up temporary PNG file
                os.remove(png_path)

        QMessageBox.information(
            self, "Success",
            f"Generated {len(ids_to_gen)} marker PDFs (IDs 0-3) in:\n{output_dir}"
        )

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to generate markers: {str(e)}")