import os
import numpy as np
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from utils.resource_path import resource_path
from backend.config import SystemConfig
from utils.bullseye_visualizer import draw_bullseye_target, draw_shot_on_bullseye, draw_mpi_marker
import io

PAGE_WIDTH, PAGE_HEIGHT = A4

class DynamicPDFLayout:
    """Manages dynamic positioning of PDF elements"""
    
    def __init__(self):
        self.current_y = PAGE_HEIGHT - 15 * mm  # Start from top with margin
        self.left_margin = 15 * mm
        self.right_margin = PAGE_WIDTH - 15 * mm
        self.content_width = self.right_margin - self.left_margin
        self.cfg = SystemConfig()
        
    def move_down(self, amount_mm):
        """Move current position down by specified mm"""
        self.current_y -= amount_mm * mm
        
    def get_y(self):
        """Get current Y position"""
        return self.current_y
    
    def set_y(self, y):
        """Set current Y position"""
        self.current_y = y
        
    def check_page_break(self, c, needed_height_mm):
        """Check if we need a new page, and create one if so"""
        if self.current_y - (needed_height_mm * mm) < 20 * mm:
            c.showPage()
            self.current_y = PAGE_HEIGHT - 15 * mm
            return True
        return False


def draw_header(c, layout):
    """Draw header with logos and title"""
    # Logo dimensions and positions
    logo_height = 15 * mm
    logo_width = 15 * mm
    
    # Left logo
    left_logo_path = resource_path("assets/left.png")
    if os.path.exists(left_logo_path):
        try:
            c.drawImage(
                left_logo_path,
                layout.left_margin,
                layout.get_y() - logo_height,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )
        except Exception as e:
            print(f"Error drawing left logo: {e}")
    
    # Right logo
    right_logo_path = resource_path("assets/right.png")
    if os.path.exists(right_logo_path):
        try:
            c.drawImage(
                right_logo_path,
                layout.right_margin - logo_width,
                layout.get_y() - logo_height,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask="auto"
            )
        except Exception as e:
            print(f"Error drawing right logo: {e}")
    
    # Header text (centered between logos)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(PAGE_WIDTH / 2, layout.get_y() - 8 * mm, "SHASTRA PROOF YARD")

    c.setFont("Helvetica", 11)
    c.drawCentredString(PAGE_WIDTH / 2, layout.get_y() - 15 * mm, "Proof Test Results")
    
    layout.move_down(22)


