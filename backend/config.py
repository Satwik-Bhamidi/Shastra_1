import json
from typing import Tuple, Dict, Any
from PyQt5.QtCore import QSettings
import sys
from pathlib import Path
import os

class SystemConfig:

    def __init__(self):
        # Windows: HKEY_CURRENT_USER\Software\ShastraAI\ProofYard
        # Linux: ~/.config/ShastraAI/ProofYard.conf
        self.settings = QSettings("Shastra_Proof_Yard", "config_settings")

        if getattr(sys, 'frozen', False):
            self.base_dir = Path(os.path.dirname(sys.executable))
        else:
            self.base_dir = Path(__file__).resolve().parents[2]

    # System configuration
    @property
    def MARKER_GRID_SIZE_MM(self) -> Tuple[float, float]:
        val = self.settings.value("physical/marker_grid_size_mm", [1066.8, 1066.8])
        return tuple(map(float, val))

    @MARKER_GRID_SIZE_MM.setter
    def MARKER_GRID_SIZE_MM(self, value: Tuple[float, float]):
        self.settings.setValue("physical/marker_grid_size_mm", [float(v) for v in value])

    @property
    def ARUCO_SIZE_MM(self) -> float:
        return float(self.settings.value("physical/aruco_size_mm", 100.0))

    @ARUCO_SIZE_MM.setter
    def ARUCO_SIZE_MM(self, value: float):
        self.settings.setValue("physical/aruco_size_mm", float(value))

    @property
    def SHEET_SIZE_MM(self) -> Tuple[float, float]:
        val = self.settings.value("physical/sheet_size_mm", [1219.2, 1219.2])
        return tuple(map(float, val))

    @SHEET_SIZE_MM.setter
    def SHEET_SIZE_MM(self, value: Tuple[float, float]):
        self.settings.setValue("physical/sheet_size_mm", [float(v) for v in value])

    # vision core settings

    @property
    def OUTPUT_PX(self) -> Tuple[int, int]:
        val = self.settings.value("vision/output_px", [1000, 1000])
        return tuple(map(int, val))

    @OUTPUT_PX.setter
    def OUTPUT_PX(self, value: Tuple[int, int]):
        self.settings.setValue("vision/output_px", [int(v) for v in value])

    # --- Tuning Parameters ---

    @property
    def DIFF_THRESHOLD(self) -> int:
        return int(self.settings.value("vision/diff_threshold", 40))

    @DIFF_THRESHOLD.setter
    def DIFF_THRESHOLD(self, value: int):
        self.settings.setValue("vision/diff_threshold", int(value))

    @property
    def MEDIAN_BLUR_KERNEL(self) -> int:
        return int(self.settings.value("vision/median_blur_kernel", 1))

    @MEDIAN_BLUR_KERNEL.setter
    def MEDIAN_BLUR_KERNEL(self, value: int):
        self.settings.setValue("vision/median_blur_kernel", int(value))

    @property
    def MORPH_KERNEL_SIZE(self) -> Tuple[int, int]:
        val = self.settings.value("vision/morph_kernel_size", [1, 1])
        return tuple(map(int, val))

    @MORPH_KERNEL_SIZE.setter
    def MORPH_KERNEL_SIZE(self, value: Tuple[int, int]):
        self.settings.setValue("vision/morph_kernel_size", [int(v) for v in value])

    @property
    def DILATE_ITERATIONS(self) -> int:
        return int(self.settings.value("vision/dilate_iterations", 1))

    @DILATE_ITERATIONS.setter
    def DILATE_ITERATIONS(self, value: int):
        self.settings.setValue("vision/dilate_iterations", int(value))

    @property
    def MIN_HOLE_AREA_PX(self) -> int:
        return int(self.settings.value("vision/min_hole_area_px", 10))

    @MIN_HOLE_AREA_PX.setter
    def MIN_HOLE_AREA_PX(self, value: int):
        self.settings.setValue("vision/min_hole_area_px", int(value))

    @property
    def MAX_HOLE_AREA_PX(self) -> int:
        return int(self.settings.value("vision/max_hole_area_px", 100))

    @MAX_HOLE_AREA_PX.setter
    def MAX_HOLE_AREA_PX(self, value: int):
        self.settings.setValue("vision/max_hole_area_px", int(value))

    @property
    def DIST_TRANSFORM_THRESHOLD(self) -> float:
        return float(self.settings.value("vision/dist_transform_threshold", 0.5))

    @DIST_TRANSFORM_THRESHOLD.setter
    def DIST_TRANSFORM_THRESHOLD(self, value: float):
        self.settings.setValue("vision/dist_transform_threshold", float(value))

    @property
    def MAX_MEAN_DEVIATION_MM(self) -> float:
        return float(self.settings.value("vision/max_mean_deviation_mm", 14.0))

    @MAX_MEAN_DEVIATION_MM.setter
    def MAX_MEAN_DEVIATION_MM(self, value: float):
        self.settings.setValue("vision/max_mean_deviation_mm", float(value))

    @property
    def AVG_MUZZLE_VELOCITY(self) -> float:
        return float(self.settings.value("vision/avg_muzzle_velocity", 800.0))

    @AVG_MUZZLE_VELOCITY.setter
    def AVG_MUZZLE_VELOCITY(self, value: float):
        self.settings.setValue("vision/avg_muzzle_velocity", float(value))

    # File paths and formats
    @property
    def PDF_OUTPUT_FOLDER(self) -> str:
        return str(self.settings.value("app/pdf_output_folder", self.base_dir / "test_reports"))

    @PDF_OUTPUT_FOLDER.setter
    def PDF_OUTPUT_FOLDER(self, value: str):
        self.settings.setValue("app/pdf_output_folder",
                               str(Path(value) if Path(value).name == "test_reports" else Path(value) / "test_reports")
        )

    @property
    def INPUT_IMG_FOLDER(self) -> str:
        return str(self.settings.value("app/input_img_folder", self.base_dir))
    
    @INPUT_IMG_FOLDER.setter
    def INPUT_IMG_FOLDER(self, value: str):
        self.settings.setValue("app/input_img_folder", str(value))

    @property
    def IMG_DB_FOLDER(self) -> str:
        return str(self.settings.value("app/img_db_folder", self.base_dir / "img_database"))
    
    @IMG_DB_FOLDER.setter
    def IMG_DB_FOLDER(self, value: str):
        self.settings.setValue("app/img_db_folder",
                               str(Path(value) if Path(value).name == "img_database" else Path(value) / "img_database")
        )
        
    @property
    def GENERATED_MARKERS_FOLDER(self) -> str:
        return str(self.settings.value("app/generated_markers_folder", self.base_dir / "aruco_markers"))
    
    @GENERATED_MARKERS_FOLDER.setter
    def GENERATED_MARKERS_FOLDER(self, value: str):
        self.settings.setValue("app/generated_markers_folder",
                               str(Path(value) if Path(value).name == "aruco_markers" else Path(value) / "aruco_markers")
        )

    #offsets used in pdf generation

    @property
    def OFFSET_X(self) -> float:
        sheet_w = float(self.SHEET_SIZE_MM[0])
        grid_w = float(self.MARKER_GRID_SIZE_MM[0])
        return (sheet_w - grid_w) / 2.0

    @property
    def OFFSET_Y(self) -> float:
        sheet_h = float(self.SHEET_SIZE_MM[1])
        grid_h = float(self.MARKER_GRID_SIZE_MM[1])
        return (sheet_h - grid_h) / 2.0


    @property
    def mm_per_px(self) -> Tuple[float, float]:
        grid = self.MARKER_GRID_SIZE_MM
        out = self.OUTPUT_PX
        x_scale = grid[0] / out[0]
        y_scale = grid[1] / out[1]
        return (x_scale, y_scale)

    def save(self):
        """Force synchronization of settings to disk/registry."""
        self.settings.sync()
        print("[Config] Settings synchronized.")

    @classmethod
    def load(cls) -> 'SystemConfig':
        """Factory method to maintain compatibility with existing codebase."""
        return cls()