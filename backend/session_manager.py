import cv2
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

from .config import SystemConfig
from .vision_core import VisionCore, AnalysisResult

class SessionManager:
    """
    Controller class for MVC architecture.
    Manages session state, handles file I/O directly, and interacts with VisionCore.
    """

    def __init__(self, config: SystemConfig, vision_core: VisionCore):
        self.cfg = config
        self.core = vision_core

        self.session_id = self._generate_session_id()

        self.ref_path: Optional[str] = None
        self.shot_path: Optional[str] = None
        
        self.ref_warp: Optional[np.ndarray] = None
        self.shot_warp: Optional[np.ndarray] = None
        
        self.shots: List[Dict[str, Any]] = []
        self.next_shot_id: int = 0
        self.latest_stats: Optional[AnalysisResult] = None
        self.form_data: Dict[str, Any] = {}
        self.muzzle_velocities: List[float] = []

    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on current timestamp."""
        return f"session_{datetime.now().strftime('%Y_%m_%d_%HH%MM%SS_%f')}" #%f is microseconds, just in case of any extreme edge cases

    def set_form_data(self, form_data: Dict[str, Any]):
        """Store form data for report generation."""
        self.form_data = form_data

    def clear_session(self):
        """Clear all session data to start fresh."""
        self.ref_path = None
        self.shot_path = None
        self.ref_warp = None
        self.shot_warp = None
        self.shots = []
        self.next_shot_id = 0
        self.latest_stats = None
        self.form_data = {}
        self.muzzle_velocities = []
        self.session_id = self._generate_session_id()

    def start_session(self, ref_path: str, shot_path: str):
        self.ref_path = ref_path
        self.shot_path = shot_path
        self.shots = []
        self.next_shot_id = 0

        img_ref = self._load_image_file(ref_path)
        img_shot = self._load_image_file(shot_path)

        self.ref_warp, self.shot_warp = self.core.align_images(img_ref, img_shot)
        
        if self.ref_warp is None or self.shot_warp is None:
            raise ValueError("Alignment Failed: ArUco markers not found in one or both images.")

        candidates = self.core.detect_candidates(self.ref_warp, self.shot_warp)

        for c in candidates:
            self._register_shot(c['x_px'], c['y_px'], c['area'], manual=False)

        self.recalculate()

    def add_manual_shot(self, x_px: float, y_px: float):
        if self.shot_warp is None: return
        self._register_shot(x_px, y_px, area=-1.0, manual=True)
        self.recalculate()

    def delete_shot(self, shot_id: int):
        initial_len = len(self.shots)
        self.shots = [s for s in self.shots if s['id'] != shot_id]
        
        if len(self.shots) < initial_len:
            self.recalculate()

    def set_muzzle_velocities(self, velocities: List[float]):
        """Set muzzle velocities for all shots."""
        self.muzzle_velocities = velocities

    def get_avg_muzzle_velocity(self) -> Optional[float]:
        """Calculate average muzzle velocity from the list."""
        if not self.muzzle_velocities:
            return None
        return sum(self.muzzle_velocities) / len(self.muzzle_velocities)

    def recalculate(self):
        coords_mm = [(s['x_mm'], s['y_mm']) for s in self.shots]
        self.latest_stats = self.core.calculate_stats(coords_mm)

    def _load_image_file(self, filepath: str) -> np.ndarray:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"Could not decode image: {path}")
        return img

    def save_img_to_db(self) -> str:
        if self.shot_warp is None or self.latest_stats is None:
            raise ValueError("No analysis data available to save.")

        results_root = Path(self.cfg.IMG_DB_FOLDER)  # Ensure it's a Path object
        session_dir = results_root / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # 2. Generate and Save Images
        raw_path = session_dir / "raw_shot.jpg"
        cv2.imwrite(str(raw_path), self.shot_warp)

        annotated_img = self.get_display_image_annotated()
        anno_path = session_dir / "annotated_shot.jpg"
        cv2.imwrite(str(anno_path), annotated_img)

        return str(session_dir)

    def get_display_image(self) -> Optional[np.ndarray]:
        return self.shot_warp

    def get_display_image_annotated(self) -> np.ndarray:
        if self.shot_warp is None: return np.zeros((100,100,3), dtype=np.uint8)
        
        vis = self.shot_warp.copy()
        i = 1
        for s in self.shots:
            cx, cy = int(s['x_px']), int(s['y_px'])
            color = (255, 0, 0)
            
            cv2.circle(vis, (cx, cy), 8, color, 4)
            cv2.putText(vis, str(i), (cx+10, cy), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2)
            i += 1
        return vis

    def get_shot_list(self) -> List[Dict[str, Any]]:
        return self.shots

    def _register_shot(self, x_px: float, y_px: float, area: float, manual: bool):
        mm_per_px_x, mm_per_px_y = self.cfg.mm_per_px
        shot_record = {
            'id': self.next_shot_id,
            'x_px': x_px,
            'y_px': y_px,
            'x_mm': x_px * mm_per_px_x,
            'y_mm': y_px * mm_per_px_y,
            'area': area,
            'manual': manual
        }
        self.shots.append(shot_record)
        self.next_shot_id += 1