def draw_metadata_table(c, layout, data):
    """Draw metadata table with dynamic positioning"""
    table_data = [
        ["Date and Time Conducted", data["date"]],
        ["AMK No", data["amk"]],
        ["Nomenclature", data["name"]],
        ["Lot No", data["lot"]],
        ["Weapon used for firing", data["weapon"]],
        ["Sample Size", data["sample"]],
        ["Range Temperature", data["temp"]],
    ]

    table = Table(table_data, colWidths=[60 * mm, 110 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    # Calculate table height
    table_width, table_height = table.wrap(PAGE_WIDTH, PAGE_HEIGHT)
    
    # Draw table
    table.drawOn(c, layout.left_margin, layout.get_y() - table_height)
    layout.set_y(layout.get_y() - table_height - 8 * mm)

def draw_result_summary(c, layout, result, max_mean_deviation_mm, avg_muzzle_velocity_threshold=None):
    """Draw result summary with MPI, deviation, pass/fail status, max mean deviation, and muzzle velocity"""
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    
    y_pos = layout.get_y()
    
    # MPI
    c.drawString(
        layout.left_margin,
        y_pos,
        f"MPI = ({round(result['mpi_x'] + layout.cfg.OFFSET_X, 2)}, "
        f"{round(result['mpi_y'] + layout.cfg.OFFSET_Y, 2)}) mm"
    )
    
    # Deviation
    c.drawString(layout.left_margin + 60 * mm, y_pos, f"Mean Deviation = {result['deviation']} mm")
    
    # Pass/Fail status based on both accuracy and muzzle velocity
    status_x = layout.left_margin + 115 * mm
    status_color = colors.green if result["pass"] else colors.red
    c.setFillColor(status_color)
    status_text = "PASS" if result["pass"] else "FAIL"
    c.drawString(status_x, y_pos, status_text)
    
    # Max mean deviation (right side of pass/fail)
    c.setFillColor(colors.black)
    max_dev_x = status_x + 25 * mm
    c.drawString(max_dev_x, y_pos, f"(Max: {max_mean_deviation_mm} mm)")

    layout.move_down(5) 
    y_pos = layout.get_y()
    
    c.drawString(
        layout.left_margin, 
        y_pos, 
        f"Max H. Spread = {result.get('max_h', 0)} mm"
    )
    
    c.drawString(
        layout.left_margin + 60 * mm, 
        y_pos, 
        f"Max V. Spread = {result.get('max_v', 0)} mm"
    )
    
    # Add muzzle velocity information
    layout.move_down(5)
    y_pos = layout.get_y()
    
    if result.get('avg_muzzle_velocity') is not None:
        c.drawString(
            layout.left_margin,
            y_pos,
            f"Avg Muzzle Velocity = {result['avg_muzzle_velocity']} m/s"
        )

        if avg_muzzle_velocity_threshold is not None:
            c.drawString(
                layout.left_margin + 60 * mm,
                y_pos,
                f"(Required: >= {avg_muzzle_velocity_threshold} m/s)"
            )

    else:
        c.drawString(
            layout.left_margin,
            y_pos,
            "Avg Muzzle Velocity = Not provided"
        )
    
    layout.move_down(8)


def draw_results_table(c, layout, rounds):
    """Draw results table with dynamic height, splitting across pages if needed"""
    # Table configuration
    row_height = 6 * mm
    col_widths = [35 * mm, 65 * mm, 55 * mm]
    header_row = ["Round No.", "Distance from MPI (mm)", "Muzzle Velocity (m/s)"]
    
    # Prepare all data rows
    data_rows = []
    for r in rounds:
        data_rows.append([str(r["no"]), str(r["distance"]), str(r["velocity"])])
    
    # Handle empty rounds
    if len(data_rows) == 0:
        data_rows.append(["-", "-", "-"])
    
    def get_table_style(is_header_included=True):
        """Get table style, adjusting for header presence"""
        style = [
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        if is_header_included:
            style.extend([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ])
        return TableStyle(style)
    
    # Calculate how many rows fit on current page
    available_height = layout.get_y() - 25 * mm  # Leave margin at bottom
    rows_that_fit = int(available_height / row_height) - 1  # -1 for header
    
    if rows_that_fit >= len(data_rows):
        # All rows fit on current page
        table_data = [header_row] + data_rows
        table = Table(table_data, colWidths=col_widths, rowHeights=row_height)
        table.setStyle(get_table_style(is_header_included=True))
        
        table_width, actual_table_height = table.wrap(PAGE_WIDTH, PAGE_HEIGHT)
        table.drawOn(c, layout.left_margin, layout.get_y() - actual_table_height)
        layout.set_y(layout.get_y() - actual_table_height - 8 * mm)
    else:
        # Need to split table across pages
        current_row_idx = 0
        is_first_page = True
        
        while current_row_idx < len(data_rows):
            if is_first_page:
                # First page: use remaining space
                rows_for_page = max(1, rows_that_fit)
                is_first_page = False
            else:
                # New page: calculate fresh
                c.showPage()
                layout.set_y(PAGE_HEIGHT - 15 * mm)
                available_height = layout.get_y() - 25 * mm
                rows_for_page = int(available_height / row_height) - 1  # -1 for header
            
            # Get rows for this page
            end_row_idx = min(current_row_idx + rows_for_page, len(data_rows))
            page_rows = data_rows[current_row_idx:end_row_idx]
            
            # Build table with header
            table_data = [header_row] + page_rows
            table = Table(table_data, colWidths=col_widths, rowHeights=row_height)
            table.setStyle(get_table_style(is_header_included=True))
            
            table_width, actual_table_height = table.wrap(PAGE_WIDTH, PAGE_HEIGHT)
            table.drawOn(c, layout.left_margin, layout.get_y() - actual_table_height)
            layout.set_y(layout.get_y() - actual_table_height - 8 * mm)
            
            current_row_idx = end_row_idx


def draw_approval_signature(c, layout):
    """Draw Approved By signature line at right bottom corner"""
    # Ensure minimum space at bottom
    min_y = 15 * mm
    if layout.get_y() < min_y + 10 * mm:
        layout.set_y(min_y + 10 * mm)
    
    x_pos = layout.right_margin - 30 * mm
    y_pos = min_y
    
    # Draw label
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(x_pos - 5 * mm, y_pos, "Approved By")
    
    # Draw signature line
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    line_y = y_pos + 12 * mm
    c.line(x_pos - 20 * mm, line_y, x_pos + 30 * mm, line_y)


def generate_report(output_path_or_buffer, form_data, image_path, results, shots_data=None, max_mean_deviation_mm=None, avg_muzzle_velocity_threshold=None, sheet_size_mm=None):
    """
    Generate PDF report with dynamic layout.
    
    Args:
        output_path_or_buffer: Path for output PDF or a BytesIO buffer
        form_data: Dictionary with metadata
        image_path: Path to annotated image
        results: Dictionary with summary and rounds data
        shots_data: List of shot dictionaries with x_mm, y_mm for bullseye plotting
        max_mean_deviation_mm: Maximum mean deviation threshold
        avg_muzzle_velocity_threshold: Minimum required average muzzle velocity
        sheet_size_mm: Tuple of (width, height) of the target sheet in mm
    """
    c = canvas.Canvas(output_path_or_buffer, pagesize=A4)
    layout = DynamicPDFLayout()

    # Draw header
    draw_header(c, layout)
    
    # Draw metadata table
    draw_metadata_table(c, layout, form_data)
    
    # Draw target image and bullseye
    if shots_data is None:
        shots_data = []
    
    mpi_x = results["summary"]["mpi_x"]
    mpi_y = results["summary"]["mpi_y"]
    
    draw_target_and_bullseye(c, layout, image_path, shots_data, 
                              mpi_x, mpi_y, sheet_size_mm)
    
    # Draw result summary
    draw_result_summary(c, layout, results["summary"], max_mean_deviation_mm, avg_muzzle_velocity_threshold)
    
    # Draw results table
    draw_results_table(c, layout, results["rounds"])
    
    # Draw approval signature
    draw_approval_signature(c, layout)

    c.showPage()
    c.save()


def generate_session_report(session_manager, return_bytes=False):
    """
    Wrapper to generate report directly from a SessionManager instance.
    Calculates derived metrics (distance from MPI) and formats data.
    """
    # 1. Save Session Images & Get Path
    session_dir_path = session_manager.save_img_to_db()
    session_dir = Path(str(session_dir_path))  # Ensure it's a Path object
    
    image_path = str(session_dir / "annotated_shot.jpg")

    output_dir = Path(session_manager.cfg.PDF_OUTPUT_FOLDER)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"report_{session_manager.session_id}.pdf")
    
    # 2. Extract Data
    stats = session_manager.latest_stats
    shots = session_manager.get_shot_list()
    
    # Get form data from session manager (set from main page)
    stored_form_data = getattr(session_manager, 'form_data', {}) or {}
    
    form_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amk": stored_form_data.get("amk_no", "N/A") or "N/A",
        "name": stored_form_data.get("name", "Session Analysis") or "Session Analysis",
        "lot": stored_form_data.get("lot_no", "N/A") or "N/A",
        "weapon": stored_form_data.get("weapon_used", "N/A") or "N/A",
        "sample": stored_form_data.get("sample_size", str(len(shots))) or str(len(shots)),
        "temp": stored_form_data.get("temperature", "N/A") or "N/A",
    }
    
    # 3. Get max mean deviation and sheet size from config
    max_mean_deviation_mm = session_manager.cfg.MAX_MEAN_DEVIATION_MM
    avg_muzzle_velocity_threshold = session_manager.cfg.AVG_MUZZLE_VELOCITY
    sheet_size_mm = session_manager.cfg.SHEET_SIZE_MM
    
    # 4. Prepare Results Data
    summary = {
        "mpi_x": 0.0,
        "mpi_y": 0.0,
        "deviation": 0.0,
        "max_h": 0.0,
        "max_v": 0.0,
        "pass": False,
        "avg_muzzle_velocity": None,
        "muzzle_velocity_pass": True
    }
    
    rounds = []
    shots_data = []  # For bullseye plotting
    
    if stats:
        # Get average muzzle velocity
        avg_muzzle_velocity = session_manager.get_avg_muzzle_velocity()
        if avg_muzzle_velocity is None:
            muzzle_velocity_pass = True
        else:
            muzzle_velocity_pass = avg_muzzle_velocity >= avg_muzzle_velocity_threshold
        
        summary = {
            "mpi_x": round(stats.mean_point_of_impact_mm[0], 2),
            "mpi_y": round(stats.mean_point_of_impact_mm[1], 2),
            "deviation": round(stats.mean_radius_deviation_mm, 2),
            "max_h": round(stats.max_horizontal_spread_mm, 2),
            "max_v": round(stats.max_vertical_spread_mm, 2),
            "pass": stats.passed and muzzle_velocity_pass,
            "avg_muzzle_velocity": round(avg_muzzle_velocity, 2) if avg_muzzle_velocity else None,
            "muzzle_velocity_pass": muzzle_velocity_pass
        }
        
        mpi = np.array(stats.mean_point_of_impact_mm)
        
        # Get individual muzzle velocities
        muzzle_velocities = session_manager.muzzle_velocities
        
        for i, s in enumerate(shots):
            # Calculate distance from MPI
            p = np.array([s['x_mm'], s['y_mm']])
            dist = np.linalg.norm(p - mpi)
            
            # Get velocity for this shot
            velocity = muzzle_velocities[i] if i < len(muzzle_velocities) else "N/A"
            
            rounds.append({
                "no": i + 1,
                "distance": round(dist, 2),
                "velocity": velocity
            })
            
            # Store shot data for bullseye
            shots_data.append({
                'x_mm': s['x_mm'],
                'y_mm': s['y_mm']
            })
            
    results = {
        "summary": summary,
        "rounds": rounds
    }

    if return_bytes:
        # memory buffer
        buffer = io.BytesIO()
        generate_report(buffer, form_data, image_path, results, 
                       shots_data=shots_data, max_mean_deviation_mm=max_mean_deviation_mm,
                       avg_muzzle_velocity_threshold=avg_muzzle_velocity_threshold,
                       sheet_size_mm=sheet_size_mm)
        buffer.seek(0) # Rewind to the beginning
        return buffer.read() # Return raw PDF bytes
    else:
        # Save to disk
        output_dir = Path(session_manager.cfg.PDF_OUTPUT_FOLDER)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"report_{session_manager.session_id}.pdf")
        
        generate_report(output_path, form_data, image_path, results, 
                       shots_data=shots_data, max_mean_deviation_mm=max_mean_deviation_mm,
                       avg_muzzle_velocity_threshold=avg_muzzle_velocity_threshold,
                       sheet_size_mm=sheet_size_mm)
        return output_path

