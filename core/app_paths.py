"""
SHASTRA Application Paths Module

Cross-platform path management for application data storage.
Handles database and configuration file locations across Windows, Linux, and macOS.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Application constants
APP_NAME = "Shastra"
DB_FILENAME = "shastra.db"


def get_app_data_dir() -> Path:
    """
    Get the platform-specific application data directory.
    
    Returns:
        Path: Application data directory path
        
    Platform paths:
        Windows: %APPDATA%/Shastra/
        Linux:   ~/.local/share/shastra/
        macOS:   ~/Library/Application Support/Shastra/
    """
    if sys.platform == "win32":
        # Windows: Use APPDATA environment variable
        base = os.environ.get("APPDATA")
        if not base:
            base = os.path.expanduser("~")
        app_dir = Path(base) / APP_NAME
    elif sys.platform == "darwin":
        # macOS: Use Application Support directory
        app_dir = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        # Linux and others: Use XDG_DATA_HOME or default
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            app_dir = Path(xdg_data) / APP_NAME.lower()
        else:
            app_dir = Path.home() / ".local" / "share" / APP_NAME.lower()
    
    return app_dir


def get_database_path() -> Path:
    """
    Get the full path to the SQLite database file.
    
    Returns:
        Path: Full path to shastra.db
    """
    return get_app_data_dir() / DB_FILENAME


def ensure_app_directories() -> Path:
    """
    Ensure application data directories exist.
    Creates all necessary directories if they don't exist.
    
    Returns:
        Path: Application data directory path
    """
    app_dir = get_app_data_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_log_dir() -> Path:
    """
    Get the directory for application logs.
    
    Returns:
        Path: Log directory path
    """
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def is_first_run() -> bool:
    """
    Check if this is the first run of the application.
    
    Returns:
        bool: True if database doesn't exist (first run)
    """
    return not get_database_path().exists()
