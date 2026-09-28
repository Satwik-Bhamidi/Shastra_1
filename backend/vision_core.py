import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any
from .config import SystemConfig

@dataclass
class AnalysisResult:
    """Structured return object for statistical analysis."""
    shot_count: int
    mean_point_of_impact_mm: Tuple[float, float]
    mean_radius_deviation_mm: float
    max_horizontal_spread_mm: float
    max_vertical_spread_mm: float
    mad_per_shot_mm: List[float]
    passed: bool

class VisionCore:
    def __init__(self, config: SystemConfig):
        self.cfg = config
        
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        
        # Tuned detection parameters
        self.aruco_params.adaptiveThreshWinSizeMin = 3
        self.aruco_params.adaptiveThreshWinSizeMax = 23
        self.aruco_params.adaptiveThreshWinSizeStep = 10
        self.aruco_params.minMarkerPerimeterRate = 0.02  # Lower to detect smaller markers
        self.aruco_params.minCornerDistanceRate = 0.05
        self.aruco_params.polygonalApproxAccuracyRate = 0.03
        self.aruco_params.errorCorrectionRate = 0.6
        
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

    def align_images(self, img_ref: np.ndarray, img_shot: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        ref_warp = self._align_single_image(img_ref)
        shot_warp = self._align_single_image(img_shot)
        return ref_warp, shot_warp

    def detect_candidates(self, ref_warp: np.ndarray, shot_warp: np.ndarray) -> Tuple[List[Dict[str, Any]]]:

        # A. Differencing (Calculates mask size dynamically)
        diff_img = self._compute_difference(ref_warp, shot_warp)

        # B. Filtering
        clean_img = self._filter_noise(diff_img)

        # C. Watershed (Separation)
        clean_img = self._separate_touching_blobs(clean_img, shot_warp)

        # D. Contour Extraction (Candidate Generation)
        candidates = self._extract_contours(clean_img)
        
        return candidates

    def calculate_stats(self, active_coords_mm: List[Tuple[float, float]]) -> AnalysisResult:
        """Step 3: Pure Math. Calculates statistics for the 'Active' shots."""
        count = len(active_coords_mm)
        
        if count == 0:
            return AnalysisResult(0, (0.0, 0.0), 0.0, 0.0, 0.0, [], False)

        coords_np = np.array(active_coords_mm)
        
        # 1. Mean Point of Impact (MPI)
        mean_x = np.mean(coords_np[:, 0])
        mean_y = np.mean(coords_np[:, 1])
        
        # 2. Mean Radius Deviation (MRD) and MAD per shot
        distances = np.sqrt((coords_np[:, 0] - mean_x)**2 + (coords_np[:, 1] - mean_y)**2)
        mean_radius = np.mean(distances)
        mad_per_shot = distances.tolist()
        
        # 3. Max Horizontal and Vertical Spread
        max_horizontal_spread = np.max(coords_np[:, 0]) - np.min(coords_np[:, 0])
        max_vertical_spread = np.max(coords_np[:, 1]) - np.min(coords_np[:, 1])
        
        # 4. Pass/Fail Check
        passed = round(mean_radius, 2) <= self.cfg.MAX_MEAN_DEVIATION_MM #banker's rounding used

        return AnalysisResult(
            shot_count=count,
            mean_point_of_impact_mm=(mean_x, mean_y),
            mean_radius_deviation_mm=float(mean_radius),
            max_horizontal_spread_mm=float(max_horizontal_spread),
            max_vertical_spread_mm=float(max_vertical_spread),
            mad_per_shot_mm=mad_per_shot,
            passed=bool(passed)
        )

    def _align_single_image(self, img: np.ndarray) -> Optional[np.ndarray]:
        if img is None:
            return None

        scales = [1.0, 0.75, 0.5]
        
        for scale in scales:
            if scale != 1.0:
                scaled_img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
            else:
                scaled_img = img.copy()
            
            # CLAHE for contrast enhancement
            gray = cv2.cvtColor(scaled_img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Slight blur to reduce noise but preserve edges
            enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            corners, ids, _ = self.detector.detectMarkers(enhanced)
            
            if ids is not None and len(ids) >= 4:
                ids = ids.flatten()
                centers = {}
                
                for i, id_val in enumerate(ids):
                    marker_center = np.mean(corners[i][0], axis=0)
                    if scale != 1.0:
                        marker_center = marker_center / scale
                    centers[id_val] = marker_center
                
                out_w, out_h = self.cfg.OUTPUT_PX
                dst_pts = [
                    (0, 0),         # TL
                    (out_w, 0),     # TR
                    (0, out_h),     # BL
                    (out_w, out_h)  # BR
                ]
                
                src_pts = []
                current_ids = {'TL': 0, 'TR': 1, 'BL': 2, 'BR': 3}
                ordered_ids = [current_ids[k] for k in ['TL', 'TR', 'BL', 'BR']]
                
                for target_id in ordered_ids:
                    if target_id in centers:
                        src_pts.append(centers[target_id])
                    else:
                        break
                
                if len(src_pts) == 4:
                    H, _ = cv2.findHomography(np.array(src_pts), np.array(dst_pts))
                    return cv2.warpPerspective(img, H, (out_w, out_h))
        
        return None

    def _compute_difference(self, img1, img2):
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(g1, g2)
        
        grid_w, grid_h = self.cfg.MARKER_GRID_SIZE_MM
        out_w, out_h = self.cfg.OUTPUT_PX
        
        px_per_mm_x = out_w / grid_w
        px_per_mm_y = out_h / grid_h
        avg_px_per_mm = (px_per_mm_x + px_per_mm_y) / 2
        
        marker_px = self.cfg.ARUCO_SIZE_MM * avg_px_per_mm
        mask_corner_size = int(marker_px * 1.2)
        
        h, w = diff.shape
        s = mask_corner_size
        
        cv2.rectangle(diff, (0,0), (s, s), 0, -1)         # TL
        cv2.rectangle(diff, (w-s, 0), (w, s), 0, -1)      # TR
        cv2.rectangle(diff, (0, h-s), (s, h), 0, -1)      # BL
        cv2.rectangle(diff, (w-s, h-s), (w, h), 0, -1)    # BR
        
        return diff

    def _filter_noise(self, diff_img):
        blurred = cv2.medianBlur(diff_img, self.cfg.MEDIAN_BLUR_KERNEL)
        _, thresh = cv2.threshold(blurred, self.cfg.DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, self.cfg.MORPH_KERNEL_SIZE)
        clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        clean = cv2.dilate(clean, kernel, iterations=self.cfg.DILATE_ITERATIONS)
        return clean
    
    def _separate_touching_blobs(self, binary_img, color_img):
        dist_transform = cv2.distanceTransform(binary_img, cv2.DIST_L2, 0)
        ret, sure_fg = cv2.threshold(dist_transform, self.cfg.DIST_TRANSFORM_THRESHOLD * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        sure_bg = cv2.dilate(binary_img, None, iterations=3)
        unknown = cv2.subtract(sure_bg, sure_fg)

        ret, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        cv2.watershed(color_img, markers)

        boundary_mask = np.zeros_like(binary_img, dtype=np.uint8)
        boundary_mask[markers == -1] = 255
        boundary_mask = cv2.dilate(boundary_mask, None, iterations=2)

        binary_img[boundary_mask == 255] = 0

        return binary_img

    def _extract_contours(self, binary_img) -> List[Dict[str, Any]]:
        contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        mm_per_px_x, mm_per_px_y = self.cfg.mm_per_px
        candidate_id = 0

        min_area = self.cfg.MIN_HOLE_AREA_PX
        max_area = self.cfg.MAX_HOLE_AREA_PX

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                M = cv2.moments(cnt)
                if M['m00'] == 0: continue
                
                cx = M['m10'] / M['m00']
                cy = M['m01'] / M['m00']
                
                candidates.append({
                    'id': candidate_id,
                    'x_px': cx,
                    'y_px': cy,
                    'x_mm': cx * mm_per_px_x,
                    'y_mm': cy * mm_per_px_y,
                    'area': area
                })
                candidate_id += 1
                
        return candidates