def draw_target_and_bullseye(c, layout, image_path, shots, mpi_x_mm, mpi_y_mm, sheet_size_mm):
    """
    Draw annotated image on left and Digital Twin sheet on right.
    """
    section_height = 75 * mm
    start_y = layout.get_y()
    
    # 1. Left: Annotated Image
    image_width = 80 * mm
    image_height = 75 * mm
    
    if os.path.exists(image_path):
        try:
            c.drawImage(image_path, layout.left_margin, start_y - image_height,
                        width=image_width, height=image_height, preserveAspectRatio=True, mask="auto")
        except Exception:
            c.setStrokeColor(colors.gray)
            c.rect(layout.left_margin, start_y - image_height, image_width, image_height)
            c.drawString(layout.left_margin + 10, start_y - image_height/2, "Image Error")
    
    # 2. Right: Digital Twin Sheet
    # Define the box area for the sheet on the right
    box_size = 70 * mm
    center_x = layout.left_margin + image_width + 15 * mm + (box_size / 2)
    center_y = start_y - (section_height / 2)
    
    sheet_w, sheet_h = sheet_size_mm
    
    # Draw Sheet & Get Mapping Params
    scale, origin_x, origin_y = draw_bullseye_target(
        c, center_x, center_y, box_size, sheet_w, sheet_h
    )
    
    # Plot Shots (Absolute Coords + Offset)
    for i, shot in enumerate(shots):
        abs_x = shot['x_mm'] + layout.cfg.OFFSET_X
        abs_y = shot['y_mm'] + layout.cfg.OFFSET_Y
        draw_shot_on_bullseye(c, scale, origin_x, origin_y, abs_x, abs_y, i + 1)
        
    # Plot MPI
    mpi_abs_x = mpi_x_mm + layout.cfg.OFFSET_X
    mpi_abs_y = mpi_y_mm + layout.cfg.OFFSET_Y
    draw_mpi_marker(c, scale, origin_x, origin_y, mpi_abs_x, mpi_abs_y)
    
    # Scale Label
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    c.drawCentredString(center_x, start_y - section_height - 1 * mm, 
                        f"Scale: {sheet_w}x{sheet_h} mm")
    
    layout.set_y(start_y - section_height - 10 * mm)