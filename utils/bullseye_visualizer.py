from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Polygon

BULLSEYE_RINGS = [
    (10, 0.10),
    (9, 0.20),
    (7, 0.40),
    (5, 0.60),
    (3, 0.80),
    (1, 1.0),
]

def draw_bullseye_target(c, center_x, center_y, box_size_pt, sheet_width_mm, sheet_height_mm):
    """
    Draws a scaled representation of the physical sheet (Digital Twin).
    Returns the scaling factor (points per mm) and top-left origin for plotting.
    """
    # 1. Calculate Scale to fit sheet in the box
    scale_x = box_size_pt / sheet_width_mm
    scale_y = box_size_pt / sheet_height_mm
    scale = min(scale_x, scale_y)
    
    # 2. Calculate Sheet Dimensions in PDF Points
    draw_width = sheet_width_mm * scale
    draw_height = sheet_height_mm * scale
    
    # 3. Calculate Sheet Origin (Top-Left relative to PDF bottom-left system)
    # We center the sheet at (center_x, center_y)
    sheet_left_x = center_x - (draw_width / 2)
    sheet_bottom_y = center_y - (draw_height / 2)
    sheet_top_y = sheet_bottom_y + draw_height
    
    # 4. Draw Sheet Boundary
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.setFillColor(colors.white)
    c.rect(sheet_left_x, sheet_bottom_y, draw_width, draw_height, fill=1, stroke=1)
    
    # 5. Draw Rings (Centered on Sheet)
    # Assume outermost ring (score 1) touches the nearest edge (min dimension)
    max_ring_radius_mm = min(sheet_width_mm, sheet_height_mm) / 2
    
    ring_center_x = center_x
    ring_center_y = center_y
    
    for i, (score, ratio) in enumerate(reversed(BULLSEYE_RINGS)):
        radius_mm = max_ring_radius_mm * ratio
        radius_pt = radius_mm * scale
        
        # Color Logic
        if score == 7: fill_color = colors.lightgrey
        elif score == 9: fill_color = colors.grey
        else: fill_color = colors.white
        
        c.setFillColor(fill_color)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.circle(ring_center_x, ring_center_y, radius_pt, fill=1, stroke=1)
        
        # Add Ring Number
        c.setFillColor(colors.black)
        if score == 10:
            font_size = 6
        else:
            font_size = 8
        c.setFont("Helvetica-Bold", font_size)
        label_text = str(score)
        text_w = c.stringWidth(label_text, "Helvetica-Bold", font_size)
        label_x = ring_center_x - text_w / 2
        label_y = ring_center_y + radius_pt - 6

        if score == 10:
            c.drawString(label_x + 5, label_y - 3, label_text)
        elif score == 9:
            c.drawString(label_x + 5, label_y - 3, label_text)
        else:
            c.drawString(label_x + 5, label_y - 8, label_text)

    # Crosshairs
    c.setLineWidth(0.3)
    c.line(sheet_left_x, ring_center_y, sheet_left_x + draw_width, ring_center_y)
    c.line(ring_center_x, sheet_bottom_y, ring_center_x, sheet_top_y)
    
    # 6. Draw Coordinate Axes with Arrows
    axis_offset = 5  # Distance from sheet edge
    arrow_size = 6
    
    # X-axis (left to right) on top
    x_axis_y = sheet_top_y + axis_offset
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(sheet_left_x, x_axis_y, sheet_left_x + draw_width, x_axis_y)
    
    # X-axis arrow (pointing right)
    arrow_right_x = sheet_left_x + draw_width
    arrow_right_y = x_axis_y
    p = c.beginPath()
    p.moveTo(arrow_right_x, arrow_right_y)
    p.lineTo(arrow_right_x - arrow_size, arrow_right_y - arrow_size/2)
    p.lineTo(arrow_right_x - arrow_size, arrow_right_y + arrow_size/2)
    p.close()
    c.setFillColor(colors.black)
    c.drawPath(p, fill=1, stroke=0)
    
    # X-axis label
    c.setFont("Helvetica-Bold", 10)
    c.drawString(sheet_left_x + draw_width + 5, x_axis_y - 3, "X")
    
    # Y-axis (top to bottom) on left
    y_axis_x = sheet_left_x - axis_offset
    c.setLineWidth(1)
    c.line(y_axis_x, sheet_top_y, y_axis_x, sheet_bottom_y)
    
    # Y-axis arrow (pointing down)
    arrow_down_x = y_axis_x
    arrow_down_y = sheet_bottom_y
    p = c.beginPath()
    p.moveTo(arrow_down_x, arrow_down_y)
    p.lineTo(arrow_down_x - arrow_size/2, arrow_down_y + arrow_size)
    p.lineTo(arrow_down_x + arrow_size/2, arrow_down_y + arrow_size)
    p.close()
    c.setFillColor(colors.black)
    c.drawPath(p, fill=1, stroke=0)
    
    # Y-axis label
    c.setFont("Helvetica-Bold", 10)
    c.drawString(y_axis_x - 12, sheet_bottom_y - 10, "Y")
    
    return scale, sheet_left_x, sheet_top_y

def draw_shot_on_bullseye(c, scale, sheet_left_x, sheet_top_y, abs_x_mm, abs_y_mm, shot_number):
    """
    Plots a shot using absolute physical coordinates (Top-Left Origin).
    """
    # Map Physical (TL origin) to PDF (BL origin)
    plot_x = sheet_left_x + (abs_x_mm * scale)
    plot_y = sheet_top_y - (abs_y_mm * scale) # Y flips down
    
    # Draw Marker
    c.setFillColor(colors.red)
    c.setStrokeColor(colors.darkred)
    c.setLineWidth(0.5)
    c.circle(plot_x, plot_y, 3, fill=1, stroke=1)
    
    # Label
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 5)
    text_w = c.stringWidth(str(shot_number), "Helvetica-Bold", 5)
    c.drawString(plot_x - text_w/2, plot_y - 1.5, str(shot_number))

def draw_mpi_marker(c, scale, sheet_left_x, sheet_top_y, abs_x_mm, abs_y_mm):
    """
    Plots MPI using absolute physical coordinates.
    """
    plot_x = sheet_left_x + (abs_x_mm * scale)
    plot_y = sheet_top_y - (abs_y_mm * scale)
    
    c.setStrokeColor(colors.blue)
    c.setFillColor(colors.blue)
    c.setLineWidth(1.5)
    c.circle(plot_x, plot_y, 2, fill=1, stroke=0)
    
    d = 6
    c.line(plot_x - d, plot_y, plot_x + d, plot_y)
    c.line(plot_x, plot_y - d, plot_x, plot_y + d)